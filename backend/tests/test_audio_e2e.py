"""
Phase 0.2: 오디오 생성 엔드투엔드 테스트

3가지 길이의 스크립트로 Zero-Fault Audio 시스템 검증
"""
import time
import requests
import json
from typing import Dict, List
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1/audio"

# 테스트 스크립트 (한국어)
TEST_SCRIPTS = {
    "short_30s": """
안녕하세요, 대표님. OmniVibe Pro의 바이브 코딩 방법론을 소개합니다.
우리는 구글 시트에서 전략을 수립하고, AI 에이전트가 협업하여 영상을 자동으로 생성합니다.
작가, 감독, 마케터 에이전트가 함께 일하며, 유튜브, 인스타그램, 틱톡에 자동으로 배포됩니다.
""",
    "medium_60s": """
안녕하세요, 대표님. OmniVibe Pro는 AI 옴니채널 영상 자동화 SaaS 플랫폼입니다.
먼저 작가 에이전트가 구글 시트에서 전략과 소재를 로드합니다.
그리고 페르소나 기반으로 플랫폼별 스크립트 초안을 생성합니다.
Neo4j GraphRAG와 Pinecone을 활용하여 사용자 취향을 학습합니다.

다음으로 감독 에이전트가 Zero-Fault Audio Loop를 실행합니다.
ElevenLabs TTS로 오디오를 생성하고, OpenAI Whisper STT로 검증합니다.
원본과 대조하여 발음을 보정하며, Google Veo와 Nano Banana로 일관된 캐릭터 영상을 생성합니다.
HeyGen 또는 Wav2Lip으로 립싱크 처리를 완료합니다.
""",
    "long_180s": """
안녕하세요, 대표님. OmniVibe Pro의 전체 워크플로우를 상세히 설명드리겠습니다.

첫 번째 단계는 전략 수립입니다. 구글 시트 API를 통해 콘텐츠 전략과 소재목을 로드합니다.
작가 에이전트가 사용자 페르소나를 분석하고, 유튜브, 인스타그램, 틱톡 각 플랫폼에 최적화된 스크립트를 작성합니다.
이때 Neo4j GraphRAG를 활용하여 장기 메모리를 관리하고, Pinecone 벡터 검색으로 사용자 취향을 학습합니다.

두 번째 단계는 오디오 생성입니다. 감독 에이전트가 Zero-Fault Audio Loop를 시작합니다.
ElevenLabs의 Professional Voice Cloning 기술로 고품질 TTS를 생성합니다.
그리고 OpenAI Whisper v3로 STT 변환을 수행하여 원본 스크립트와 대조합니다.
발음 오류가 발견되면 자동으로 재생성하며, 정확도가 95퍼센트 이상이 될 때까지 반복합니다.
최대 5회까지 재시도하여 완벽한 오디오를 보장합니다.

세 번째 단계는 영상 생성입니다. Google Veo API를 사용하여 시네마틱 품질의 영상을 생성합니다.
Nano Banana로 일관된 캐릭터 레퍼런스 이미지를 만들고, 모든 프레임에서 동일한 캐릭터를 유지합니다.
HeyGen API 또는 Wav2Lip 기술로 립싱크 처리를 수행하여 자연스러운 입 모양을 구현합니다.

네 번째 단계는 최적화와 배포입니다. 마케터 에이전트가 썸네일과 카피 문구를 자동으로 생성합니다.
Cloudinary를 통해 플랫폼별 해상도와 포맷으로 최적화합니다.
스케줄 기반으로 유튜브, 인스타그램, 틱톡에 자동으로 배포합니다.

마지막으로 모니터링입니다. Logfire로 실시간 관측성을 확보하고, API 비용을 추적합니다.
Celery와 Redis로 비디오 렌더링 작업 큐를 관리하며, FastAPI로 안정적인 API 서버를 운영합니다.

이것이 바로 OmniVibe Pro의 바이브 코딩 방법론입니다. 감사합니다.
"""
}

class AudioE2ETest:
    def __init__(self):
        self.results = []

    def test_audio_generation(self, name: str, text: str) -> Dict:
        """단일 오디오 생성 테스트"""
        print(f"\n{'='*80}")
        print(f"테스트: {name}")
        print(f"텍스트 길이: {len(text)} 자")
        print(f"{'='*80}")

        result = {
            "name": name,
            "text_length": len(text),
            "start_time": datetime.now().isoformat(),
            "status": "unknown",
            "task_id": None,
            "attempts": 0,
            "final_similarity": 0.0,
            "elapsed_time_seconds": 0.0,
            "error": None
        }

        start = time.time()

        try:
            # Step 1: 오디오 생성 요청
            print("\n[1/3] 오디오 생성 요청 중...")
            response = requests.post(
                f"{API_BASE}/generate",
                json={
                    "text": text.strip(),
                    "voice_id": "pMsXgVXv3BLzUgSXRplE",  # Rachel voice
                    "language": "ko",
                    "accuracy_threshold": 0.95,
                    "max_attempts": 5
                },
                timeout=10
            )
            response.raise_for_status()

            task_data = response.json()
            task_id = task_data["task_id"]
            result["task_id"] = task_id

            print(f"✓ Task ID: {task_id}")
            print(f"  Status: {task_data['status']}")

            # Step 2: 작업 완료 대기
            print("\n[2/3] 작업 완료 대기 중...")
            max_wait = 300  # 5분
            check_interval = 3
            waited = 0

            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval

                status_response = requests.get(
                    f"{API_BASE}/status/{task_id}",
                    timeout=10
                )
                status_response.raise_for_status()

                status_data = status_response.json()
                task_status = status_data["status"]

                print(f"  [{waited}s] Status: {task_status}", end="")

                if "info" in status_data and isinstance(status_data["info"], dict):
                    current_attempt = status_data["info"].get("current_attempt")
                    if current_attempt:
                        print(f" (Attempt: {current_attempt})", end="")

                print()

                if task_status == "SUCCESS":
                    result["status"] = "success"
                    task_result = status_data.get("result", {})
                    result["attempts"] = task_result.get("attempts", 0)
                    result["final_similarity"] = task_result.get("final_similarity", 0.0)

                    print(f"\n✓ 생성 완료!")
                    print(f"  최종 유사도: {result['final_similarity']:.2%}")
                    print(f"  재시도 횟수: {result['attempts']}")
                    break

                elif task_status == "FAILURE":
                    result["status"] = "failure"
                    result["error"] = status_data.get("error", "Unknown error")
                    print(f"\n✗ 실패: {result['error']}")
                    break

            else:
                result["status"] = "timeout"
                result["error"] = f"Timeout after {max_wait}s"
                print(f"\n✗ 타임아웃 ({max_wait}초 초과)")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"\n✗ 오류 발생: {e}")

        finally:
            result["elapsed_time_seconds"] = time.time() - start
            result["end_time"] = datetime.now().isoformat()

        return result

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*80)
        print("Phase 0.2: 오디오 생성 엔드투엔드 테스트 시작")
        print("="*80)

        for name, text in TEST_SCRIPTS.items():
            result = self.test_audio_generation(name, text)
            self.results.append(result)

            # 각 테스트 사이에 짧은 대기
            if name != list(TEST_SCRIPTS.keys())[-1]:
                print("\n⏳ 다음 테스트 준비 중... (5초 대기)")
                time.sleep(5)

        self.print_summary()
        self.save_report()

    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "="*80)
        print("테스트 결과 요약")
        print("="*80)

        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "success")

        print(f"\n총 테스트: {total}개")
        print(f"성공: {success}개")
        print(f"실패: {total - success}개")
        print(f"성공률: {success / total * 100:.1f}%")

        if success > 0:
            avg_similarity = sum(r["final_similarity"] for r in self.results if r["status"] == "success") / success
            avg_time = sum(r["elapsed_time_seconds"] for r in self.results if r["status"] == "success") / success
            avg_attempts = sum(r["attempts"] for r in self.results if r["status"] == "success") / success

            print(f"\n평균 유사도: {avg_similarity:.2%}")
            print(f"평균 소요 시간: {avg_time:.1f}초")
            print(f"평균 재시도 횟수: {avg_attempts:.1f}회")

        print("\n상세 결과:")
        print("-" * 80)
        for r in self.results:
            print(f"\n{r['name']}:")
            print(f"  텍스트 길이: {r['text_length']}자")
            print(f"  상태: {r['status']}")
            if r['status'] == 'success':
                print(f"  유사도: {r['final_similarity']:.2%}")
                print(f"  재시도: {r['attempts']}회")
                print(f"  소요 시간: {r['elapsed_time_seconds']:.1f}초")
            else:
                print(f"  오류: {r.get('error', 'N/A')}")

        print("\n" + "="*80)

        # 목표 달성 여부
        if success == total:
            print("✓ 모든 테스트 통과!")
        else:
            print(f"✗ {total - success}개 테스트 실패")

        if success > 0:
            if avg_similarity >= 0.95:
                print("✓ 목표 유사도 달성 (95% 이상)")
            else:
                print(f"✗ 목표 유사도 미달성 (현재: {avg_similarity:.2%}, 목표: 95%)")

    def save_report(self):
        """결과를 JSON 파일로 저장"""
        report = {
            "test_date": datetime.now().isoformat(),
            "phase": "0.2",
            "description": "Audio Generation End-to-End Test",
            "total_tests": len(self.results),
            "success_count": sum(1 for r in self.results if r["status"] == "success"),
            "results": self.results
        }

        filename = f"test_report_phase_0.2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/backend/{filename}"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 상세 리포트 저장: {filename}")

if __name__ == "__main__":
    tester = AudioE2ETest()
    tester.run_all_tests()
