#!/usr/bin/env python3
"""Vrew 기능 API 테스트 스크립트"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_remove_silence():
    """무음 제거 API 테스트"""
    print("\n=== 무음 제거 API 테스트 ===")

    # 테스트용 오디오 URL (예시)
    # 실제 테스트 시 유효한 오디오 URL로 변경 필요
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

    payload = {
        "audio_url": audio_url,
        "threshold_db": -40,
        "min_silence_duration": 0.5
    }

    print(f"\n1. 무음 제거 작업 시작...")
    print(f"   Audio URL: {audio_url}")

    response = requests.post(f"{BASE_URL}/audio/remove-silence", json=payload)

    if response.status_code == 200:
        result = response.json()
        task_id = result["task_id"]
        print(f"   ✅ 작업 시작 성공")
        print(f"   Task ID: {task_id}")

        # 작업 상태 확인
        print(f"\n2. 작업 상태 확인 중...")
        for i in range(30):  # 최대 30초 대기
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/audio/status/{task_id}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                print(f"   [{i*2}초] 상태: {status}")

                if status == "SUCCESS":
                    result = status_data.get("result", {})
                    print(f"\n   ✅ 무음 제거 완료!")
                    print(f"   원본 길이: {result.get('original_duration', 0):.2f}초")
                    print(f"   새 길이: {result.get('new_duration', 0):.2f}초")
                    print(f"   제거된 구간: {len(result.get('removed_segments', []))}개")
                    print(f"   처리된 파일: {result.get('processed_audio_url')}")
                    return True

                elif status == "FAILURE":
                    print(f"   ❌ 작업 실패: {status_data.get('error')}")
                    return False

        print(f"   ⏱️ 타임아웃")
        return False

    else:
        print(f"   ❌ API 호출 실패: {response.status_code}")
        print(f"   에러: {response.text}")
        return False


def test_remove_fillers():
    """필러 워드 제거 API 테스트"""
    print("\n=== 필러 워드 제거 API 테스트 ===")

    # 테스트용 오디오 URL (예시)
    # 실제 테스트 시 한국어 음성 파일 URL로 변경 필요
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

    payload = {
        "audio_url": audio_url,
        "filler_words": ["음", "어", "그", "저", "아"],
        "language": "ko"
    }

    print(f"\n1. 필러 워드 제거 작업 시작...")
    print(f"   Audio URL: {audio_url}")

    response = requests.post(f"{BASE_URL}/audio/remove-fillers", json=payload)

    if response.status_code == 200:
        result = response.json()
        task_id = result["task_id"]
        print(f"   ✅ 작업 시작 성공")
        print(f"   Task ID: {task_id}")

        # 작업 상태 확인
        print(f"\n2. 작업 상태 확인 중...")
        for i in range(60):  # 최대 60초 대기 (Whisper STT 시간 고려)
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/audio/status/{task_id}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                print(f"   [{i*2}초] 상태: {status}")

                if status == "SUCCESS":
                    result = status_data.get("result", {})
                    print(f"\n   ✅ 필러 워드 제거 완료!")
                    print(f"   원본 길이: {result.get('original_duration', 0):.2f}초")
                    print(f"   새 길이: {result.get('new_duration', 0):.2f}초")
                    print(f"   제거된 단어: {len(result.get('removed_words', []))}개")
                    print(f"   Transcript: {result.get('transcript', '')[:100]}...")
                    print(f"   처리된 파일: {result.get('processed_audio_url')}")

                    # 제거된 단어 목록 출력
                    removed_words = result.get('removed_words', [])
                    if removed_words:
                        print(f"\n   제거된 단어 목록:")
                        for word_data in removed_words[:5]:  # 처음 5개만 출력
                            print(f"     - {word_data['word']} ({word_data['start']:.2f}s - {word_data['end']:.2f}s)")

                    return True

                elif status == "FAILURE":
                    print(f"   ❌ 작업 실패: {status_data.get('error')}")
                    return False

        print(f"   ⏱️ 타임아웃")
        return False

    else:
        print(f"   ❌ API 호출 실패: {response.status_code}")
        print(f"   에러: {response.text}")
        return False


def test_api_docs():
    """API 문서 확인"""
    print("\n=== API 문서 확인 ===")

    response = requests.get(f"{BASE_URL}/../docs")

    if response.status_code == 200:
        print(f"   ✅ API 문서 접근 가능")
        print(f"   URL: http://localhost:8000/docs")
        return True
    else:
        print(f"   ❌ API 문서 접근 실패")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Vrew 기능 API 테스트")
    print("=" * 60)

    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Backend 서버 연결 성공")
    except Exception as e:
        print(f"❌ Backend 서버 연결 실패: {e}")
        print(f"   서버를 먼저 실행하세요: cd backend && uvicorn app.main:app --reload")
        exit(1)

    # 테스트 실행
    results = []

    # 1. 무음 제거 테스트
    # results.append(("무음 제거", test_remove_silence()))

    # 2. 필러 워드 제거 테스트
    # results.append(("필러 워드 제거", test_remove_fillers()))

    # 3. API 문서 확인
    results.append(("API 문서", test_api_docs()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    print("\n" + "=" * 60)
    print("참고:")
    print("- 실제 오디오 파일로 테스트하려면 audio_url을 유효한 URL로 변경하세요")
    print("- Celery worker가 실행 중인지 확인하세요")
    print("- OpenAI API 키가 설정되어 있는지 확인하세요 (필러 워드 제거)")
    print("=" * 60)
