#!/usr/bin/env python3
"""자막 API 테스트 스크립트

이 스크립트는 자막 조정 API의 기본 기능을 테스트합니다.
실제 서버가 실행 중이어야 합니다.

사용법:
    python test_subtitle_api.py
"""
import requests
import json
from typing import Dict, Any

# API 베이스 URL
BASE_URL = "http://localhost:8000/api/v1"

# 테스트용 프로젝트 ID (실제 프로젝트 ID로 변경 필요)
TEST_PROJECT_ID = "proj_test123"


def print_response(title: str, response: requests.Response):
    """응답을 보기 좋게 출력"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def test_get_subtitle_style():
    """자막 스타일 조회 테스트"""
    url = f"{BASE_URL}/projects/{TEST_PROJECT_ID}/subtitles"
    response = requests.get(url)
    print_response("1. 자막 스타일 조회 (GET /subtitles)", response)
    return response.json() if response.status_code == 200 else None


def test_update_subtitle_style():
    """자막 스타일 업데이트 테스트"""
    url = f"{BASE_URL}/projects/{TEST_PROJECT_ID}/subtitles"

    # 업데이트할 스타일
    update_data = {
        "font_size": 32,
        "font_color": "#FFFF00",  # 노란색
        "background_opacity": 0.5,
        "position": "top",
        "alignment": "center"
    }

    response = requests.patch(url, json=update_data)
    print_response("2. 자막 스타일 업데이트 (PATCH /subtitles)", response)
    return response.json() if response.status_code == 200 else None


def test_generate_preview():
    """자막 미리보기 생성 테스트"""
    url = f"{BASE_URL}/projects/{TEST_PROJECT_ID}/subtitles/preview"

    # 미리보기 요청
    preview_data = {
        "start_time": 0.0,
        "duration": 5.0,
        "style": {
            "font_size": 28,
            "font_color": "#00FF00",  # 녹색
            "outline_width": 2
        }
    }

    response = requests.post(url, json=preview_data)
    print_response("3. 자막 미리보기 생성 (POST /subtitles/preview)", response)
    return response.json() if response.status_code == 200 else None


def test_subtitle_style_variations():
    """다양한 스타일 변형 테스트"""
    url = f"{BASE_URL}/projects/{TEST_PROJECT_ID}/subtitles"

    test_styles = [
        {
            "name": "유튜브 스타일",
            "data": {
                "font_family": "Arial",
                "font_size": 28,
                "font_color": "#FFFFFF",
                "background_opacity": 0.8,
                "outline_width": 2,
                "position": "bottom"
            }
        },
        {
            "name": "틱톡 스타일",
            "data": {
                "font_family": "Impact",
                "font_size": 36,
                "font_color": "#FFFF00",
                "outline_width": 3,
                "outline_color": "#000000",
                "position": "center"
            }
        },
        {
            "name": "미니멀 스타일",
            "data": {
                "font_family": "Helvetica",
                "font_size": 22,
                "font_color": "#FFFFFF",
                "background_opacity": 0.3,
                "outline_width": 1,
                "position": "bottom"
            }
        }
    ]

    print(f"\n{'='*60}")
    print("4. 다양한 스타일 변형 테스트")
    print(f"{'='*60}")

    for style_test in test_styles:
        print(f"\n>>> {style_test['name']}")
        response = requests.patch(url, json=style_test['data'])
        if response.status_code == 200:
            print("✓ 성공")
        else:
            print(f"✗ 실패: {response.status_code}")
            print(response.text)


def test_error_handling():
    """에러 처리 테스트"""
    print(f"\n{'='*60}")
    print("5. 에러 처리 테스트")
    print(f"{'='*60}")

    # 존재하지 않는 프로젝트
    print("\n>>> 존재하지 않는 프로젝트")
    url = f"{BASE_URL}/projects/invalid_project_id/subtitles"
    response = requests.get(url)
    print(f"Status: {response.status_code} (예상: 404)")

    # 잘못된 스타일 값
    print("\n>>> 잘못된 폰트 크기 (범위 초과)")
    url = f"{BASE_URL}/projects/{TEST_PROJECT_ID}/subtitles"
    invalid_data = {"font_size": 100}  # 최대값 72 초과
    response = requests.patch(url, json=invalid_data)
    print(f"Status: {response.status_code} (예상: 422)")

    # 잘못된 투명도 값
    print("\n>>> 잘못된 투명도 값 (범위 초과)")
    invalid_data = {"background_opacity": 1.5}  # 최대값 1.0 초과
    response = requests.patch(url, json=invalid_data)
    print(f"Status: {response.status_code} (예상: 422)")


def main():
    """메인 테스트 실행"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         OmniVibe Pro - 자막 조정 API 테스트              ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    print(f"테스트 대상: {BASE_URL}")
    print(f"프로젝트 ID: {TEST_PROJECT_ID}")
    print("\n서버가 실행 중인지 확인하세요!")
    print("(backend 디렉토리에서 'uvicorn app.main:app --reload' 실행)")

    input("\nEnter를 눌러 테스트 시작...")

    try:
        # 1. 기본 조회
        test_get_subtitle_style()

        # 2. 스타일 업데이트
        test_update_subtitle_style()

        # 3. 미리보기 생성
        # test_generate_preview()  # 주석 처리: 실제 비디오/SRT 파일 필요

        # 4. 다양한 스타일 테스트
        test_subtitle_style_variations()

        # 5. 에러 처리 테스트
        test_error_handling()

        print(f"\n{'='*60}")
        print("✓ 모든 테스트 완료!")
        print(f"{'='*60}\n")

    except requests.exceptions.ConnectionError:
        print("\n✗ 서버에 연결할 수 없습니다!")
        print("FastAPI 서버가 실행 중인지 확인하세요.")
        print("실행 명령: uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
