"""
Locust 성능 테스트

동시 사용자 시뮬레이션 및 부하 테스트
"""
from locust import HttpUser, task, between, events
import json
import random


class OmniVibeUser(HttpUser):
    """
    일반 사용자 시나리오
    """
    wait_time = between(1, 3)  # 요청 간 1-3초 대기

    def on_start(self):
        """테스트 시작 시 1회 실행 (로그인)"""
        # 회원가입
        response = self.client.post("/api/v1/auth/register", json={
            "email": f"test_{random.randint(1, 10000)}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test User {random.randint(1, 1000)}"
        })

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
        else:
            # 로그인 재시도
            response = self.client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "TestPass123!"
            })
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")

    @task(5)
    def list_campaigns(self):
        """캠페인 목록 조회 (가장 빈번한 작업)"""
        self.client.get("/api/v1/campaigns", headers={
            "Authorization": f"Bearer {self.access_token}"
        })

    @task(3)
    def generate_script(self):
        """스크립트 생성 (AI 호출, 느림)"""
        self.client.post("/api/v1/writer/generate", json={
            "spreadsheet_id": "test_spreadsheet",
            "campaign_name": f"Campaign {random.randint(1, 100)}",
            "topic": "AI 비디오 자동화",
            "platform": random.choice(["YouTube", "Instagram", "TikTok"]),
            "target_duration": random.randint(60, 180)
        }, headers={
            "Authorization": f"Bearer {self.access_token}"
        })

    @task(2)
    def create_campaign(self):
        """캠페인 생성"""
        self.client.post("/api/v1/campaigns", json={
            "name": f"Test Campaign {random.randint(1, 1000)}",
            "client_id": 1,
            "concept_gender": random.choice(["male", "female", "neutral"]),
            "concept_tone": random.choice(["professional", "casual", "friendly"]),
            "concept_style": random.choice(["cinematic", "minimal", "dynamic"]),
            "platform": random.choice(["YouTube", "Instagram", "TikTok"])
        }, headers={
            "Authorization": f"Bearer {self.access_token}"
        })

    @task(1)
    def get_pricing_plans(self):
        """가격 플랜 조회"""
        self.client.get("/api/v1/billing/plans")


class PowerUser(HttpUser):
    """
    고급 사용자 시나리오 (오디오 생성 포함)
    """
    wait_time = between(2, 5)

    def on_start(self):
        """로그인"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "poweruser@example.com",
            "password": "PowerPass123!"
        })
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")

    @task(3)
    def generate_audio(self):
        """오디오 생성 (비동기)"""
        self.client.post("/api/v1/audio/generate", json={
            "content_id": random.randint(1, 100),
            "text": "안녕하세요, 테스트 오디오입니다.",
            "voice_id": "default",
            "language": "ko"
        }, headers={
            "Authorization": f"Bearer {self.access_token}"
        })

    @task(2)
    def check_audio_status(self):
        """오디오 상태 조회"""
        task_id = f"task_{random.randint(1, 100)}"
        self.client.get(f"/api/v1/audio/status/{task_id}", headers={
            "Authorization": f"Bearer {self.access_token}"
        })

    @task(1)
    def list_campaigns(self):
        """캠페인 목록 조회"""
        self.client.get("/api/v1/campaigns", headers={
            "Authorization": f"Bearer {self.access_token}"
        })


# 성능 메트릭 기록
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    모든 요청에 대해 메트릭 기록
    """
    if exception:
        print(f"❌ {name} failed: {exception}")
    elif response_time > 500:  # 500ms 초과 시 경고
        print(f"⚠️  {name} slow response: {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 시"""
    print("🚀 OmniVibe Pro Performance Test Started")
    print(f"   Target Host: {environment.host}")
    print(f"   Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 시"""
    print("\n📊 Performance Test Summary:")
    print(f"   Total Requests: {environment.stats.total.num_requests}")
    print(f"   Total Failures: {environment.stats.total.num_failures}")
    print(f"   Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"   RPS: {environment.stats.total.current_rps:.2f}")
