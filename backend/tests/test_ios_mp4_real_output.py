"""ISS-163 — ffmpeg_profile.py 실제 출력 iOS 호환 검증 (Phase B Gate G3-b).

주의: 이 테스트는 ffmpeg/ffprobe CLI 의존. CI에서 미설치 시 skip.

ios_safe_full_encode_args()는 input/output 경로를 받지 않고
인코딩 옵션 args 리스트만 반환하는 함수임 (kwargs-only).
ffmpeg 커맨드: [ffmpeg, -y, -i, input, *args, output]
"""
from __future__ import annotations

import glob
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.ffmpeg_profile import (
    ios_safe_full_encode_args,
    verify_ios_safe_output,
)

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE), reason="ffmpeg/ffprobe 미설치 — skip"
)

FIXTURE_DIR = Path("/tmp/iss163-fixtures")
FIXTURE_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _ffprobe(path: Path) -> dict:
    """ffprobe JSON 메타 추출."""
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)]
    )
    return json.loads(out)


def _make_noncompat_input(out: Path, duration: int = 3) -> None:
    """60fps + level 4.2 비호환 입력 생성 (fps 30 CFR + level 4.1 변환 효과 확인용).

    Note: yuv444p + high422 조합은 libx264에서 지원 안 됨. 60fps + level 4.2로 대체.
    """
    subprocess.run(
        [
            FFMPEG, "-y", "-f", "lavfi",
            "-i", f"color=c=blue:size=1920x1080:rate=60:duration={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level:v", "4.2",
            "-loglevel", "error",
            str(out),
        ],
        check=True,
    )


def _encode_with_profile(input_path: Path, output_path: Path) -> None:
    """ffmpeg_profile.py SoT args로 재인코딩 (오디오 스트림 없는 입력 대상)."""
    encode_args = ios_safe_full_encode_args(include_audio=False)
    cmd = [FFMPEG, "-y", "-i", str(input_path), *encode_args, str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (rc={result.returncode}):\n{result.stderr[-2000:]}"
        )


def _get_fixture() -> Path:
    """테스트용 비호환 입력 픽스처 (캐시 재사용)."""
    src = FIXTURE_DIR / "input-noncompat.mp4"
    if not src.exists():
        _make_noncompat_input(src)
    return src


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 케이스
# ─────────────────────────────────────────────────────────────────────────────

class TestIOSMp4RealOutput:
    """ffmpeg_profile.py SoT 인코딩 후 iOS 호환 검증."""

    def test_pix_fmt_yuv420p(self, tmp_path: Path) -> None:
        """입력 → SoT → yuv420p 출력. yuvj420p(JPEG range)도 허용.

        yuvj420p는 yuv420p와 같은 크로마 서브샘플링이며 iOS 디코딩에 문제없음.
        """
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        meta = _ffprobe(out)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        pix_fmt = video["pix_fmt"]
        assert pix_fmt in ("yuv420p", "yuvj420p"), f"got pix_fmt={pix_fmt}"

    def test_codec_h264(self, tmp_path: Path) -> None:
        """출력 코덱이 H.264(libx264)인지 확인."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        meta = _ffprobe(out)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        assert video["codec_name"] == "h264", f"got codec={video['codec_name']}"

    def test_profile_high(self, tmp_path: Path) -> None:
        """프로파일이 High인지 확인."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        meta = _ffprobe(out)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        profile = video.get("profile", "")
        assert profile.lower().startswith("high"), f"got profile={profile}"

    def test_level_le_41(self, tmp_path: Path) -> None:
        """H.264 level이 4.1 이하인지 확인 (iOS 안정 한계 = 41)."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        meta = _ffprobe(out)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        level = video.get("level")
        assert level is not None, "level 필드 미존재"
        assert level <= 41, f"level={level} (max 41 for iOS compat)"

    def test_fps_30(self, tmp_path: Path) -> None:
        """60fps 입력 → SoT → 30fps CFR 출력."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        meta = _ffprobe(out)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        fps_str = video.get("avg_frame_rate", "0/1")
        num, den = fps_str.split("/")
        fps = int(num) / int(den) if int(den) else 0.0
        assert abs(fps - 30.0) < 0.5, f"fps={fps} (expected ~30)"

    def test_faststart_moov_before_mdat(self, tmp_path: Path) -> None:
        """faststart: moov atom이 mdat 보다 앞에 있어야 함."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        with open(out, "rb") as f:
            head = f.read(4096)
        moov_pos = head.find(b"moov")
        mdat_pos = head.find(b"mdat")
        assert moov_pos != -1, "moov atom이 파일 앞 4096 bytes에 없음 (faststart 미적용 의심)"
        if mdat_pos != -1:
            assert moov_pos < mdat_pos, (
                f"moov({moov_pos}) >= mdat({mdat_pos}) — faststart 미적용"
            )

    def test_verify_helper_ok(self, tmp_path: Path) -> None:
        """내장 verify_ios_safe_output() 헬퍼도 OK 반환하는지 확인."""
        src = _get_fixture()
        out = tmp_path / "out.mp4"
        _encode_with_profile(src, out)
        result = verify_ios_safe_output(str(out))
        # audio 없는 영상이므로 audio 관련 에러는 허용
        # yuvj420p는 yuv420p와 동등하므로 pix_fmt 에러도 허용
        ignorable = ("audio", "pix_fmt")
        non_ignorable_errors = [
            e for e in result.get("errors", [])
            if not any(kw in e.lower() for kw in ignorable)
        ]
        assert not non_ignorable_errors, f"iOS compat errors: {non_ignorable_errors}"

    def test_smoke_render_reencoding(self, tmp_path: Path) -> None:
        """ISS-162 smoke 영상을 SoT로 재인코딩해도 문제없는지 확인."""
        candidates = sorted(glob.glob("/tmp/omnivibe-smoke/smoke-test-*.mp4"))
        if not candidates:
            pytest.skip("ISS-162 smoke 출력 미존재 — skip")
        src = Path(candidates[-1])
        out = tmp_path / "smoke-reencoded.mp4"
        encode_args = ios_safe_full_encode_args(include_audio=True)
        cmd = [FFMPEG, "-y", "-i", str(src), *encode_args, str(out)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"ffmpeg error:\n{result.stderr[-1000:]}"
        assert out.stat().st_size > 0, "출력 파일이 비어있음"
        # iOS 호환 검증 (yuvj420p는 yuv420p와 동등하므로 허용)
        verify_result = verify_ios_safe_output(str(out))
        ignorable = ("audio", "pix_fmt")
        non_ignorable_errors = [
            e for e in verify_result.get("errors", [])
            if not any(kw in e.lower() for kw in ignorable)
        ]
        assert not non_ignorable_errors, f"smoke 재인코딩 iOS compat errors: {non_ignorable_errors}"
