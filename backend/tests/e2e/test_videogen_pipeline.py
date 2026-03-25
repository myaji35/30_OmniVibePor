"""
VIDEOGEN 경로 B — E2E 파이프라인 테스트

실제 MP3 + SRT 파일을 사용하여 전체 파이프라인을 검증한다.
실행: pytest tests/e2e/test_videogen_pipeline.py -v
"""
import subprocess
import sys
import json
import os
import pytest
from pathlib import Path

# 프로젝트 루트 (backend/ 기준으로 상위)
PROJECT_ROOT = Path(__file__).parents[3]
SKILLS_DIR   = PROJECT_ROOT / ".claude" / "skills" / "videogen"
VIDEOGEN_DIR = PROJECT_ROOT / "videogen"
INPUT_DIR    = VIDEOGEN_DIR / "input"
OUTPUT_DIR   = VIDEOGEN_DIR / "output"
WORKSPACE    = VIDEOGEN_DIR / "workspace"


# ── 픽스처: 테스트용 SRT 샘플 ──────────────────────────────────────
SAMPLE_SRT = """\
1
00:00:00,000 --> 00:00:02,500
안녕하세요

2
00:00:02,800 --> 00:00:05,000
오늘은 AI 영상 자동화를

3
00:00:05,200 --> 00:00:08,500
소개합니다

4
00:00:10,000 --> 00:00:13,000
OmniVibe Pro는

5
00:00:13,300 --> 00:00:16,500
스크립트 한 줄로 영상을 만듭니다

6
00:00:18,000 --> 00:00:21,000
지금 바로 시작하세요
"""


@pytest.fixture(scope="module", autouse=True)
def setup_videogen_dirs():
    """테스트용 디렉토리 및 파일 준비"""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    # SRT 파일 생성
    srt_path = INPUT_DIR / "subtitles.srt"
    srt_path.write_text(SAMPLE_SRT, encoding="utf-8")

    # MP3 더미 파일 (실제 테스트 시 교체)
    mp3_path = INPUT_DIR / "dubbing.mp3"
    if not mp3_path.exists():
        # 1초짜리 사일런트 mp3 생성 (ffmpeg 필요)
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", "22", "-q:a", "9", "-acodec", "libmp3lame", str(mp3_path)],
            capture_output=True
        )
        if result.returncode != 0:
            # ffmpeg 없으면 빈 파일로 대체
            mp3_path.write_bytes(b"")

    yield

    # 정리 (선택적 — CI에서는 출력 보존)
    # shutil.rmtree(WORKSPACE, ignore_errors=True)


# ── 테스트 케이스 ──────────────────────────────────────────────────

class TestSceneAnalyzer:
    """Step 1: SRT 파싱 및 씬 그룹핑"""

    def test_srt_file_exists(self):
        assert (INPUT_DIR / "subtitles.srt").exists(), "SRT 파일이 없습니다"

    def test_scene_analyzer_runs(self):
        """scene-analyzer.ts 실행 → workspace/scenes.json 생성 확인"""
        result = subprocess.run(
            ["npx", "ts-node", str(SKILLS_DIR / "scene-analyzer.ts")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # ts-node 미설치 시 skip
        if result.returncode == 127:
            pytest.skip("ts-node 미설치")

        assert result.returncode == 0, f"scene-analyzer 실패:\n{result.stderr}"

    def test_scenes_json_structure(self):
        """scenes.json 구조 검증"""
        scenes_path = WORKSPACE / "scenes.json"
        if not scenes_path.exists():
            pytest.skip("scenes.json 미생성 (scene-analyzer 미실행)")

        data = json.loads(scenes_path.read_text())
        assert "scenes" in data, "scenes 키 없음"
        assert len(data["scenes"]) > 0, "씬이 0개"

        for scene in data["scenes"]:
            assert "id" in scene
            assert "startMs" in scene
            assert "endMs" in scene
            assert "subtitles" in scene
            assert len(scene["subtitles"]) > 0

    def test_scene_gap_detection(self):
        """1.5초 이상 gap → 씬 분리 검증"""
        scenes_path = WORKSPACE / "scenes.json"
        if not scenes_path.exists():
            pytest.skip("scenes.json 미생성")

        data = json.loads(scenes_path.read_text())
        scenes = data["scenes"]
        # 샘플 SRT에서 10초 공백이 있으므로 2개 이상 씬이어야 함
        assert len(scenes) >= 2, f"씬 분리 실패: {len(scenes)}개"


class TestLayoutSelector:
    """Step 2: 씬 → 레이아웃 자동 선택"""

    def test_layout_selector_runs(self):
        result = subprocess.run(
            ["npx", "ts-node", str(SKILLS_DIR / "layout-selector.ts")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 127:
            pytest.skip("ts-node 미설치")
        assert result.returncode == 0, f"layout-selector 실패:\n{result.stderr}"

    def test_layout_assigned(self):
        scenes_path = WORKSPACE / "scenes.json"
        if not scenes_path.exists():
            pytest.skip("scenes.json 미생성")

        data = json.loads(scenes_path.read_text())
        for scene in data["scenes"]:
            assert "layout" in scene, f"씬 {scene.get('id')}에 layout 없음"
            valid_layouts = [
                "text-center", "text-image", "infographic",
                "list-reveal", "full-visual", "split-screen", "graph-focus"
            ]
            assert scene["layout"] in valid_layouts, f"미지원 레이아웃: {scene['layout']}"


class TestRemotionCodegen:
    """Step 3: Remotion 컴포넌트 코드 자동 생성"""

    def test_codegen_runs(self):
        result = subprocess.run(
            ["npx", "ts-node", str(SKILLS_DIR / "remotion-codegen.ts")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "DEV_MODE": "true"},
        )
        if result.returncode == 127:
            pytest.skip("ts-node 미설치")
        assert result.returncode == 0, f"remotion-codegen 실패:\n{result.stderr}"

    def test_generated_files_exist(self):
        """필수 생성 파일 존재 확인"""
        workspace_src = WORKSPACE / "src"
        if not workspace_src.exists():
            pytest.skip("workspace/src 미생성")

        required = ["GeneratedVideo.tsx", "index.ts"]
        for fname in required:
            assert (workspace_src / fname).exists(), f"{fname} 미생성"

    def test_scene_components_exist(self):
        """씬 컴포넌트 파일 생성 확인"""
        workspace_src = WORKSPACE / "src"
        if not workspace_src.exists():
            pytest.skip("workspace/src 미생성")

        scene_files = list(workspace_src.glob("Scene*.tsx"))
        assert len(scene_files) > 0, "씬 컴포넌트 미생성"

    def test_dev_mode_overlay_in_code(self):
        """DEV_MODE=true 시 씬 번호 오버레이 코드 포함 확인"""
        workspace_src = WORKSPACE / "src"
        if not workspace_src.exists():
            pytest.skip("workspace/src 미생성")

        scene_files = list(workspace_src.glob("Scene*.tsx"))
        for f in scene_files:
            content = f.read_text()
            assert "devMode" in content or "SCENE" in content, \
                f"{f.name}에 DEV 오버레이 없음"


class TestRemotionRender:
    """Step 4: Remotion 렌더링 실행 (DEV_MODE)"""

    @pytest.mark.slow
    def test_dev_render(self):
        """DEV_MODE=true 렌더링 → preview MP4 생성"""
        workspace = WORKSPACE
        if not (workspace / "src" / "GeneratedVideo.tsx").exists():
            pytest.skip("GeneratedVideo.tsx 미생성")

        result = subprocess.run(
            ["npx", "remotion", "render", "src/index.ts", "GeneratedVideo",
             str(OUTPUT_DIR / f"preview_test.mp4"),
             "--props", json.dumps({"devMode": True})],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 127:
            pytest.skip("remotion CLI 미설치")

        assert result.returncode == 0, f"Remotion 렌더 실패:\n{result.stderr}"
        assert (OUTPUT_DIR / "preview_test.mp4").exists(), "MP4 파일 미생성"

    @pytest.mark.slow
    def test_final_render(self):
        """DEV_MODE=false 최종 렌더링"""
        workspace = WORKSPACE
        if not (workspace / "src" / "GeneratedVideo.tsx").exists():
            pytest.skip("GeneratedVideo.tsx 미생성")

        result = subprocess.run(
            ["npx", "remotion", "render", "src/index.ts", "GeneratedVideo",
             str(OUTPUT_DIR / f"final_test.mp4"),
             "--props", json.dumps({"devMode": False})],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 127:
            pytest.skip("remotion CLI 미설치")

        assert result.returncode == 0, f"최종 렌더 실패:\n{result.stderr}"
        mp4 = OUTPUT_DIR / "final_test.mp4"
        assert mp4.exists()
        assert mp4.stat().st_size > 1024, "MP4 파일이 너무 작음"
