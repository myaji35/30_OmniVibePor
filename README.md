# OmniVibe Pro 🎬

**AI 옴니채널 영상 자동화 SaaS** - Vibe Coding 방법론 기반

## 프로젝트 개요

OmniVibe Pro는 구글 시트 기반 전략 수립부터 AI 에이전트 협업, 영상 생성/보정, 다채널 자동 배포까지 전 과정을 자동화하는 플랫폼입니다.

### 핵심 특징

- **🎯 Zero-Fault Audio**: TTS → STT 검증 루프로 발음 오류 제로화
- **🤖 3-Agent System**: Writer, Director, Marketer 에이전트 협업
- **📊 Self-Learning System**: 조회수+좋아요+댓글 분석하여 다음 썸네일에 자동 반영 ⭐
- **🎨 Character Consistency**: 영상 내 캐릭터 일관성 유지
- **🚀 Multi-Channel**: YouTube, Instagram, Facebook 자동 배포
- **📈 TensorFlow Embedding Projector**: 썸네일 임베딩 시각화로 성공 패턴 발견 ⭐

## 빠른 시작

### 1. 사전 요구사항

- Python 3.11+
- Docker & Docker Compose
- Poetry (의존성 관리)

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd 30_OmniVibePro

# 백엔드 디렉토리 이동
cd backend

# Poetry 설치 (없는 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 API 키들을 설정하세요
```

### 3. Docker로 실행

```bash
# Docker Compose로 모든 서비스 시작 (FastAPI + Redis + Neo4j)
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

### 4. 로컬 개발 모드

```bash
# Poetry 가상환경 활성화
poetry shell

# FastAPI 서버 실행
uvicorn app.main:app --reload

# 또는
python -m app.main
```

API 서버: http://localhost:8000
API 문서: http://localhost:8000/docs
Flower (Celery 모니터링): http://localhost:5555
Neo4j 브라우저: http://localhost:7474

## API 사용 예시

### 1. 유튜브 고성과 영상 학습 (타인의 패턴)

```bash
curl -X POST "http://localhost:8000/api/v1/thumbnails/learn" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI 트렌드 2026",
    "min_views": 100000,
    "max_results": 50
  }'
```

### 2. 자신의 컨텐츠 성과 추적 (자가학습) ⭐

```bash
curl -X POST "http://localhost:8000/api/v1/performance/track" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "youtube_channel_id": "UCxxx",
    "facebook_page_id": "123456789",
    "instagram_account_id": "17841401234567890",
    "days_back": 30
  }'
```

**자동 분석 항목**:
- ✅ 조회수 (Views)
- ✅ 좋아요 (Likes)
- ✅ 댓글 (Comments)
- ✅ 인게이지먼트 레이트 계산
- ✅ 성과 점수 (0-100점)
- ✅ Neo4j에 그래프 저장
- ✅ Pinecone에 성공/실패 패턴 저장

### 3. 학습 기반 썸네일 + 카피 생성 ⭐

```bash
curl -X POST "http://localhost:8000/api/v1/performance/generate-learned" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "script": "2026년 AI 트렌드를 알아봅니다...",
    "persona": {
      "gender": "female",
      "style": "professional",
      "tone": "friendly"
    }
  }'
```

**학습 우선순위**:
1. 자신의 고성과 컨텐츠 (70점 이상)
2. 타인의 고성과 컨텐츠 (10만 조회수 이상)
3. 자신의 중성과 컨텐츠 (40-70점)

### 4. TensorFlow Embedding Projector 시각화 ⭐

```bash
# 임베딩 데이터 생성
curl -X POST "http://localhost:8000/api/v1/performance/visualize-embeddings?user_id=user123&max_vectors=1000"

# TensorBoard 실행
cd backend
tensorboard --logdir=./embeddings_viz

# 브라우저에서 http://localhost:6006 접속
# Projector 탭에서 t-SNE/PCA로 시각화
```

**시각화 분석**:
- 🔴 고성과 클러스터 vs 🔵 저성과 클러스터
- ● 자신의 컨텐츠 vs ★ 타인의 컨텐츠
- 플랫폼별 패턴 차이 (YouTube, Facebook, Instagram)

## 프로젝트 구조

```
omnivibe-pro/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph 에이전트
│   │   ├── services/        # 외부 API 연동
│   │   │   ├── youtube_thumbnail_learner.py      ✅ 타인의 고성과 영상 학습
│   │   │   ├── content_performance_tracker.py    ✅ 자신의 성과 추적 & 자가학습
│   │   │   ├── neo4j_client.py                   ✅ GraphRAG 클라이언트
│   │   │   └── embedding_visualizer.py           ✅ TensorBoard Projector 연동
│   │   ├── core/            # 설정, 로깅
│   │   │   └── config.py    ✅
│   │   ├── api/v1/          # FastAPI 라우터
│   │   │   ├── thumbnail_learner.py  ✅
│   │   │   └── performance.py        ✅ 성과 추적 & 시각화 API
│   │   ├── models/          # Pydantic 모델
│   │   ├── tasks/           # Celery 작업
│   │   └── utils/
│   ├── tests/
│   ├── embeddings_viz/      ✅ TensorBoard 시각화 데이터
│   ├── pyproject.toml       ✅
│   ├── Dockerfile           ✅
│   └── docker-compose.yml   ✅
├── frontend/                # Next.js (예정)
├── docs/
├── prd.md                   ✅
├── CLAUDE.md                ✅
├── RALPLAN.md               ✅ Ultra Work 실행 계획
└── README.md                ✅
```

## 개발 로드맵

### ✅ Phase 0: 프로젝트 초기화 (완료)
- [x] 디렉토리 구조 생성
- [x] Poetry 설정 (25+ 패키지)
- [x] Docker Compose 구성 (FastAPI, Redis, Neo4j, Celery, Flower)
- [x] FastAPI 기본 구조
- [x] YouTube 썸네일 학습 모듈 (타인의 고성과 영상)
- [x] 멀티 플랫폼 성과 추적 (YouTube, Facebook, Instagram) ⭐
- [x] 조회수+좋아요+댓글 자가학습 시스템 ⭐
- [x] Neo4j GraphRAG 클라이언트 ⭐
- [x] Pinecone 성과 패턴 저장 ⭐
- [x] TensorFlow Embedding Projector 시각화 ⭐

### 🚧 Phase 1: PoC - Zero-Fault Audio (진행 중)
- [ ] ElevenLabs TTS 서비스
- [ ] Whisper STT 서비스
- [ ] Audio Correction Loop
- [ ] Celery 작업 큐

### 📋 Phase 2: Alpha - LangGraph Agents
- [ ] Writer 에이전트
- [ ] Director 에이전트
- [ ] Marketer 에이전트
- [ ] Neo4j + Pinecone 메모리

### 📋 Phase 3: Beta - Integration
- [ ] Google Sheets 커넥터
- [ ] Google Veo + Nano Banana
- [ ] Cloudinary 최적화
- [ ] HeyGen 립싱크

### 📋 Phase 4: Launch - SaaS Dashboard
- [ ] Next.js 프론트엔드
- [ ] 사용자 인증
- [ ] 다채널 자동 배포

## 기술 스택

**Backend**
- FastAPI (Python 3.11)
- LangGraph (에이전트 오케스트레이션)
- Celery + Redis (작업 큐)
- Logfire (관측성)

**AI Services**
- OpenAI (Whisper, DALL-E, GPT-4)
- ElevenLabs (TTS)
- Google Veo (영상 생성)
- CLIP (이미지 임베딩)

**Data & Memory**
- Neo4j (GraphRAG)
- Pinecone (벡터 검색)
- Google Sheets API

**Media & Distribution**
- Cloudinary (미디어 최적화)
- YouTube Data API
- HeyGen / Wav2Lip (립싱크)

## 테스트

```bash
# 전체 테스트 실행
poetry run pytest

# 커버리지 포함
poetry run pytest --cov=app --cov-report=html

# 특정 테스트
poetry run pytest tests/test_thumbnail_learner.py
```

## 라이선스

MIT License

## 문의

프로젝트 관련 문의: [연락처]

---

**🤖 Generated with Claude Code** - Vibe Coding Methodology
