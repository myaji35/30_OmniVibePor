#!/usr/bin/env python3
"""비용 추적 API 테스트 스크립트

FastAPI 서버가 실행 중일 때 이 스크립트를 실행하여 비용 추적 API를 테스트합니다.

사용법:
    python3 test_costs_api.py
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1/costs"


def test_total_cost():
    """총 비용 조회 테스트"""
    print("\n=== 1. 총 비용 조회 테스트 ===")

    response = requests.get(f"{BASE_URL}/total")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"총 비용: ${data['total_cost']:.4f}")
        print(f"레코드 개수: {data['record_count']}")
        print(f"제공자별 비용: {json.dumps(data['by_provider'], indent=2)}")
    else:
        print(f"Error: {response.text}")


def test_total_cost_with_filters():
    """필터 적용 총 비용 조회 테스트"""
    print("\n=== 2. 필터 적용 총 비용 조회 테스트 ===")

    # 최근 7일 데이터만 조회
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

    response = requests.get(f"{BASE_URL}/total", params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"최근 7일 총 비용: ${data['total_cost']:.4f}")
        print(f"레코드 개수: {data['record_count']}")
    else:
        print(f"Error: {response.text}")


def test_cost_trend():
    """일별 비용 트렌드 조회 테스트"""
    print("\n=== 3. 일별 비용 트렌드 조회 테스트 ===")

    params = {"days": 7}
    response = requests.get(f"{BASE_URL}/trend", params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"트렌드 데이터 개수: {len(data)}일")

        if data:
            print("\n최근 3일 데이터:")
            for item in data[:3]:
                print(f"  {item['date']}: ${item['total_cost']:.4f}")
    else:
        print(f"Error: {response.text}")


def test_cost_by_provider():
    """제공자별 비용 분석 테스트"""
    print("\n=== 4. 제공자별 비용 분석 테스트 ===")

    params = {"days": 30}
    response = requests.get(f"{BASE_URL}/by-provider", params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"총 비용: ${data['total_cost']:.4f}")
        print(f"조회 기간: {data['period_days']}일")

        if data['providers']:
            print("\n제공자별 비용:")
            for provider in data['providers']:
                print(f"  {provider['provider']}: ${provider['cost']:.4f} ({provider['percentage']:.1f}%)")
    else:
        print(f"Error: {response.text}")


def test_estimate_cost():
    """프로젝트 비용 예상 테스트"""
    print("\n=== 5. 프로젝트 비용 예상 테스트 ===")

    payload = {
        "script_length": 500,
        "video_duration": 60,
        "platform": "YouTube"
    }

    response = requests.post(f"{BASE_URL}/estimate", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n500자 스크립트, 60초 영상 예상 비용:")
        print(f"  Writer Agent (Claude): ${data['writer_agent']:.4f}")
        print(f"  TTS (ElevenLabs): ${data['tts']:.4f}")
        print(f"  STT (Whisper): ${data['stt']:.4f}")
        print(f"  Character (Nano Banana): ${data['character']:.4f}")
        print(f"  Video (Google Veo): ${data['video_generation']:.4f}")
        print(f"  Lipsync (HeyGen): ${data['lipsync']:.4f}")
        print(f"  --------------")
        print(f"  총 예상 비용: ${data['total']:.4f}")
    else:
        print(f"Error: {response.text}")


def test_dashboard():
    """대시보드 데이터 조회 테스트"""
    print("\n=== 6. 대시보드 데이터 조회 테스트 ===")

    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"오늘 비용: ${data['total_cost_today']:.4f}")
        print(f"이번 주 비용: ${data['total_cost_week']:.4f}")
        print(f"이번 달 비용: ${data['total_cost_month']:.4f}")
        print(f"최근 7일 트렌드 데이터: {len(data['daily_trend'])}개")
    else:
        print(f"Error: {response.text}")


def test_export_csv():
    """CSV 내보내기 테스트"""
    print("\n=== 7. CSV 내보내기 테스트 ===")

    response = requests.get(f"{BASE_URL}/export")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"CSV 파일 다운로드 성공")
        print(f"파일 크기: {len(response.content)} bytes")

        # 첫 5줄 출력
        lines = response.text.split('\n')[:5]
        print("\nCSV 미리보기 (첫 5줄):")
        for line in lines:
            print(f"  {line}")
    else:
        print(f"Error: {response.text}")


def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("비용 추적 API 테스트 시작")
    print("=" * 60)

    try:
        # 서버 연결 확인
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("\n⚠️  FastAPI 서버가 실행 중이 아닙니다.")
            print("먼저 'docker-compose up' 또는 'uvicorn app.main:app --reload'를 실행하세요.")
            return
    except requests.exceptions.ConnectionError:
        print("\n⚠️  FastAPI 서버에 연결할 수 없습니다.")
        print("먼저 'docker-compose up' 또는 'uvicorn app.main:app --reload'를 실행하세요.")
        return

    # 모든 테스트 실행
    test_total_cost()
    test_total_cost_with_filters()
    test_cost_trend()
    test_cost_by_provider()
    test_estimate_cost()
    test_dashboard()
    test_export_csv()

    print("\n" + "=" * 60)
    print("모든 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
