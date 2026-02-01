# OmniVibe Pro - 템플릿 기반 콘텐츠 팩토리

> **비즈니스 모델**: "영상 제작 패턴 확정 → 클라이언트 전달 → 자동 콘텐츠 생성"
> **핵심 가치**: 한 번 설정하면 무한히 콘텐츠가 생성되는 턴키 솔루션

---

## 📋 비즈니스 모델 개요

### 기존 영상 제작 SaaS의 문제점

```
기존 모델 (Canva, CapCut 등):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용자가 영상 하나 만들 때마다:
1. 템플릿 선택
2. 텍스트 입력
3. 이미지/영상 업로드
4. 편집 조정
5. 내보내기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과: 영상 1개 생성 시간 = 30분~1시간
```

### OmniVibe Pro의 혁신

```
턴키 콘텐츠 팩토리:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1단계: 클라이언트 온보딩 (1회, 2시간)
   - 브랜드 가이드 설정
   - 음성 클론 (대표 또는 성우)
   - 영상 스타일 확정
   - 플랫폼 선택

2단계: 템플릿 생성 (1회, 1시간)
   - Neo4j에 저장된 고성과 패턴 분석
   - 클라이언트 맞춤 템플릿 자동 생성
   - 10개 샘플 영상 생성 및 승인

3단계: 클라이언트에 전달
   - 옵션 A: On-Premise 설치 (Docker Image)
   - 옵션 B: SaaS 계정 생성 (독립 워크스페이스)
   - 옵션 C: API 키 발급 (외부 시스템 연동)

4단계: 자동 콘텐츠 생성 (무한 반복)
   - 주제만 입력 → 1분 내 완성
   - 또는 RSS 피드 자동 수집 → 매일 영상 생성
   - 또는 구글 시트 연동 → 스케줄대로 자동 배포
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과: 영상 1개 생성 시간 = 1분 (자동)
      한 달 콘텐츠 = 30개 (자동)
```

---

## 🏗️ 시스템 아키텍처

### 1. 템플릿 시스템 설계

#### **템플릿 정의 (Neo4j)**

```cypher
// 노드: ContentTemplate
(:ContentTemplate {
  template_id: "template_news_recap_60s",
  name: "60초 뉴스 요약",
  client_id: "client_sbs",

  // 영상 스타일
  video_style: {
    aspect_ratio: "9:16",
    duration: 60,
    platform: "instagram",

    // 콘티 구조
    sections: [
      {type: "hook", duration: 5, prompt: "Breaking news visual"},
      {type: "body", duration: 50, prompt: "News anchor in studio"},
      {type: "cta", duration: 5, prompt: "Follow us CTA"}
    ],

    // 비주얼 스타일
    character: "professional_female_anchor",
    background: "modern_news_studio",
    camera_angle: "medium_shot",
    transition: "fade"
  },

  // 오디오 스타일
  audio_style: {
    voice_id: "voice_clone_sbs_anchor",
    speed: 1.0,
    bgm: "news_background_subtle",
    bgm_volume: 0.15
  },

  // 자막 스타일
  subtitle_style: {
    position: "bottom",
    font_family: "Pretendard",
    font_size: 48,
    color: "#FFFFFF",
    background: "rgba(0,0,0,0.7)",
    animation: "fade_in"
  },

  // 스크립트 구조
  script_template: {
    hook: "{{news_headline}}에 대해 알아보겠습니다.",
    body: "{{detailed_explanation}}",
    cta: "더 많은 뉴스는 팔로우하세요!"
  },

  // 성과 기록
  performance: {
    avg_views: 15000,
    avg_engagement: 0.08,
    success_rate: 0.92
  },

  created_at: "2025-02-01T10:00:00Z",
  last_used: "2025-02-01T15:30:00Z",
  usage_count: 127
})

// 관계
(:Client)-[:HAS_TEMPLATE]->(:ContentTemplate)
(:ContentTemplate)-[:BASED_ON]->(:Video {performance_score: 85})
```

---

### 2. 템플릿 기반 콘텐츠 생성 워크플로우

```python
# backend/app/services/template_engine.py

class TemplateEngine:
    """
    템플릿 기반 자동 콘텐츠 생성 엔진
    """

    async def generate_from_template(
        self,
        template_id: str,
        variables: Dict[str, str],
        auto_publish: bool = False
    ) -> Dict:
        """
        템플릿으로 콘텐츠 자동 생성

        Args:
            template_id: 템플릿 ID
            variables: 변수 값 (예: {"news_headline": "..."})
            auto_publish: 자동 배포 여부

        Returns:
            생성된 콘텐츠 정보

        Example:
            >>> engine = TemplateEngine()
            >>> result = await engine.generate_from_template(
            ...     template_id="template_news_recap_60s",
            ...     variables={
            ...         "news_headline": "AI가 인간 작곡가를 넘어서다",
            ...         "detailed_explanation": "OpenAI의 Sora 2.0이..."
            ...     },
            ...     auto_publish=True
            ... )
            >>> print(result['video_url'])
            'https://cdn.omnivibe.com/client_sbs/video_20250201_001.mp4'
        """
        # 1. 템플릿 로드
        template = await self.neo4j.get_template(template_id)

        # 2. 스크립트 생성 (변수 치환)
        script = self._render_script(template.script_template, variables)

        # 3. Writer Agent (템플릿 기반 최적화)
        optimized_script = await self.writer.optimize_with_template(
            script=script,
            template=template
        )

        # 4. Director Agent (템플릿 스타일 적용)
        audio = await self.tts.generate_audio(
            text=optimized_script,
            voice_id=template.audio_style['voice_id'],
            speed=template.audio_style['speed']
        )

        video = await self.veo.generate_video(
            audio=audio,
            style=template.video_style,
            sections=template.video_style['sections']
        )

        # 5. Marketer Agent (자막, 썸네일)
        final_video = await self.marketer.finalize_video(
            video=video,
            subtitle_style=template.subtitle_style,
            auto_thumbnail=True
        )

        # 6. 자동 배포 (옵션)
        if auto_publish:
            await self.deploy(
                video=final_video,
                platform=template.video_style['platform'],
                schedule=None  # 즉시 배포
            )

        # 7. 성과 추적 준비
        await self.neo4j.create_content_from_template(
            template_id=template_id,
            content_id=final_video['content_id'],
            variables=variables
        )

        return {
            "status": "success",
            "content_id": final_video['content_id'],
            "video_url": final_video['url'],
            "estimated_performance": template.performance,
            "auto_published": auto_publish
        }
```

---

### 3. 클라이언트 온보딩 프로세스

```python
# backend/app/services/client_onboarding.py

class ClientOnboardingService:
    """
    클라이언트 온보딩 및 템플릿 생성
    """

    async def onboard_client(
        self,
        client_name: str,
        brand_guide: Dict,
        voice_sample_path: str,
        sample_videos: List[str]  # 기존 영상 URL (분석용)
    ) -> Dict:
        """
        클라이언트 온보딩 자동화

        Args:
            client_name: 클라이언트 이름
            brand_guide: 브랜드 가이드 (로고, 색상, 폰트 등)
            voice_sample_path: 음성 샘플 (3-5분)
            sample_videos: 기존 영상 URL (스타일 분석용)

        Returns:
            {
                "client_id": "client_sbs",
                "voice_id": "voice_clone_sbs_anchor",
                "templates": ["template_news_recap_60s", ...],
                "workspace_url": "https://app.omnivibe.com/sbs"
            }
        """
        # 1. 클라이언트 생성
        client = await self.neo4j.create_client({
            "client_id": f"client_{client_name.lower()}",
            "name": client_name,
            "brand_guide": brand_guide,
            "onboarded_at": datetime.now()
        })

        # 2. 음성 클론
        voice_id = await self.elevenlabs.clone_voice(
            name=f"{client_name} Voice",
            audio_path=voice_sample_path
        )

        await self.neo4j.create_custom_voice(
            client_id=client['client_id'],
            voice_id=voice_id,
            name=f"{client_name} Default Voice"
        )

        # 3. 기존 영상 분석 (스타일 추출)
        styles = []
        for video_url in sample_videos:
            style = await self._analyze_video_style(video_url)
            styles.append(style)

        # 4. 템플릿 자동 생성
        templates = await self._generate_templates_from_styles(
            client_id=client['client_id'],
            styles=styles,
            voice_id=voice_id
        )

        # 5. 샘플 영상 10개 생성 (승인용)
        samples = []
        for template in templates[:3]:  # 상위 3개 템플릿
            for i in range(3):
                sample = await self.template_engine.generate_from_template(
                    template_id=template['template_id'],
                    variables=self._get_sample_variables(i),
                    auto_publish=False
                )
                samples.append(sample)

        # 6. 워크스페이스 생성
        workspace = await self._create_workspace(
            client_id=client['client_id'],
            templates=templates
        )

        return {
            "client_id": client['client_id'],
            "voice_id": voice_id,
            "templates": [t['template_id'] for t in templates],
            "sample_videos": samples,
            "workspace_url": workspace['url'],
            "api_key": workspace['api_key']
        }
```

---

## 🚀 클라이언트 전달 옵션

### 옵션 A: On-Premise 설치 (Enterprise)

```bash
# Docker Image 제공
docker pull omnivibepro/client-workspace:latest

# 클라이언트 전용 환경 변수
export CLIENT_ID=client_sbs
export TEMPLATE_IDS=template_news_recap_60s,template_interview_90s
export VOICE_ID=voice_clone_sbs_anchor
export API_KEY=sk-sbs-xxxxxxxxxxxxx

# 실행
docker run -d \
  -p 8000:8000 \
  -e CLIENT_ID=$CLIENT_ID \
  -e TEMPLATE_IDS=$TEMPLATE_IDS \
  -e VOICE_ID=$VOICE_ID \
  -e API_KEY=$API_KEY \
  omnivibepro/client-workspace:latest
```

**장점**:
- 클라이언트 인프라에서 실행 (데이터 보안)
- 무제한 사용 (라이선스 기반)
- 커스터마이징 가능

**가격**: $50,000 + $10,000/년 유지보수

---

### 옵션 B: SaaS 계정 (Professional)

```
클라이언트 전용 워크스페이스:
https://app.omnivibe.com/sbs

기능:
- 템플릿 기반 콘텐츠 생성 (무제한)
- 구글 시트 연동 (자동 스케줄링)
- RSS 피드 수집 (자동 영상화)
- 성과 대시보드
- 팀 협업 (최대 10명)
```

**가격**: $499/월 (100개 영상/월 포함, 추가 $3/영상)

---

### 옵션 C: API 키 발급 (Developer)

```python
# 클라이언트 시스템에서 호출
import requests

API_KEY = "sk-sbs-xxxxxxxxxxxxx"

response = requests.post(
    "https://api.omnivibe.com/v1/generate",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "template_id": "template_news_recap_60s",
        "variables": {
            "news_headline": "AI가 인간 작곡가를 넘어서다",
            "detailed_explanation": "OpenAI의 Sora 2.0이..."
        },
        "auto_publish": True,
        "webhook_url": "https://sbs.com/api/video-ready"
    }
)

video_url = response.json()['video_url']
```

**가격**: $0.10/API 호출 (영상 1개 = 1 호출)

---

## 💰 수익 모델

### 1. 초기 온보딩 비용

| 서비스 | 가격 | 포함 사항 |
|--------|------|----------|
| **기본 온보딩** | $5,000 | 음성 클론 1개, 템플릿 3개, 샘플 영상 10개 |
| **프리미엄 온보딩** | $15,000 | 음성 클론 3개, 템플릿 10개, 샘플 영상 30개, 커스텀 캐릭터 |
| **엔터프라이즈 온보딩** | $50,000+ | 무제한 커스터마이징, 전담 PM, On-Premise 설치 |

### 2. 월간 구독 (SaaS)

| 플랜 | 가격 | 영상 개수 | 추가 기능 |
|------|------|-----------|-----------|
| **Starter** | $99/월 | 10개/월 | 템플릿 3개, 기본 음성 |
| **Professional** | $499/월 | 100개/월 | 템플릿 무제한, 음성 클론 3개, 구글 시트 연동 |
| **Enterprise** | $2,999/월 | 1,000개/월 | 전용 워크스페이스, API 액세스, 팀 협업 |

### 3. API 종량제

- **기본**: $0.10/영상
- **대량** (1,000+/월): $0.05/영상
- **엔터프라이즈** (10,000+/월): 협의

---

## 📊 수익 시뮬레이션

### 시나리오 1: 뉴스 미디어 (SBS 예시)

```
클라이언트: SBS 뉴스
플랜: Enterprise ($2,999/월)
사용량: 매일 5개 영상 = 150개/월

비용:
- 초기 온보딩: $15,000 (1회)
- 월간 구독: $2,999
- 추가 영상 (50개): $2,500

매출:
- 1년 차: $15,000 + ($2,999 × 12) = $50,988
- 2년 차 이후: $35,988/년

클라이언트 절감 비용:
- 기존: 영상 1개 = 외주 $500 × 150 = $75,000/월
- OmniVibe: $5,499/월
- 절감: $69,501/월 (93% 절감!)
```

### 시나리오 2: 교육 기관 (10개 계정)

```
클라이언트: 대학교 (10개 학과)
플랜: Professional × 10 = $4,990/월
사용량: 학과당 50개/월 = 총 500개/월

매출:
- 1년 차: ($5,000 × 10) + ($4,990 × 12) = $109,880
- 2년 차 이후: $59,880/년
```

---

## 🔄 자동 콘텐츠 생성 파이프라인

### 1. RSS 피드 자동 수집

```python
# backend/app/services/rss_pipeline.py

class RSSContentPipeline:
    """
    RSS 피드 → 자동 영상 생성 파이프라인
    """

    async def monitor_rss_feeds(self, client_id: str):
        """
        RSS 피드 모니터링 및 자동 영상 생성

        Example:
            클라이언트: TechCrunch Korea
            RSS: https://techcrunch.com/feed/

            새 기사 발견 → 1분 내 요약 영상 생성 → 인스타 자동 배포
        """
        client = await self.neo4j.get_client(client_id)
        feeds = client['rss_feeds']  # ["https://techcrunch.com/feed/", ...]

        for feed_url in feeds:
            # 1. RSS 파싱
            new_articles = await self._fetch_new_articles(feed_url)

            for article in new_articles:
                # 2. 템플릿 선택 (기사 카테고리 기반)
                template = await self._select_template_for_article(
                    client_id=client_id,
                    category=article['category']
                )

                # 3. 변수 추출
                variables = {
                    "headline": article['title'],
                    "summary": article['summary'][:200],
                    "source": article['source']
                }

                # 4. 영상 생성
                video = await self.template_engine.generate_from_template(
                    template_id=template['template_id'],
                    variables=variables,
                    auto_publish=True  # 즉시 배포
                )

                # 5. 성과 추적
                await self.neo4j.link_article_to_video(
                    article_url=article['url'],
                    video_id=video['content_id']
                )
```

### 2. 구글 시트 스케줄링

```python
# backend/app/services/sheets_scheduler.py

class SheetsScheduler:
    """
    구글 시트 → 스케줄 기반 자동 배포
    """

    async def sync_google_sheets(self, client_id: str):
        """
        구글 시트의 콘텐츠 캘린더를 읽어 자동 영상 생성

        Google Sheet 예시:
        | 날짜 | 템플릿 | 주제 | 세부 내용 | 배포 시간 |
        |------|--------|------|----------|----------|
        | 2025-02-01 | template_news_recap_60s | AI 뉴스 | GPT-5 발표... | 09:00 |
        | 2025-02-01 | template_interview_90s | CEO 인터뷰 | 삼성 이재용... | 18:00 |
        """
        client = await self.neo4j.get_client(client_id)
        sheet_url = client['google_sheet_url']

        # 1. 구글 시트 읽기
        rows = await self.google_sheets.read_rows(sheet_url)

        for row in rows:
            scheduled_time = row['배포 시간']

            # 2. 스케줄 확인
            if self._should_generate_now(scheduled_time):
                # 3. 영상 생성
                video = await self.template_engine.generate_from_template(
                    template_id=row['템플릿'],
                    variables={
                        "topic": row['주제'],
                        "details": row['세부 내용']
                    },
                    auto_publish=False  # 스케줄 시간까지 대기
                )

                # 4. 예약 배포
                await self.scheduler.schedule_publish(
                    video_id=video['content_id'],
                    publish_at=scheduled_time
                )
```

---

## 🎯 클라이언트 성공 사례 시나리오

### 사례 1: SBS 뉴스

**Before OmniVibe**:
- 영상 1개 제작 시간: 2시간 (촬영 + 편집)
- 일일 영상: 5개 = 10시간 작업
- 인력: 촬영팀 3명 + 편집팀 2명 = 5명
- 월간 인건비: $30,000

**After OmniVibe**:
- 영상 1개 제작 시간: 1분 (자동)
- 일일 영상: 5개 = 5분 작업
- 인력: 콘텐츠 기획자 1명 (주제 입력만)
- 월간 비용: $5,499 (구독료 + 초과분)
- **절감**: $24,501/월 (82%)

---

### 사례 2: 교육 스타트업 (에듀테크)

**Before OmniVibe**:
- 강의 영상 1개: 외주 $500
- 월간 50개 = $25,000

**After OmniVibe**:
- 템플릿: "강의 요약 60초", "강사 인터뷰 90초"
- 월간 50개 = $499 (Professional 플랜)
- **절감**: $24,501/월 (98%)

---

## 🔮 향후 확장 계획

### 1. AI Copilot 기능
```
사용자: "오늘 뉴스 5개 요약해서 영상 만들어줘"
AI: "네, TechCrunch에서 상위 5개 기사를 분석했습니다.
     1. GPT-5 발표 (조회수 예상: 15,000)
     2. 테슬라 신차 (조회수 예상: 12,000)
     ...

     총 5개 영상을 생성했습니다. 지금 배포할까요?"
```

### 2. 다국어 자동 번역
```
템플릿 1개 → 10개 언어 자동 변환
- 한국어 원본
- 영어, 일본어, 중국어, 스페인어... 자동 생성
- 음성도 각 언어의 AI 음성으로 자동 변환
```

### 3. A/B 테스트 자동화
```
템플릿 A vs 템플릿 B
→ 각 100회 배포
→ 성과 분석
→ 승자 템플릿 자동 선택
→ 계속 최적화
```

---

## 📝 다음 액션

대표님, 이 "턴키 콘텐츠 팩토리" 모델을 구현하기 위해:

### 즉시 시작
1. **TemplateEngine 클래스 구현** (backend/app/services/template_engine.py)
2. **ContentTemplate 노드 스키마 추가** (Neo4j)
3. **ClientOnboardingService 구현**

### 단기 (1-2주)
4. **템플릿 UI** (frontend/app/templates)
5. **RSS 파이프라인 구현**
6. **구글 시트 스케줄러 구현**

### 중기 (1개월)
7. **On-Premise Docker Image 패키징**
8. **API 키 시스템 구현**
9. **클라이언트 대시보드**

어떤 부분부터 시작하시겠습니까?
