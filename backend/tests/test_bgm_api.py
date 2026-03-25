"""BGM API 테스트 스크립트

BGM 업로드, 조회, 수정, 삭제 API를 테스트합니다.
"""
import requests
import json
from pathlib import Path

# API 기본 URL
BASE_URL = "http://localhost:8000/api/v1"

# 테스트 프로젝트 ID (실제 존재하는 프로젝트 ID 사용 필요)
PROJECT_ID = "proj_test123"


def test_upload_bgm():
    """BGM 파일 업로드 테스트"""
    print("\n=== Test 1: BGM Upload ===")

    # 테스트용 BGM 파일 경로 (실제 파일로 교체 필요)
    test_bgm_path = Path("test_bgm.mp3")

    if not test_bgm_path.exists():
        print(f"❌ Test BGM file not found: {test_bgm_path}")
        print("ℹ️  Please create a test BGM file or update the path")
        return None

    url = f"{BASE_URL}/projects/{PROJECT_ID}/bgm/upload"

    with open(test_bgm_path, "rb") as f:
        files = {"bgm_file": ("test_bgm.mp3", f, "audio/mpeg")}
        data = {
            "volume": 0.3,
            "fade_in_duration": 2.0,
            "fade_out_duration": 2.0,
            "start_time": 0.0,
            "loop": True,
            "ducking_enabled": True,
            "ducking_level": 0.3
        }

        response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        print("✅ BGM uploaded successfully")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None


def test_get_bgm():
    """BGM 설정 조회 테스트"""
    print("\n=== Test 2: Get BGM Settings ===")

    url = f"{BASE_URL}/projects/{PROJECT_ID}/bgm"
    response = requests.get(url)

    if response.status_code == 200:
        print("✅ BGM settings retrieved successfully")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    elif response.status_code == 404:
        print("❌ BGM settings not found (404)")
        print("ℹ️  Please upload a BGM file first")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

    return None


def test_update_bgm():
    """BGM 설정 업데이트 테스트"""
    print("\n=== Test 3: Update BGM Settings ===")

    url = f"{BASE_URL}/projects/{PROJECT_ID}/bgm"

    updates = {
        "volume": 0.5,
        "fade_in_duration": 3.0,
        "ducking_enabled": False
    }

    response = requests.patch(url, json=updates)

    if response.status_code == 200:
        print("✅ BGM settings updated successfully")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    else:
        print(f"❌ Update failed: {response.status_code}")
        print(response.text)
        return None


def test_delete_bgm():
    """BGM 삭제 테스트"""
    print("\n=== Test 4: Delete BGM ===")

    url = f"{BASE_URL}/projects/{PROJECT_ID}/bgm"
    response = requests.delete(url)

    if response.status_code == 200:
        print("✅ BGM deleted successfully")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    else:
        print(f"❌ Delete failed: {response.status_code}")
        print(response.text)
        return None


def main():
    """전체 테스트 실행"""
    print("=" * 50)
    print("BGM API Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Project ID: {PROJECT_ID}")

    # 1. BGM 업로드
    upload_result = test_upload_bgm()

    if upload_result:
        # 2. BGM 조회
        test_get_bgm()

        # 3. BGM 업데이트
        test_update_bgm()

        # 4. 업데이트 후 재조회
        print("\n=== Test 5: Get BGM After Update ===")
        test_get_bgm()

        # 5. BGM 삭제 (선택사항 - 주석 처리)
        # test_delete_bgm()

    print("\n" + "=" * 50)
    print("Test Suite Completed")
    print("=" * 50)


if __name__ == "__main__":
    main()
