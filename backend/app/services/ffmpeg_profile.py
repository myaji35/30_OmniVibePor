"""
FFmpeg iOS Safe Profile — 단일 진실 소스(Single Source of Truth)

ISS-031/032 회귀 방지의 핵심 모듈.

배경:
    - ISS-031에서 yuv420p+faststart만 추가했으나, iPhone에서 화면-음성 싱크 어긋남 회귀 발생
    - 원인: -r 30, -vsync cfr, -profile:v high, -level:v 4.1, -ar 48000, -af aresample=async=1 누락
    - macOS h264_videotoolbox는 fps/profile을 자동 보장하지 않음
    - ISS-032에서 8곳에 흩어 fix → ISS-037에서 단일 모듈로 추출하여 회귀 방지

원칙:
    1. 모든 ffmpeg 호출은 이 모듈의 함수에서 args를 받아야 한다
    2. 직접 ["-c:v", "libx264", ...] 같은 하드코딩 금지
    3. 새 ffmpeg 명령 추가 시 이 모듈에 헬퍼를 먼저 추가하라
    4. iOS 호환 표준이 변경되면 이 한 파일만 수정한다

iOS 호환 표준 (memory: feedback_ios_mp4_format.md):
    -c:v libx264 (또는 h264_videotoolbox + 동일 profile/level 강제)
    -preset medium
    -crf 23
    -r 30                    # 30fps 필수 (낮은 fps는 iPhone에서 이미지 안 보임)
    -vsync cfr               # CFR 강제 (iPhone은 VFR에서 싱크 깨짐)
    -pix_fmt yuv420p         # iOS 하드웨어 디코딩 필수
    -profile:v high          # iOS 최대 안정 프로파일
    -level:v 4.1             # iOS 최대 안정 레벨
    -c:a aac
    -b:a 192k
    -ar 48000                # 48kHz 샘플레이트 (44.1k는 일부 iPhone에서 깨짐)
    -af aresample=async=1:first_pts=0  # 오디오 싱크 자동 보정
    -movflags +faststart     # moov atom 앞으로 이동 (스트리밍/프리뷰)
"""
from __future__ import annotations

import platform
import subprocess
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# 표준 상수 — 변경 시 ISS-037 검증 재실행 필요
# ─────────────────────────────────────────────────────────────────────────────

IOS_SAFE_FPS = "30"
IOS_SAFE_PIX_FMT = "yuv420p"
IOS_SAFE_PROFILE = "high"
IOS_SAFE_LEVEL = "4.1"
IOS_SAFE_PRESET = "medium"
IOS_SAFE_CRF = "23"
IOS_SAFE_AUDIO_CODEC = "aac"
IOS_SAFE_AUDIO_BITRATE = "192k"
IOS_SAFE_AUDIO_SAMPLE_RATE = "48000"
IOS_SAFE_VIDEO_CODEC = "libx264"
IOS_SAFE_HW_VIDEO_CODEC = "h264_videotoolbox"  # macOS only
IOS_SAFE_HW_VIDEO_BITRATE = "5M"

# aresample async 보정 필터 — 영상 합성 마지막 단계에서 오디오 드리프트 방지
IOS_SAFE_AUDIO_FILTER = "aresample=async=1:first_pts=0"


# ─────────────────────────────────────────────────────────────────────────────
# 비디오 인코딩 args
# ─────────────────────────────────────────────────────────────────────────────

def ios_safe_video_encoder_args(
    *,
    use_hw_acceleration: bool = False,
    preset: str = IOS_SAFE_PRESET,
    crf: str = IOS_SAFE_CRF,
    extra_tune: Optional[str] = None,
) -> List[str]:
    """
    iOS 호환 비디오 인코더 args.

    Args:
        use_hw_acceleration: macOS VideoToolbox(h264_videotoolbox) 사용 여부.
            True 시 더 빠르지만 동일한 profile/level/CFR 강제 적용됨.
        preset: libx264 preset (ultrafast..veryslow). HW accel 시 무시됨.
        crf: libx264 CRF (낮을수록 고품질). HW accel 시 무시됨.
        extra_tune: libx264 -tune (예: "stillimage"). HW accel 시 무시됨.

    Returns:
        FFmpeg cmd에 그대로 extend 할 수 있는 args 리스트.
    """
    if use_hw_acceleration:
        args = [
            "-c:v", IOS_SAFE_HW_VIDEO_CODEC,
            "-b:v", IOS_SAFE_HW_VIDEO_BITRATE,
            "-profile:v", IOS_SAFE_PROFILE,
            "-level:v", IOS_SAFE_LEVEL,
        ]
    else:
        args = [
            "-c:v", IOS_SAFE_VIDEO_CODEC,
            "-preset", preset,
            "-crf", crf,
        ]
        if extra_tune:
            args.extend(["-tune", extra_tune])
        args.extend([
            "-profile:v", IOS_SAFE_PROFILE,
            "-level:v", IOS_SAFE_LEVEL,
        ])
    return args


def ios_safe_video_output_args(
    *,
    include_pix_fmt: bool = True,
    include_fps: bool = True,
    include_vsync: bool = True,
    include_faststart: bool = True,
    threads: Optional[str] = "0",
) -> List[str]:
    """
    인코더 뒤에 붙는 표준 출력 args.

    이 함수가 보장하는 것:
        - yuv420p (iOS 하드웨어 디코딩)
        - 30fps CFR (가변 fps 차단)
        - faststart (moov atom 앞으로)

    개별 옵션을 끄려면 키워드로 False 지정.
    """
    args: List[str] = []
    if include_pix_fmt:
        args.extend(["-pix_fmt", IOS_SAFE_PIX_FMT])
    if include_fps:
        args.extend(["-r", IOS_SAFE_FPS])
    if include_vsync:
        args.extend(["-vsync", "cfr"])
    if include_faststart:
        args.extend(["-movflags", "+faststart"])
    if threads is not None:
        args.extend(["-threads", threads])
    return args


# ─────────────────────────────────────────────────────────────────────────────
# 오디오 인코딩 args
# ─────────────────────────────────────────────────────────────────────────────

def ios_safe_audio_encoder_args(
    *,
    bitrate: str = IOS_SAFE_AUDIO_BITRATE,
    include_async_filter: bool = True,
) -> List[str]:
    """
    iOS 호환 오디오 인코더 args.

    Args:
        bitrate: AAC 비트레이트 (기본 192k).
        include_async_filter: aresample async 보정 필터 포함 여부.
            영상-오디오 결합 단계에서 True 권장 (싱크 어긋남 방지).
            중간 클립 생성 단계에서는 False도 OK.

    Returns:
        FFmpeg cmd args.
    """
    args = [
        "-c:a", IOS_SAFE_AUDIO_CODEC,
        "-b:a", bitrate,
        "-ar", IOS_SAFE_AUDIO_SAMPLE_RATE,
    ]
    if include_async_filter:
        args.extend(["-af", IOS_SAFE_AUDIO_FILTER])
    return args


# ─────────────────────────────────────────────────────────────────────────────
# 컴포지트 헬퍼 — 자주 쓰는 패턴
# ─────────────────────────────────────────────────────────────────────────────

def ios_safe_full_encode_args(
    *,
    use_hw_acceleration: bool = False,
    preset: str = IOS_SAFE_PRESET,
    crf: str = IOS_SAFE_CRF,
    extra_tune: Optional[str] = None,
    include_audio: bool = True,
    audio_async_filter: bool = True,
    threads: Optional[str] = "0",
) -> List[str]:
    """
    이미지/슬라이드/짧은 클립을 비디오로 인코딩할 때 쓰는 풀세트.

    포함:
        - 비디오 인코더 (libx264 또는 h264_videotoolbox)
        - profile:v high, level:v 4.1
        - pix_fmt yuv420p
        - r 30, vsync cfr
        - movflags faststart
        - (옵션) AAC 192k 48kHz + async 필터

    예시:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", audio]
        cmd.extend(ios_safe_full_encode_args(use_hw_acceleration=True, extra_tune="stillimage"))
        cmd.extend(["-shortest", output_path])
    """
    args = ios_safe_video_encoder_args(
        use_hw_acceleration=use_hw_acceleration,
        preset=preset,
        crf=crf,
        extra_tune=extra_tune,
    )
    args.extend(ios_safe_video_output_args(threads=threads))
    if include_audio:
        args.extend(ios_safe_audio_encoder_args(include_async_filter=audio_async_filter))
    return args


def ios_safe_audio_mux_args(
    *,
    video_codec_copy: bool = True,
    audio_async_filter: bool = True,
    audio_bitrate: str = IOS_SAFE_AUDIO_BITRATE,
) -> List[str]:
    """
    이미 인코딩된 비디오에 오디오를 mux 할 때 쓰는 args.

    포함:
        - -c:v copy (재인코딩 없음, 빠름)
        - AAC 192k 48kHz + async 필터
        - faststart

    use case: 슬라이드들을 xfade로 묶은 후 최종 오디오 합성 단계.
    """
    args: List[str] = []
    if video_codec_copy:
        args.extend(["-c:v", "copy"])
    args.extend(ios_safe_audio_encoder_args(
        bitrate=audio_bitrate,
        include_async_filter=audio_async_filter,
    ))
    args.extend(["-movflags", "+faststart"])
    return args


def ios_safe_subtitle_burn_args(
    *,
    preset: str = IOS_SAFE_PRESET,
    crf: str = IOS_SAFE_CRF,
    audio_codec_copy: bool = True,
) -> List[str]:
    """
    자막을 영상에 burn-in 할 때 쓰는 args.

    이 단계는 비디오 재인코딩이 필수(자막 픽셀 합성)이므로
    full encode args + 오디오 copy 패턴.
    """
    args = ios_safe_video_encoder_args(
        use_hw_acceleration=False,  # 자막 burn은 SW 인코딩 권장 (정확도)
        preset=preset,
        crf=crf,
    )
    args.extend(ios_safe_video_output_args())
    if audio_codec_copy:
        args.extend(["-c:a", "copy"])
    return args


def ios_safe_concat_demuxer_args() -> List[str]:
    """
    FFmpeg concat demuxer로 동일 codec/spec 클립을 이어붙일 때 쓰는 args.

    재인코딩 없이 빠른 결합을 위해 -c copy 사용.
    단 결합 대상 클립들이 모두 ios_safe 표준으로 인코딩되어 있어야 함.
    """
    return ["-c", "copy"]


# ─────────────────────────────────────────────────────────────────────────────
# 하드웨어 가속 검출
# ─────────────────────────────────────────────────────────────────────────────

def detect_hardware_acceleration() -> Optional[Dict[str, List[str]]]:
    """
    하드웨어 가속 사용 가능 여부 검출.

    Returns:
        {"input": [...], "encoder": [...]} 형태 dict, 또는 None.

        encoder는 ios_safe_video_encoder_args(use_hw_acceleration=True)와
        동일한 결과 — profile/level이 강제 적용된 상태.

    Note:
        macOS Darwin에서만 VideoToolbox 가속 활성화.
        Linux/Windows는 None 반환 (SW 인코딩으로 fallback).
    """
    system = platform.system()

    if system == "Darwin":
        try:
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return {
                "input": [],  # VideoToolbox는 별도 input flag 불필요
                "encoder": ios_safe_video_encoder_args(use_hw_acceleration=True),
            }
        except Exception:
            return None

    # Linux NVIDIA(h264_nvenc) / Intel(h264_qsv) 등은 향후 확장
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 검증 헬퍼 (테스트/CI에서 사용)
# ─────────────────────────────────────────────────────────────────────────────

def verify_ios_safe_output(file_path: str) -> Dict[str, object]:
    """
    ffprobe로 출력 파일이 iOS 호환 표준을 따르는지 검증.

    Returns:
        {
            "ok": bool,
            "fps": float,
            "profile": str,
            "level": int,
            "pix_fmt": str,
            "audio_sample_rate": int,
            "errors": [str, ...]
        }

    사용 예 (테스트 코드):
        result = verify_ios_safe_output("output.mp4")
        assert result["ok"], result["errors"]
    """
    import json

    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_streams", "-show_format",
                "-of", "json", file_path,
            ],
            capture_output=True, text=True, check=True, timeout=30,
        )
        data = json.loads(proc.stdout)
    except Exception as e:
        return {"ok": False, "errors": [f"ffprobe failed: {e}"]}

    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    errors: List[str] = []

    if not video:
        errors.append("no video stream")
        return {"ok": False, "errors": errors}

    # fps 계산
    fps_str = video.get("r_frame_rate", "0/1")
    try:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 0.0
    except Exception:
        fps = 0.0

    profile = video.get("profile", "")
    level = video.get("level", 0)
    pix_fmt = video.get("pix_fmt", "")

    if abs(fps - 30.0) > 0.5:
        errors.append(f"fps={fps} (expected ~30)")
    if profile.lower() != "high":
        errors.append(f"profile={profile} (expected High)")
    if level != 41:
        errors.append(f"level={level} (expected 41)")
    if pix_fmt != IOS_SAFE_PIX_FMT:
        errors.append(f"pix_fmt={pix_fmt} (expected {IOS_SAFE_PIX_FMT})")

    audio_sr = 0
    if audio:
        try:
            audio_sr = int(audio.get("sample_rate", 0))
        except Exception:
            audio_sr = 0
        if audio_sr != int(IOS_SAFE_AUDIO_SAMPLE_RATE):
            errors.append(f"audio sample_rate={audio_sr} (expected {IOS_SAFE_AUDIO_SAMPLE_RATE})")

    return {
        "ok": len(errors) == 0,
        "fps": fps,
        "profile": profile,
        "level": level,
        "pix_fmt": pix_fmt,
        "audio_sample_rate": audio_sr,
        "errors": errors,
    }
