# OmniVibe Pro - REALPLAN (실제 구현 계획)

> **작성일**: 2025-02-01
> **목표**: "90% AI 자동 생성 + 10% 사용자 미세 조정" 컨셉의 AI 옴니채널 영상 자동화 SaaS
> **핵심 철학**: 바이브 코딩 방법론 - 사용자는 최소 개입, AI가 최대 자동화

---

## 📋 목차

1. [프로젝트 현황](#1-프로젝트-현황)
2. [핵심 기능 정의](#2-핵심-기능-정의)
3. [기술 스택 확정](#3-기술-스택-확정)
4. [Phase별 구현 계획](#4-phase별-구현-계획)
5. [우선순위 매트릭스](#5-우선순위-매트릭스)
6. [리스크 관리](#6-리스크-관리)
7. [성공 지표](#7-성공-지표)

---

## 1. 프로젝트 현황

### ✅ 완료된 것

#### **Backend (FastAPI)**
- [x] 기본 프로젝트 구조
- [x] Zero-Fault Audio Loop (TTS → STT → 검증)
  - ElevenLabs TTS 통합
  - OpenAI Whisper STT 통합
  - 유사도 계산 및 재생성 로직
- [x] Text Normalizer (한국어 숫자 → 한글 변환)
  - 마크다운 헤더 제거 (`### 훅`, `### 본문`)
  - 메타데이터 제거 (`--- 예상 영상 길이: 2분 30초`)
- [x] Celery + Redis 작업 큐
- [x] Neo4j 연동 준비
- [x] Voice Cloning 서비스 (ElevenLabs)
- [x] Docker Compose 환경

#### **Frontend (Next.js)**
- [x] 기본 프로젝트 구조
- [x] Audio 생성 페이지 (`/audio`)
- [x] AudioProgressTracker 컴포넌트
- [x] HTML5 Audio 플레이어

#### **문서화**
- [x] `UX_IMPROVEMENT_PROPOSAL.md` - UI/UX 개선안
- [x] `DOCKER_TROUBLESHOOTING.md` - Docker 운영 가이드
- [x] PDF 프리젠테이션 스타일 구현 방안
- [x] 영상 분량 제어 시스템 설계

### ❌ 아직 안 된 것

#### **Backend**
- [ ] 프로젝트 기반 API 구조 (`/api/v1/projects`)
- [ ] Writer Agent 구현
- [ ] Director Agent 구현 (영상 생성)
- [ ] Continuity Agent 구현
- [ ] Google Sheets 연동
- [ ] Google Veo 통합
- [ ] HeyGen/Wav2Lip 립싱크
- [ ] Cloudinary 미디어 최적화
- [ ] WebSocket 실시간 진행 상태

#### **Frontend**
- [ ] `/production` 통합 대시보드
- [ ] ProductionContext 상태 관리
- [ ] WriterPanel
- [ ] DirectorPanel
- [ ] VideoEditorPanel (타임라인)
- [ ] PresentationMode

#### **인프라**
- [ ] 프로덕션 배포 환경
- [ ] CI/CD 파이프라인
- [ ] 모니터링 (Logfire 완전 연동)

---

## 2. 핵심 기능 정의

### 🎯 MVP (Minimum Viable Product) - 출시 필수 기능

#### **Feature 1: 스크립트 기반 오디오 생성** ✅ (90% 완료)
**현황**: 이미 구현됨, UI 개선 필요
- [x] 텍스트 입력
- [x] Zero-Fault Audio Loop
- [x] 음성 선택 (기본 음성 + 클론 음성)
- [ ] 통합 UI로 이동 필요

#### **Feature 2: 프로젝트 기반 워크플로우** ⚠️ (0% - 최우선)
**목표**: 스크립트 → 오디오 → 영상을 하나의 프로젝트로 관리
- [ ] 프로젝트 생성/저장/불러오기
- [ ] Writer → Director → Marketer 단계별 진행
- [ ] 자동 컨텍스트 전달 (복사/붙여넣기 제거)
- [ ] Neo4j에 프로젝트 상태 저장

**우선순위**: 🔴 최우선 (전체 UX의 기반)

#### **Feature 3: 통합 프로덕션 대시보드** ⚠️ (0% - 최우선)
**목표**: `/production` 단일 페이지에서 모든 작업 수행
- [ ] 4단계 진행 상태 (Writer → Director → Marketer → Deployment)
- [ ] 단계별 패널 자동 전환
- [ ] 실시간 진행 상태 표시
- [ ] 자동 저장 (5초 간격)

**우선순위**: 🔴 최우선 (사용자 경험 핵심)

#### **Feature 4: AI Writer Agent** 🟡 (20% - 설계 완료)
**목표**: 주제 입력 → 목표 시간에 맞는 스크립트 자동 생성
- [ ] 주제 기반 스크립트 생성
- [ ] 목표 영상 길이 설정 (15초 ~ 10분)
- [ ] 플랫폼별 최적화 (틱톡/인스타/유튜브)
- [ ] 실시간 예상 시간 표시
- [ ] 섹션별 시간 배분 (훅/본문/CTA)

**우선순위**: 🟡 중간 (MVP에 포함되지만 수동 입력으로 대체 가능)

#### **Feature 5: 영상 생성 (Director Agent)** 🔴 (0% - 핵심)
**목표**: 오디오 + 영상 클립 → 완성된 영상
- [ ] Google Veo API 연동
- [ ] Nano Banana 캐릭터 일관성
- [ ] HeyGen 립싱크 또는 Wav2Lip
- [ ] 자막 자동 생성 및 타이밍
- [ ] 배경음악 자동 믹싱

**우선순위**: 🔴 최우선 (MVP 핵심 가치)

#### **Feature 6: 콘티별 미세 조정** 🟢 (0% - Phase 2)
**목표**: 90% AI 생성 후 10% 사용자 조정
- [ ] 타임라인 뷰어
- [ ] 콘티별 섹션 카드
- [ ] 자막 위치/스타일 변경
- [ ] BGM 볼륨 조절
- [ ] 클립 교체 (AI 생성 3개 중 선택)

**우선순위**: 🟢 낮음 (Phase 2, MVP 이후)

---

## 3. 기술 스택 확정

### Backend

```yaml
언어: Python 3.11+
프레임워크: FastAPI
작업 큐: Celery + Redis
데이터베이스:
  - Neo4j: 프로젝트 그래프, 사용자 취향 학습
  - Redis: Celery 브로커, 세션 캐시
AI/ML:
  - OpenAI API: GPT-4o (스크립트 생성), Whisper v3 (STT)
  - ElevenLabs: TTS, Voice Cloning
  - Google Veo: 영상 생성 (예정)
  - HeyGen API: 립싱크 (예정)
미디어 처리:
  - FFmpeg: 영상 편집 및 렌더링
  - pdf2image: PDF 변환
  - pytesseract: OCR
모니터링:
  - Logfire: 관측성 및 비용 추적
배포:
  - Docker Compose (개발)
  - Kubernetes (프로덕션 예정)
```

### Frontend

```yaml
프레임워크: Next.js 14 (App Router)
언어: TypeScript
상태 관리: React Context API (+ Zustand 고려)
UI 라이브러리: Tailwind CSS
영상 편집:
  - Fabric.js / Konva.js (캔버스 편집)
  - WaveSurfer.js (오디오 파형)
  - Video.js (플레이어)
애니메이션: Framer Motion
통신:
  - HTTP (API 호출)
  - WebSocket (실시간 진행 상태)
```

### 인프라

```yaml
컨테이너: Docker + Docker Compose
CI/CD: GitHub Actions
모니터링: Logfire
미디어 저장: Cloudinary (예정)
배포:
  - 개발: 로컬 Docker
  - 프로덕션: AWS/GCP (예정)
```

---

## 4. Phase별 구현 계획

### 📅 Phase 0: 현재 시스템 안정화 (1주)

**목표**: 기존 구현된 기능들의 버그 수정 및 테스트

#### Tasks
- [ ] **메타데이터 제거 로직 테스트**
  - text_normalizer.py 수정사항 Docker 재빌드
  - 테스트 스크립트로 검증
  - 예상 시간: 1일

- [ ] **오디오 생성 엔드투엔드 테스트**
  - 짧은 텍스트 (30초)
  - 중간 텍스트 (1분)
  - 긴 텍스트 (3분)
  - 각 케이스별 유사도 및 시간 측정
  - 예상 시간: 2일

- [ ] **Docker 환경 최적화**
  - 볼륨 마운트 재활성화 시도
  - 빌드 시간 단축
  - 예상 시간: 1일

- [ ] **문서 정리**
  - API 문서 작성 (Swagger 자동 생성)
  - 주요 설정 파일 README 추가
  - 예상 시간: 1일

**기간**: 5일 (1주)
**완료 기준**:
- ✅ 오디오 생성 성공률 95% 이상
- ✅ 평균 유사도 95% 이상
- ✅ Docker 재빌드 시간 3분 이내

---

### 📅 Phase 1: 프로젝트 기반 인프라 (2주)

**목표**: 프로젝트 중심의 API 구조 및 Neo4j 스키마 구축

#### Week 1: Backend API

**Tasks**
- [ ] **Neo4j 스키마 설계**
  ```cypher
  (User)-[:OWNS]->(Project)
  (Project)-[:HAS_SCRIPT]->(Script)
  (Project)-[:HAS_AUDIO]->(Audio)
  (Project)-[:HAS_VIDEO]->(Video)
  ```
  - 예상 시간: 2일

- [ ] **Project CRUD API**
  ```python
  POST   /api/v1/projects
  GET    /api/v1/projects
  GET    /api/v1/projects/{id}
  PATCH  /api/v1/projects/{id}
  DELETE /api/v1/projects/{id}
  ```
  - 예상 시간: 3일

- [ ] **기존 Audio API 마이그레이션**
  ```python
  # Before
  POST /api/v1/audio/generate

  # After
  POST /api/v1/projects/{id}/audio
  ```
  - 기존 API 유지하면서 새 API 추가 (Strangler Fig Pattern)
  - 예상 시간: 2일

#### Week 2: Frontend 상태 관리

**Tasks**
- [ ] **ProductionContext 구현**
  ```typescript
  interface ProductionState {
    projectId: string;
    currentStep: 'writer' | 'director' | 'marketer' | 'deployment';
    script: ScriptData;
    audio: AudioData;
    video: VideoData;
  }
  ```
  - 예상 시간: 2일

- [ ] **프로젝트 관리 UI**
  - 프로젝트 목록 페이지
  - 새 프로젝트 생성
  - 기존 프로젝트 불러오기
  - 예상 시간: 3일

**기간**: 10일 (2주)
**완료 기준**:
- ✅ 프로젝트 생성 및 저장 가능
- ✅ Neo4j에 데이터 정상 저장
- ✅ 프론트엔드에서 프로젝트 전환 시 상태 유지

---

### 📅 Phase 2: 통합 프로덕션 대시보드 (3주)

**목표**: `/production` 페이지에서 Writer → Director 자동 연결

#### Week 1: 기본 레이아웃

**Tasks**
- [ ] **ProductionLayout 컴포넌트**
  - 4단계 진행 바 (Writer → Director → Marketer → Deployment)
  - 단계별 활성화 표시
  - 예상 시간: 2일

- [ ] **WriterPanel (수동 입력 버전)**
  - 스크립트 에디터 (Monaco Editor)
  - 실시간 저장 (debounce 5초)
  - 글자 수 / 예상 시간 표시
  - 예상 시간: 3일

#### Week 2: Director 통합

**Tasks**
- [ ] **DirectorPanel**
  - WriterPanel에서 스크립트 자동 전달
  - 음성 선택 UI
  - AudioProgressTracker 통합
  - 생성 완료 시 AudioPlayer
  - 예상 시간: 3일

- [ ] **자동 컨텍스트 전달**
  - "다음" 버튼 클릭 시 자동 전환
  - 데이터 손실 없이 이동
  - 예상 시간: 2일

#### Week 3: 자동 저장 및 UX 개선

**Tasks**
- [ ] **자동 저장 시스템**
  - 5초마다 ProductionContext → Backend 저장
  - 새로고침 시에도 복구
  - 예상 시간: 2일

- [ ] **에러 처리 및 복구**
  - 중간 실패 시 이전 단계로 돌아가기
  - 재시도 버튼
  - 예상 시간: 2일

- [ ] **UX 개선**
  - 키보드 단축키 (Cmd+S 저장, Cmd+Enter 다음)
  - 로딩 스켈레톤
  - 툴팁 및 가이드
  - 예상 시간: 1일

**기간**: 15일 (3주)
**완료 기준**:
- ✅ 스크립트 작성 → 오디오 생성 자동 연결
- ✅ 복사/붙여넣기 없이 워크플로우 완성
- ✅ 자동 저장 동작 확인
- ✅ 사용자 테스트 긍정 피드백 70% 이상

---

### 📅 Phase 3: Writer Agent 구현 (2주)

**목표**: 주제 입력 → AI가 목표 시간에 맞는 스크립트 자동 생성

#### Week 1: Duration Calculator & LLM 통합

**Tasks**
- [ ] **DurationCalculator 구현**
  - 텍스트 → 음성 시간 예측
  - 언어별 읽기 속도 설정
  - 구두점 휴지 고려
  - 예상 시간: 2일

- [ ] **WriterAgent 기본 구현**
  - 주제 → 스크립트 생성 (LLM)
  - 목표 시간 제약 조건 프롬프트
  - 예상 시간: 3일

#### Week 2: 실시간 조정 및 학습

**Tasks**
- [ ] **실시간 분량 조정**
  - 스크립트 수정 시 즉시 예상 시간 업데이트
  - AI 자동 조정 API (`/adjust-script-duration`)
  - 예상 시간: 2일

- [ ] **DurationLearningSystem**
  - 실제 TTS 시간 기록
  - 예측 vs 실제 오차 학습
  - 보정 계수 계산
  - 예상 시간: 3일

**기간**: 10일 (2주)
**완료 기준**:
- ✅ AI 생성 스크립트 목표 시간 대비 ±10% 이내
- ✅ 사용자 수정 시 실시간 예상 시간 업데이트
- ✅ 학습 데이터 50개 이상 수집 시 정확도 95% 달성

---

### 📅 Phase 4: Director Agent - 영상 생성 (4주)

**목표**: 오디오 + 비주얼 → 완성된 영상

#### Week 1-2: Google Veo 통합

**Tasks**
- [ ] **Google Veo API 연동**
  - API 인증 및 테스트
  - 프롬프트 → 영상 생성
  - 예상 시간: 3일

- [ ] **Nano Banana 캐릭터 일관성**
  - 캐릭터 레퍼런스 이미지 생성
  - Veo 호출 시 레퍼런스 전달
  - 예상 시간: 2일

- [ ] **스크립트 → Veo 프롬프트 변환**
  - 섹션별 시각적 설명 자동 생성
  - 예: "훅" → "Modern studio, friendly female presenter"
  - 예상 시간: 3일

- [ ] **영상 생성 작업 큐**
  - Celery 작업으로 비동기 처리
  - 진행 상태 WebSocket 전송
  - 예상 시간: 2일

#### Week 3: 립싱크 및 자막

**Tasks**
- [ ] **HeyGen API 또는 Wav2Lip**
  - 립싱크 처리 파이프라인
  - 오디오 + 영상 → 립싱크 영상
  - 예상 시간: 4일

- [ ] **자막 자동 생성**
  - Whisper Timestamps 활용
  - SRT 파일 생성
  - FFmpeg로 자막 오버레이
  - 예상 시간: 3일

#### Week 4: 최종 렌더링 및 최적화

**Tasks**
- [ ] **SlideVideoRenderer 구현**
  - 오디오 + 영상 클립 + 자막 → 최종 영상
  - 화면 전환 효과 (fade/slide/zoom)
  - 배경음악 믹싱
  - 예상 시간: 4일

- [ ] **Cloudinary 통합**
  - 영상 업로드 및 최적화
  - 플랫폼별 변환 (9:16, 16:9, 1:1)
  - 예상 시간: 3일

**기간**: 24일 (4주)
**완료 기준**:
- ✅ 스크립트 → 영상 엔드투엔드 생성 성공
- ✅ 립싱크 품질 만족 (사용자 테스트)
- ✅ 자막 타이밍 정확도 95% 이상
- ✅ 렌더링 시간 5분 이내 (60초 영상 기준)

---

### 📅 Phase 5: 실시간 피드백 (WebSocket) (1주)

**목표**: 폴링 → WebSocket으로 전환하여 진행 상태 실시간 업데이트

**Tasks**
- [ ] **FastAPI WebSocket 엔드포인트**
  ```python
  WS /api/v1/projects/{id}/stream
  ```
  - 예상 시간: 2일

- [ ] **Celery → WebSocket 이벤트 발행**
  - 작업 진행률 이벤트
  - 에러 발생 시 즉시 알림
  - 예상 시간: 2일

- [ ] **React WebSocket 클라이언트**
  - 자동 재연결
  - Fallback to 폴링
  - 예상 시간: 1일

**기간**: 5일 (1주)
**완료 기준**:
- ✅ 진행 상태 1초 내 업데이트
- ✅ 네트워크 끊김 시 자동 재연결
- ✅ WebSocket 실패 시 폴링으로 전환

---

### 📅 Phase 6: 콘티별 미세 조정 (3주)

**목표**: 90% AI 생성 후 10% 사용자 조정

#### Week 1: 타임라인 뷰어

**Tasks**
- [ ] **VideoTimeline 컴포넌트**
  - 영상/오디오/자막 레이어
  - 재생/정지/구간 이동
  - 예상 시간: 4일

- [ ] **콘티 섹션 카드**
  - 훅/본문/CTA 구간별 카드
  - 클릭 시 해당 구간 재생
  - 예상 시간: 3일

#### Week 2: 조정 기능

**Tasks**
- [ ] **자막 조정**
  - 위치/스타일/크기 변경
  - 실시간 미리보기
  - 예상 시간: 3일

- [ ] **BGM 조정**
  - 볼륨 슬라이더
  - 페이드인/아웃
  - 예상 시간: 2일

- [ ] **클립 교체**
  - AI 생성 대체 영상 3개 제공
  - 원클릭 교체
  - 예상 시간: 2일

#### Week 3: 스타일 프리셋

**Tasks**
- [ ] **플랫폼별 프리셋**
  - 유튜브 쇼츠 / 인스타 릴스 / 틱톡
  - 원클릭 최적화
  - 예상 시간: 3일

- [ ] **커스텀 프리셋 저장**
  - 사용자 설정 저장
  - Neo4j에 프리셋 저장
  - 예상 시간: 2일

**기간**: 15일 (3주)
**완료 기준**:
- ✅ 타임라인 재생 정상 동작
- ✅ 자막/BGM 조정 실시간 반영
- ✅ 프리셋 적용 시 1초 내 변경

---

### 📅 Phase 7: PDF 프리젠테이션 모드 (2주)

**목표**: PDF 업로드 → 나레이션 붙은 프리젠테이션 영상 생성

**Tasks**
- [ ] **PDFProcessor 구현**
  - PDF → 이미지 변환
  - OCR 텍스트 추출
  - 예상 시간: 2일

- [ ] **SlideToScriptConverter**
  - 슬라이드 → 나레이션 자동 생성
  - 예상 시간: 2일

- [ ] **Whisper Timestamps 기반 타이밍**
  - 음성 구간 분석
  - 슬라이드별 타이밍 매칭
  - 예상 시간: 2일

- [ ] **PresentationMode UI**
  - 슬라이드 썸네일 리스트
  - 나레이션 편집
  - 화면 전환 효과 선택
  - 예상 시간: 4일

**기간**: 10일 (2주)
**완료 기준**:
- ✅ PDF 업로드 → 영상 생성 엔드투엔드
- ✅ 슬라이드 타이밍 정확도 90% 이상
- ✅ 화면 전환 효과 정상 동작

---

### 📅 Phase 8: 프로덕션 배포 준비 (2주)

**목표**: 실제 사용자 대상 서비스 런칭

**Tasks**
- [ ] **성능 최적화**
  - 렌더링 속도 개선
  - API 응답 시간 단축
  - 예상 시간: 3일

- [ ] **보안 강화**
  - 인증/인가 (JWT)
  - API Rate Limiting
  - 예상 시간: 2일

- [ ] **CI/CD 파이프라인**
  - GitHub Actions
  - 자동 테스트 및 배포
  - 예상 시간: 2일

- [ ] **모니터링 및 알림**
  - Logfire 완전 연동
  - Slack 알림
  - 예상 시간: 2일

- [ ] **사용자 문서**
  - 사용 가이드
  - API 문서
  - FAQ
  - 예상 시간: 1일

**기간**: 10일 (2주)
**완료 기준**:
- ✅ 배포 자동화 완료
- ✅ 평균 응답 시간 2초 이내
- ✅ 에러율 1% 미만
- ✅ Logfire 대시보드 정상 동작

---

## 5. 우선순위 매트릭스

### 📊 Impact vs Effort

```
High Impact, Low Effort (Quick Wins)
┌──────────────────────────────────────┐
│ ✅ 메타데이터 제거 (Phase 0)           │ → 즉시 시작
│ ✅ 프로젝트 CRUD API (Phase 1)         │ → Week 1
│ ✅ ProductionContext (Phase 1)        │ → Week 2
└──────────────────────────────────────┘

High Impact, High Effort (Big Bets)
┌──────────────────────────────────────┐
│ 🔥 통합 프로덕션 대시보드 (Phase 2)    │ → MVP 핵심
│ 🔥 Director Agent 영상 생성 (Phase 4) │ → MVP 핵심
│ 🔥 Writer Agent (Phase 3)             │ → 차별화 요소
└──────────────────────────────────────┘

Low Impact, Low Effort (Fill-ins)
┌──────────────────────────────────────┐
│ ⚪ WebSocket 실시간 (Phase 5)         │ → Phase 2 이후
│ ⚪ 스타일 프리셋 (Phase 6)             │ → Phase 4 이후
└──────────────────────────────────────┘

Low Impact, High Effort (Time Sinks)
┌──────────────────────────────────────┐
│ 🚫 PDF 프리젠테이션 (Phase 7)         │ → Phase 2 기능
│ 🚫 고급 영상 편집 (Phase 6)           │ → Phase 2 기능
└──────────────────────────────────────┘
```

### 🎯 MVP 범위 결정

**MVP에 포함 (출시 필수)**:
- ✅ Phase 0: 현재 시스템 안정화
- ✅ Phase 1: 프로젝트 기반 인프라
- ✅ Phase 2: 통합 프로덕션 대시보드
- ✅ Phase 3: Writer Agent (간소화 버전)
- ✅ Phase 4: Director Agent 영상 생성
- ✅ Phase 8: 프로덕션 배포 준비

**Post-MVP (출시 후 추가)**:
- 🔜 Phase 5: WebSocket 실시간 피드백
- 🔜 Phase 6: 콘티별 미세 조정
- 🔜 Phase 7: PDF 프리젠테이션 모드

---

## 6. 리스크 관리

### 🔴 High Risk

#### Risk 1: Google Veo API 접근 불가
**확률**: 40%
**영향**: 🔥 치명적 (영상 생성 불가)
**완화 방안**:
- Plan A: Google Cloud 계정으로 조기 액세스 신청
- Plan B: Runway Gen-3 Alpha API 대체
- Plan C: Stable Diffusion Video 오픈소스 대체
- Plan D: 이미지 슬라이드쇼 + Ken Burns 효과로 MVP 출시

#### Risk 2: 렌더링 속도 너무 느림
**확률**: 60%
**영향**: 🟡 중간 (사용자 이탈)
**완화 방안**:
- 렌더링 작업 병렬화 (Celery Worker 증설)
- GPU 인스턴스 사용 (AWS p3.2xlarge)
- 프리뷰 품질 낮춰서 빠른 피드백
- 백그라운드 렌더링 후 이메일 알림

#### Risk 3: API 비용 폭발
**확률**: 50%
**영향**: 🟡 중간 (수익성 악화)
**완화 방안**:
- Logfire로 API 비용 실시간 추적
- 사용자별 일일 한도 설정
- Free tier는 저화질 영상만 제공
- 캐싱으로 중복 API 호출 방지

### 🟡 Medium Risk

#### Risk 4: Neo4j 쿼리 성능 저하
**확률**: 30%
**영향**: 🟢 낮음 (속도 저하)
**완화 방안**:
- 인덱스 최적화
- 자주 쓰는 쿼리 Redis 캐싱
- 필요 시 PostgreSQL로 부분 이전

#### Risk 5: 립싱크 품질 낮음
**확률**: 40%
**영향**: 🟡 중간 (사용자 만족도)
**완화 방안**:
- HeyGen API 우선 사용 (품질 보장)
- Wav2Lip은 Fallback으로만 사용
- 사용자가 립싱크 on/off 선택 가능

### 🟢 Low Risk

#### Risk 6: Docker 볼륨 마운트 이슈
**확률**: 20%
**영향**: 🟢 낮음 (개발 속도 저하)
**완화 방안**:
- Docker Desktop으로 전환
- 또는 재빌드 스크립트 자동화

---

## 7. 성공 지표

### 📈 KPI (Key Performance Indicators)

#### Phase 0 완료 기준
- [x] 오디오 생성 성공률 95% 이상
- [ ] 평균 유사도 95% 이상
- [ ] Docker 재빌드 시간 3분 이내

#### Phase 1 완료 기준
- [ ] 프로젝트 생성 및 저장 성공률 100%
- [ ] Neo4j 쿼리 응답 시간 100ms 이내
- [ ] API 에러율 1% 미만

#### Phase 2 완료 기준
- [ ] 스크립트 → 오디오 워크플로우 자동 연결 성공률 95%
- [ ] 복사/붙여넣기 제거 (사용자 액션 7회 → 2회)
- [ ] 자동 저장 동작률 100%
- [ ] 사용자 테스트 만족도 70% 이상

#### Phase 3 완료 기준
- [ ] AI 생성 스크립트 시간 정확도 ±10% 이내
- [ ] 스크립트 생성 시간 10초 이내
- [ ] 사용자 수정 후 재생성 요청률 30% 이하

#### Phase 4 완료 기준
- [ ] 영상 생성 성공률 90% 이상
- [ ] 립싱크 품질 사용자 만족도 80% 이상
- [ ] 자막 타이밍 정확도 95% 이상
- [ ] 60초 영상 렌더링 시간 5분 이내

#### MVP 출시 기준
- [ ] 엔드투엔드 (주제 → 영상) 성공률 85% 이상
- [ ] 평균 작업 시간 5분 이내 (기존 43분 대비)
- [ ] 시스템 가동률 99% 이상
- [ ] 얼리 어답터 10명 이상 확보
- [ ] NPS (Net Promoter Score) 50 이상

---

## 📅 전체 타임라인 요약

```
Phase 0: 현재 시스템 안정화          [1주]  ████
Phase 1: 프로젝트 기반 인프라        [2주]  ████████
Phase 2: 통합 프로덕션 대시보드      [3주]  ████████████
Phase 3: Writer Agent               [2주]  ████████
Phase 4: Director Agent 영상 생성   [4주]  ████████████████
Phase 8: 프로덕션 배포 준비         [2주]  ████████
─────────────────────────────────────────────────────
MVP 출시                            [14주 = 3.5개월]

Post-MVP:
Phase 5: WebSocket 실시간           [1주]  ████
Phase 6: 콘티별 미세 조정           [3주]  ████████████
Phase 7: PDF 프리젠테이션           [2주]  ████████
─────────────────────────────────────────────────────
Full Release                        [20주 = 5개월]
```

---

## 🎯 다음 액션 아이템

### 즉시 시작 (이번 주)
1. ✅ **메타데이터 제거 로직 테스트**
   - Docker 재빌드
   - 테스트 스크립트 작성
   - 담당: Claude
   - 기한: 1일

2. 🔄 **오디오 생성 엔드투엔드 테스트**
   - 짧은/중간/긴 텍스트 각 10회 테스트
   - 유사도 및 시간 측정
   - 담당: Claude
   - 기한: 2일

3. 📝 **Neo4j 스키마 설계 문서 작성**
   - 노드/관계 정의
   - 인덱스 전략
   - 담당: Claude
   - 기한: 1일

### 다음 주
4. 🏗️ **Project CRUD API 구현 시작**
   - 백엔드 모델 작성
   - API 엔드포인트 구현
   - 담당: Claude
   - 기한: 3일

5. ⚛️ **ProductionContext 설계**
   - TypeScript 인터페이스 정의
   - Context Provider 구현
   - 담당: Claude
   - 기한: 2일

---

## 💡 핵심 메시지

### OmniVibe Pro의 차별화 포인트

**기존 툴의 문제**:
- Adobe Premiere Pro: 전문가용, 러닝커브 높음, 모든 걸 수동으로
- Canva: 간단하지만 템플릿 제약, 영상 품질 낮음
- Loom: 화면 녹화만, 편집 불가, 발표자가 직접 말해야 함

**OmniVibe Pro의 솔루션**:
> "주제만 입력하면 → 1분 안에 완성된 영상"

**핵심 가치**:
1. **90% AI 자동 생성**: 스크립트 → 음성 → 영상 → 자막 모두 자동
2. **10% 사용자 조정**: 마음에 안 드는 부분만 클릭해서 수정
3. **Zero-Fault 품질**: TTS/STT 검증으로 발음 오류 제로
4. **플랫폼 최적화**: 틱톡/인스타/유튜브 원클릭 변환

**타겟 시장**:
- 1인 창업자, 마케터
- 교육 콘텐츠 제작자
- 기업 교육 담당자
- 비전문가 영상 크리에이터

---

## 📞 문의 및 협업

**프로젝트 리드**: 대표님
**개발**: Claude (AI Assistant)
**기술 스택 질문**: REALPLAN.md 참고
**진행 상황**: GitHub Issues 트래킹

---

**최종 업데이트**: 2025-02-01
**다음 검토일**: Phase 0 완료 후 (2025-02-08 예정)
