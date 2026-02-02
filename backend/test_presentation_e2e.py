#!/usr/bin/env python3
"""
프리젠테이션 API 엔드투엔드 테스트

전체 워크플로우:
1. PDF 업로드
2. 스크립트 생성
3. 오디오 생성
4. 타이밍 분석
5. 영상 생성
6. 상태 조회
"""

import asyncio
import httpx
import time
from pathlib import Path
import sys

# API 엔드포인트
BASE_URL = "http://localhost:8000/api/v1"
PRESENTATIONS_URL = f"{BASE_URL}/presentations"


async def test_presentation_workflow():
    """전체 프리젠테이션 워크플로우 테스트"""

    print("=" * 60)
    print("프리젠테이션 API 엔드투엔드 테스트")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=300.0) as client:

        # 1. PDF 업로드
        print("\n[1/6] PDF 업로드...")

        # 테스트 PDF 파일 경로 (실제 파일로 교체 필요)
        pdf_path = Path("./test_presentation.pdf")

        if not pdf_path.exists():
            print(f"⚠️  테스트 PDF 파일이 없습니다: {pdf_path}")
            print("   실제 PDF 파일을 준비하거나 경로를 수정하세요.")
            return

        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            data = {
                "project_id": "test_project_001",
                "dpi": 200,
                "lang": "kor+eng"
            }

            response = await client.post(
                f"{PRESENTATIONS_URL}/upload",
                files=files,
                data=data
            )

        if response.status_code != 200:
            print(f"❌ PDF 업로드 실패: {response.status_code}")
            print(response.text)
            return

        upload_result = response.json()
        presentation_id = upload_result["presentation_id"]
        total_slides = upload_result["total_slides"]

        print(f"✅ PDF 업로드 완료")
        print(f"   - Presentation ID: {presentation_id}")
        print(f"   - 총 슬라이드: {total_slides}개")

        # 2. 스크립트 생성
        print("\n[2/6] 나레이션 스크립트 생성...")

        script_request = {
            "tone": "professional",
            "target_duration_per_slide": 15.0,
            "include_slide_numbers": False
        }

        response = await client.post(
            f"{PRESENTATIONS_URL}/{presentation_id}/generate-script",
            json=script_request
        )

        if response.status_code != 200:
            print(f"❌ 스크립트 생성 실패: {response.status_code}")
            print(response.text)
            return

        script_result = response.json()
        estimated_duration = script_result["estimated_total_duration"]

        print(f"✅ 스크립트 생성 완료")
        print(f"   - 예상 총 시간: {estimated_duration:.1f}초")
        print(f"   - 전체 스크립트 길이: {len(script_result['full_script'])}자")

        # 3. 오디오 생성
        print("\n[3/6] TTS 오디오 생성...")

        audio_request = {
            "voice_id": "alloy",
            "model": "tts-1"
        }

        response = await client.post(
            f"{PRESENTATIONS_URL}/{presentation_id}/generate-audio",
            json=audio_request
        )

        if response.status_code != 200:
            print(f"❌ 오디오 생성 실패: {response.status_code}")
            print(response.text)
            return

        audio_result = response.json()
        audio_duration = audio_result["duration"]
        accuracy = audio_result["accuracy"]

        print(f"✅ 오디오 생성 완료")
        print(f"   - 오디오 길이: {audio_duration:.1f}초")
        print(f"   - STT 정확도: {accuracy:.2%}")
        print(f"   - 오디오 경로: {audio_result['audio_path']}")

        # 4. 타이밍 분석
        print("\n[4/6] 슬라이드 타이밍 분석...")

        timing_request = {}

        response = await client.post(
            f"{PRESENTATIONS_URL}/{presentation_id}/analyze-timing",
            json=timing_request
        )

        if response.status_code != 200:
            print(f"❌ 타이밍 분석 실패: {response.status_code}")
            print(response.text)
            return

        timing_result = response.json()
        total_duration = timing_result["total_duration"]

        print(f"✅ 타이밍 분석 완료")
        print(f"   - 총 영상 길이: {total_duration:.1f}초")

        # 슬라이드별 타이밍 출력
        for slide in timing_result["slides"][:3]:  # 처음 3개만
            print(f"   - 슬라이드 {slide['slide_number']}: "
                  f"{slide['start_time']:.1f}s ~ {slide['end_time']:.1f}s "
                  f"({slide['duration']:.1f}s)")

        if len(timing_result["slides"]) > 3:
            print(f"   - ... (총 {len(timing_result['slides'])}개)")

        # 5. 영상 생성 (비동기)
        print("\n[5/6] 프리젠테이션 영상 생성 시작...")

        video_request = {
            "transition_effect": "fade",
            "transition_duration": 0.5,
            "bgm_path": None,
            "bgm_volume": 0.3
        }

        response = await client.post(
            f"{PRESENTATIONS_URL}/{presentation_id}/generate-video",
            json=video_request
        )

        if response.status_code != 200:
            print(f"❌ 영상 생성 요청 실패: {response.status_code}")
            print(response.text)
            return

        video_result = response.json()
        task_id = video_result["celery_task_id"]
        estimated_time = video_result.get("estimated_completion_time", 60)

        print(f"✅ 영상 생성 작업 시작")
        print(f"   - Celery Task ID: {task_id}")
        print(f"   - 예상 완료 시간: {estimated_time}초")

        # 6. 상태 조회 (폴링)
        print("\n[6/6] 영상 생성 상태 확인 중...")

        max_wait = 300  # 최대 5분 대기
        poll_interval = 5  # 5초마다 확인
        elapsed = 0

        while elapsed < max_wait:
            response = await client.get(f"{PRESENTATIONS_URL}/{presentation_id}")

            if response.status_code != 200:
                print(f"❌ 상태 조회 실패: {response.status_code}")
                return

            detail = response.json()
            status = detail["status"]

            if status == "video_ready":
                print(f"\n✅ 영상 생성 완료!")
                print(f"   - 영상 경로: {detail['video_path']}")
                print(f"   - 총 소요 시간: {elapsed}초")
                break
            elif status == "failed":
                print(f"\n❌ 영상 생성 실패")
                print(f"   - 에러: {detail.get('metadata', {}).get('error', 'Unknown')}")
                return
            else:
                print(f"   [{elapsed}s] 상태: {status} (대기 중...)")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        if elapsed >= max_wait:
            print(f"\n⚠️  타임아웃: {max_wait}초 경과")
            print("   영상 생성이 아직 진행 중일 수 있습니다.")
            print(f"   직접 확인: GET {PRESENTATIONS_URL}/{presentation_id}")

        # 최종 상세 정보
        print("\n" + "=" * 60)
        print("최종 프리젠테이션 정보")
        print("=" * 60)

        response = await client.get(f"{PRESENTATIONS_URL}/{presentation_id}")
        if response.status_code == 200:
            detail = response.json()
            print(f"Presentation ID: {detail['presentation_id']}")
            print(f"프로젝트 ID: {detail['project_id']}")
            print(f"총 슬라이드: {detail['total_slides']}개")
            print(f"상태: {detail['status']}")
            print(f"PDF 경로: {detail['pdf_path']}")
            if detail.get('audio_path'):
                print(f"오디오 경로: {detail['audio_path']}")
            if detail.get('video_path'):
                print(f"영상 경로: {detail['video_path']}")
            print(f"생성 시각: {detail['created_at']}")
            print(f"업데이트 시각: {detail['updated_at']}")


async def test_list_presentations():
    """프리젠테이션 목록 조회 테스트"""

    print("\n" + "=" * 60)
    print("프리젠테이션 목록 조회 테스트")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        project_id = "test_project_001"

        response = await client.get(
            f"{PRESENTATIONS_URL}/projects/{project_id}/presentations",
            params={"page": 1, "page_size": 10}
        )

        if response.status_code != 200:
            print(f"❌ 목록 조회 실패: {response.status_code}")
            print(response.text)
            return

        result = response.json()

        print(f"\n총 {result['total']}개 프리젠테이션 (페이지 {result['page']}/{result['page_size']})")

        for p in result["presentations"]:
            print(f"\n- {p['presentation_id']}")
            print(f"  슬라이드: {p['total_slides']}개")
            print(f"  상태: {p['status']}")
            print(f"  생성: {p['created_at']}")


def print_usage():
    """사용법 출력"""
    print("""
사용법:
    python test_presentation_e2e.py [workflow|list]

명령어:
    workflow  - 전체 워크플로우 테스트 (기본값)
    list      - 프리젠테이션 목록 조회 테스트

예시:
    python test_presentation_e2e.py
    python test_presentation_e2e.py workflow
    python test_presentation_e2e.py list

참고:
    - FastAPI 서버가 실행 중이어야 합니다 (http://localhost:8000)
    - test_presentation.pdf 파일이 필요합니다
    - Celery worker가 실행 중이어야 영상 생성이 완료됩니다
    """)


async def main():
    """메인 함수"""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            await test_list_presentations()
        elif command == "workflow":
            await test_presentation_workflow()
        elif command in ["-h", "--help", "help"]:
            print_usage()
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print_usage()
    else:
        # 기본값: 전체 워크플로우
        await test_presentation_workflow()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
