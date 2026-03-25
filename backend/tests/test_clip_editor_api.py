"""클립 에디터 API 통합 테스트

대체 클립 생성 및 교체 API의 기본 동작을 검증하는 테스트입니다.

실행 방법:
    pytest test_clip_editor_api.py -v

또는:
    python test_clip_editor_api.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# FastAPI 앱 import
from app.main import app
from app.services.clip_editor_service import PromptVariationGenerator

client = TestClient(app)


# ==================== Fixtures ====================

@pytest.fixture
def mock_section_id():
    """테스트용 섹션 ID"""
    return "section_test123"


@pytest.fixture
def mock_clip_id():
    """테스트용 클립 ID"""
    return "clip_test456"


@pytest.fixture
def mock_veo_result():
    """Mock Veo API 결과"""
    return {
        "job_id": "veo_job_789",
        "status": "queued",
        "video_url": None,
        "estimated_time": 50
    }


@pytest.fixture
def mock_alternative_clips():
    """Mock 대체 클립 목록"""
    return {
        "section_id": "section_test123",
        "current_clip": {
            "clip_id": "clip_current",
            "video_path": "https://cloudinary.com/video1.mp4",
            "thumbnail_url": "https://cloudinary.com/thumb1.jpg",
            "prompt": "Original prompt",
            "created_at": datetime.utcnow().isoformat()
        },
        "alternatives": [
            {
                "clip_id": "clip_alt1",
                "video_path": "https://cloudinary.com/video2.mp4",
                "thumbnail_url": "https://cloudinary.com/thumb2.jpg",
                "prompt": "Close-up variation",
                "variation": "camera_angle",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "clip_id": "clip_alt2",
                "video_path": "https://cloudinary.com/video3.mp4",
                "thumbnail_url": "https://cloudinary.com/thumb3.jpg",
                "prompt": "Dramatic lighting variation",
                "variation": "lighting",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    }


# ==================== 프롬프트 변형 생성 테스트 ====================

def test_prompt_variation_generator_camera_angle():
    """카메라 앵글 변형 생성 테스트"""
    base_prompt = "A presenter explaining a concept"

    variations = PromptVariationGenerator.generate_camera_angle_variation(base_prompt)

    assert len(variations) == 3
    assert all("type" in v and v["type"] == "camera_angle" for v in variations)
    assert all("prompt" in v and base_prompt in v["prompt"] for v in variations)

    print("✓ Camera angle variations generated successfully")


def test_prompt_variation_generator_lighting():
    """조명 스타일 변형 생성 테스트"""
    base_prompt = "A presenter explaining a concept"

    variations = PromptVariationGenerator.generate_lighting_variation(base_prompt)

    assert len(variations) == 3
    assert all("type" in v and v["type"] == "lighting" for v in variations)

    print("✓ Lighting variations generated successfully")


def test_prompt_variation_generator_color_tone():
    """색감 변형 생성 테스트"""
    base_prompt = "A presenter explaining a concept"

    variations = PromptVariationGenerator.generate_color_tone_variation(base_prompt)

    assert len(variations) == 3
    assert all("type" in v and v["type"] == "color_tone" for v in variations)

    print("✓ Color tone variations generated successfully")


def test_prompt_variation_generator_all():
    """모든 변형 생성 테스트"""
    base_prompt = "A presenter explaining a concept"

    all_variations = PromptVariationGenerator.generate_all_variations(base_prompt)

    assert "camera_angle" in all_variations
    assert "lighting" in all_variations
    assert "color_tone" in all_variations

    assert len(all_variations["camera_angle"]) == 3
    assert len(all_variations["lighting"]) == 3
    assert len(all_variations["color_tone"]) == 3

    print("✓ All variations generated successfully")


# ==================== API 엔드포인트 테스트 (Mock) ====================

@patch("app.services.clip_editor_service.ClipEditorService.get_section_alternative_clips")
def test_get_section_alternative_clips_api(
    mock_get_clips,
    mock_section_id,
    mock_alternative_clips
):
    """대체 클립 목록 조회 API 테스트"""
    # Mock 설정
    mock_get_clips.return_value = mock_alternative_clips

    # API 호출
    response = client.get(f"/api/v1/sections/{mock_section_id}/alternative-clips")

    # 검증
    assert response.status_code == 200
    data = response.json()

    assert data["section_id"] == mock_section_id
    assert data["current_clip"] is not None
    assert len(data["alternatives"]) == 2

    print(f"✓ GET /sections/{mock_section_id}/alternative-clips succeeded")


@patch("app.services.clip_editor_service.ClipEditorService.generate_alternative_clips")
def test_generate_alternative_clips_api(
    mock_generate,
    mock_section_id
):
    """대체 클립 생성 API 테스트"""
    # Mock 설정
    mock_generate.return_value = [
        {
            "clip_id": "clip_new1",
            "variation_type": "camera_angle",
            "variation_description": "Close-up shot",
            "prompt": "Test prompt. Close-up shot",
            "veo_job_id": "veo_job_123",
            "status": "processing",
            "estimated_time": 50
        }
    ]

    # API 호출
    request_data = {
        "base_prompt": "A presenter explaining",
        "variations": ["camera_angle"]
    }

    response = client.post(
        f"/api/v1/sections/{mock_section_id}/alternative-clips",
        json=request_data
    )

    # 검증
    assert response.status_code == 200
    data = response.json()

    assert data["section_id"] == mock_section_id
    assert data["status"] == "processing"
    assert len(data["clips"]) >= 1

    print(f"✓ POST /sections/{mock_section_id}/alternative-clips succeeded")


@patch("app.services.clip_editor_service.ClipEditorService.replace_section_clip")
def test_replace_section_clip_api(
    mock_replace,
    mock_section_id,
    mock_clip_id
):
    """클립 교체 API 테스트"""
    # Mock 설정
    mock_replace.return_value = True

    # API 호출
    request_data = {
        "new_clip_id": mock_clip_id
    }

    response = client.patch(
        f"/api/v1/sections/{mock_section_id}/clip",
        json=request_data
    )

    # 검증
    assert response.status_code == 200
    data = response.json()

    assert data["section_id"] == mock_section_id
    assert data["new_clip_id"] == mock_clip_id
    assert data["status"] == "success"

    print(f"✓ PATCH /sections/{mock_section_id}/clip succeeded")


@patch("app.services.clip_editor_service.ClipEditorService.delete_alternative_clip")
def test_delete_alternative_clip_api(
    mock_delete,
    mock_section_id,
    mock_clip_id
):
    """대체 클립 삭제 API 테스트"""
    # Mock 설정
    mock_delete.return_value = True

    # API 호출
    response = client.delete(
        f"/api/v1/sections/{mock_section_id}/alternative-clips/{mock_clip_id}"
    )

    # 검증
    assert response.status_code == 200
    data = response.json()

    assert data["section_id"] == mock_section_id
    assert data["clip_id"] == mock_clip_id
    assert data["status"] == "success"

    print(f"✓ DELETE /sections/{mock_section_id}/alternative-clips/{mock_clip_id} succeeded")


# ==================== 엣지 케이스 테스트 ====================

@patch("app.services.clip_editor_service.ClipEditorService.replace_section_clip")
def test_replace_clip_not_found(mock_replace, mock_section_id):
    """존재하지 않는 클립 교체 시도 테스트"""
    # Mock 설정 - 실패
    mock_replace.return_value = False

    # API 호출
    request_data = {"new_clip_id": "nonexistent_clip"}

    response = client.patch(
        f"/api/v1/sections/{mock_section_id}/clip",
        json=request_data
    )

    # 검증
    assert response.status_code == 404

    print("✓ 404 error for nonexistent clip")


@patch("app.services.clip_editor_service.ClipEditorService.delete_alternative_clip")
def test_delete_clip_not_found(mock_delete, mock_section_id):
    """존재하지 않는 클립 삭제 시도 테스트"""
    # Mock 설정 - 실패
    mock_delete.return_value = False

    # API 호출
    response = client.delete(
        f"/api/v1/sections/{mock_section_id}/alternative-clips/nonexistent_clip"
    )

    # 검증
    assert response.status_code == 404

    print("✓ 404 error for nonexistent clip deletion")


# ==================== 실행 ====================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("클립 에디터 API 통합 테스트")
    print("="*70 + "\n")

    # 프롬프트 변형 생성 테스트
    print("1. 프롬프트 변형 생성 테스트")
    print("-" * 70)
    test_prompt_variation_generator_camera_angle()
    test_prompt_variation_generator_lighting()
    test_prompt_variation_generator_color_tone()
    test_prompt_variation_generator_all()

    print("\n2. API 엔드포인트 테스트 (Mock)")
    print("-" * 70)

    # Mock 데이터 준비
    section_id = "section_test123"
    clip_id = "clip_test456"
    alternative_clips = {
        "section_id": section_id,
        "current_clip": {
            "clip_id": "clip_current",
            "video_path": "https://cloudinary.com/video1.mp4",
            "thumbnail_url": "https://cloudinary.com/thumb1.jpg",
            "prompt": "Original prompt",
            "created_at": datetime.utcnow().isoformat()
        },
        "alternatives": []
    }

    # Mock을 사용한 테스트 실행
    with patch("app.services.clip_editor_service.ClipEditorService.get_section_alternative_clips") as mock1:
        mock1.return_value = alternative_clips
        test_get_section_alternative_clips_api(mock1, section_id, alternative_clips)

    with patch("app.services.clip_editor_service.ClipEditorService.generate_alternative_clips") as mock2:
        test_generate_alternative_clips_api(mock2, section_id)

    with patch("app.services.clip_editor_service.ClipEditorService.replace_section_clip") as mock3:
        test_replace_section_clip_api(mock3, section_id, clip_id)

    with patch("app.services.clip_editor_service.ClipEditorService.delete_alternative_clip") as mock4:
        test_delete_alternative_clip_api(mock4, section_id, clip_id)

    print("\n3. 엣지 케이스 테스트")
    print("-" * 70)

    with patch("app.services.clip_editor_service.ClipEditorService.replace_section_clip") as mock5:
        test_replace_clip_not_found(mock5, section_id)

    with patch("app.services.clip_editor_service.ClipEditorService.delete_alternative_clip") as mock6:
        test_delete_clip_not_found(mock6, section_id)

    print("\n" + "="*70)
    print("모든 테스트 통과!")
    print("="*70 + "\n")
