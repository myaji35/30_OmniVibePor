#!/usr/bin/env python3
"""커스텀 프리셋 API 임포트 및 기본 검증 테스트"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

try:
    # 모델 임포트 테스트
    from app.models.neo4j_models import (
        CustomPresetModel,
        CustomPresetCreateRequest,
        CustomPresetUpdateRequest,
        CustomPresetResponse,
        CustomPresetListResponse,
        VideoSettingsModel,
        SubtitleStyleModel,
        BGMSettingsModel
    )
    print("✓ 모델 임포트 성공")

    # API 라우터 임포트 테스트
    from app.api.v1.presets import router
    print("✓ API 라우터 임포트 성공")

    # 라우터 경로 확인
    print("\n[등록된 엔드포인트]")
    for route in router.routes:
        methods = ", ".join(route.methods) if hasattr(route, 'methods') else "N/A"
        print(f"  {methods:8s} {route.path}")

    # 기본 모델 생성 테스트
    print("\n[모델 생성 테스트]")

    # VideoSettingsModel
    video_settings = VideoSettingsModel()
    print(f"✓ VideoSettingsModel 생성: resolution={video_settings.resolution}")

    # SubtitleStyleModel
    subtitle_style = SubtitleStyleModel()
    print(f"✓ SubtitleStyleModel 생성: font_size={subtitle_style.font_size}")

    # CustomPresetModel (BGMSettingsModel은 bgm_file_path가 필수)
    bgm_settings = BGMSettingsModel(bgm_file_path="/test/bgm.mp3")
    preset = CustomPresetModel(
        user_id="test_user_123",
        name="테스트 프리셋",
        description="테스트용 프리셋입니다",
        subtitle_style=subtitle_style,
        bgm_settings=bgm_settings,
        video_settings=video_settings
    )
    print(f"✓ CustomPresetModel 생성: preset_id={preset.preset_id}")

    print("\n[전체 테스트 성공]")
    print("모든 모델과 API 라우터가 정상적으로 임포트되었습니다.")

except Exception as e:
    print(f"\n[에러 발생]")
    print(f"에러 타입: {type(e).__name__}")
    print(f"에러 메시지: {str(e)}")
    import traceback
    print("\n[상세 트레이스백]")
    traceback.print_exc()
    sys.exit(1)
