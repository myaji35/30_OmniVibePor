# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
OmniVibe Pro는 '바이브 코딩(Vibe Coding)' 방법론을 기반으로 한 AI 옴니채널 영상 자동화 SaaS 플랫폼입니다. 구글 시트 기반 전략 수립부터 AI 에이전트 협업, 영상 생성/보정, 다채널 자동 배포까지 전 과정을 자동화합니다.

## Architecture Overview

### Core System Design
이 프로젝트는 3개의 주요 에이전트가 협업하는 구조입니다:

1. **The Writer (작가 에이전트)**
   - 구글 시트에서 전략/소재목 로드
   - 페르소나 기반 스크립트 초안 생성 (플랫폼별 3종)
   - Neo4j GraphRAG + Pinecone을 활용한 사용자 취향 학습

2. **The Director (감독 에이전트)**
   - **Zero-Fault Audio Loop**: ElevenLabs TTS → OpenAI Whisper STT → 원본 대조 및 발음 보정
   - Google Veo + Nano Banana를 활용한 일관된 캐릭터 영상 생성
   - HeyGen 또는 Wav2Lip 기반 립싱크 처리

3. **The Marketer (마케터 에이전트)**
   - 썸네일 및 카피 문구 자동 생성
   - Cloudinary를 통한 플랫폼별 최적화 (해상도/포맷)
   - 스케줄 기반 다채널 자동 배포

### Tech Stack

**Backend**
- FastAPI (Python 3.11+): 메인 API 서버
- LangGraph: 에이전트 상태 관리 및 워크플로우 오케스트레이션
- Celery + Redis: 비디오 렌더링 작업 큐
- Logfire: 실시간 관측성 및 API 비용 추적

**Data & Memory**
- Google Sheets API: 전략 및 스케줄 연동
- Neo4j: GraphRAG 장기 메모리
- Pinecone: 벡터 검색 (사용자 취향 학습)

**AI Services**
- ElevenLabs: Professional Voice Cloning
- OpenAI Whisper v3: STT 기반 오디오 검증
- Google Veo: 시네마틱 영상 생성
- Nano Banana: 일관된 캐릭터 레퍼런스
- HeyGen API / Wav2Lip: 립싱크

**Media & Distribution**
- Cloudinary: 플랫폼별 미디어 최적화 및 변환
- Next.js: SaaS 대시보드 프론트엔드 (예정)

## Development Workflow

### Audio Closed-Loop Correction
오디오 생성 시 반드시 다음 루프를 따라야 합니다:
1. ElevenLabs API로 TTS 생성
2. Whisper v3로 STT 변환
3. 원본 스크립트와 대조
4. 발음 오류 발견 시 재생성
5. 정확도 임계값 달성까지 반복

### Agent Orchestration Pattern
LangGraph를 사용한 에이전트 워크플로우:
- 각 에이전트는 독립적인 상태(state)를 가짐
- 에이전트 간 전환은 명시적 조건(conditional edges)으로 관리
- 모든 에이전트 액션은 Logfire로 추적

### Persona Consistency
영상 생성 시 캐릭터 일관성 유지:
- Nano Banana로 캐릭터 레퍼런스 이미지 생성
- 모든 Veo API 호출 시 동일 레퍼런스 전달
- 사용자 설정(성별, 톤, 스타일)을 Neo4j에 영구 저장

## Development Roadmap

### Step 1 (PoC)
- FastAPI 기본 구조 설정
- ElevenLabs + Whisper 오디오 보정 파이프라인 구현
- 기본 Celery 작업 큐 설정

### Step 2 (Alpha)
- LangGraph 기반 3개 에이전트 구현
- Neo4j + Pinecone 메모리 시스템 연동
- Logfire 모니터링 설정

### Step 3 (Beta)
- Google Sheets API 커넥터
- Cloudinary 미디어 최적화 파이프라인
- Google Veo + Nano Banana 영상 생성 통합

### Step 4 (Launch)
- HeyGen/Wav2Lip 립싱크 통합
- Next.js SaaS 대시보드 완성
- 다채널 자동 배포 시스템 완성

## Important Patterns

### Error Handling
- 모든 외부 API 호출은 재시도 로직 포함 (tenacity 라이브러리 권장)
- Whisper STT 검증에서 정확도가 95% 미만이면 반드시 재생성
- Celery 작업 실패 시 상태를 사용자에게 명확히 전달

### Memory Management
- 사용자 페르소나는 Neo4j에 그래프 형태로 저장
- 과거 성과 데이터는 벡터화하여 Pinecone에 저장
- 구글 시트 데이터는 캐싱하되, 변경 감지 시 즉시 동기화

### Cost Optimization
- Logfire로 API 호출당 비용 추적
- 영상 생성 전 사용자에게 예상 비용 표시
- Cloudinary 변환은 배치 처리로 최적화

## Vibe Coding Level 4 - Autonomous Execution Rules

### Slash Commands for Autonomous Execution

이 프로젝트는 **Vibe Coding Lv.4**를 지원합니다. 사용자가 슬래시 커맨드를 사용하면 Claude는 자율적으로 작업을 실행합니다.

#### `/phase {number}` - 자율 Phase 실행
- **목적**: REALPLAN.md의 특정 Phase를 완전 자율적으로 실행
- **자율권**:
  - 파일 생성/수정 사전 승인 불필요 (프로덕션 DB/환경 변수 제외)
  - 에러 발생 시 자동 재시도 (최대 3회)
  - 의존성 자동 설치 (pyproject.toml/package.json 수정)
  - 테스트 자동 실행 및 실패 시 자동 수정
- **실행 패턴**:
  1. REALPLAN.md에서 Phase 태스크 추출
  2. 의존성 분석 및 병렬 그룹 식별
  3. TodoWrite로 모든 태스크 추가
  4. Task 도구로 병렬 그룹 실행
  5. 각 그룹 완료 시 진행 상황 보고
  6. Phase 완료 시 최종 보고 및 다음 단계 제안

#### `/auto "{goal}"` - 완전 자율 실행
- **목적**: 목표만 제시하면 Claude가 계획부터 실행까지 모두 수행
- **자율권**: `/phase`의 모든 권한 + 아키텍처 변경 권한
- **실행 패턴**:
  1. 목표 분석 및 현재 상태 파악
  2. 실행 계획 자동 생성 (Phase 분할)
  3. 각 Phase 자율 실행
  4. 실패 시 계획 수정 및 재시도
  5. 목표 달성 시 최종 보고

#### `/health` - 시스템 헬스 체크 및 자동 복구
- **목적**: 프로젝트 상태 점검 및 문제 자동 해결
- **점검 항목**:
  - Docker 컨테이너 상태
  - 의존성 설치 상태
  - 환경 변수 설정
  - 데이터베이스 연결
  - 외부 API 연결 (ElevenLabs, Whisper 등)
- **자동 복구**:
  - 컨테이너 다운 시 자동 재시작
  - 의존성 누락 시 자동 설치
  - 설정 오류 시 자동 수정

### Autonomous Error Recovery

에러 발생 시 다음 절차를 **자동으로** 실행:

1. **에러 분석**:
   - 로그 파일 자동 읽기
   - 에러 타입 분류 (일시적/영구적)
   - 유사 에러 패턴 검색 (Neo4j에서 과거 이력 조회)

2. **자동 해결 시도** (최대 3회):
   - 일시적 에러: 재시도
   - 의존성 에러: 패키지 설치
   - 설정 에러: 설정 파일 수정
   - 코드 에러: 코드 수정 시도

3. **에스컬레이션**:
   - 3회 실패 시 사용자에게 보고
   - 해결책 2-3개 제시
   - 사용자 선택 대기

### Self-Learning System

Claude는 각 세션 종료 시 자동으로 학습하고 CLAUDE.md를 업데이트합니다:

#### 학습 항목
- **에러 패턴**: 자주 발생하는 에러와 해결책을 "Error Patterns" 섹션에 추가
- **효율적 워크플로우**: 성공적인 병렬화 패턴을 "Efficient Patterns" 섹션에 추가
- **Phase 실행 통계**: 각 Phase의 평균 실행 시간과 난이도를 기록

#### 업데이트 예시
```markdown
## Error Patterns (Auto-Learned)

### Docker Volume Mount on ExFAT
- **문제**: ExFAT 파일시스템에서 volume mount 실패
- **원인**: ExFAT는 Unix 권한 미지원
- **해결**: APFS 볼륨으로 이동 또는 rebuild 워크플로우 사용
- **학습일**: 2026-02-02
- **재발 방지**: 프로젝트 초기화 시 파일시스템 확인

### ElevenLabs TTS Metadata Reading
- **문제**: 스크립트의 메타데이터(### 훅, --- 예상 영상 길이)를 TTS가 읽음
- **해결**: text_normalizer.py에 메타데이터 제거 로직 추가
- **학습일**: 2026-02-02
- **재발 방지**: 스크립트 생성 시 자동 정규화 적용
```

### Parallel Execution Rules

병렬 실행 시 다음 규칙을 **자동으로** 적용:

1. **의존성 분석**:
   - 파일 의존성: A 파일을 B 파일이 import하면 순차
   - 데이터 의존성: A 작업의 결과를 B 작업이 사용하면 순차
   - 리소스 의존성: 동일 DB/API를 사용하면 순차

2. **병렬 그룹 생성**:
   - 그룹 1: 의존성 없는 작업들
   - 그룹 2: 그룹 1 완료 후 실행 가능한 작업들
   - 그룹 N: 그룹 N-1 완료 후 실행 가능한 작업들

3. **Task 도구 사용**:
   - 동일 그룹 작업은 **단일 메시지**에서 여러 Task 도구 호출
   - 각 Task는 독립적인 서브에이전트로 실행
   - 모든 서브에이전트 완료 후 다음 그룹 시작

### Quality Assurance Rules

코드 생성 시 다음을 **자동으로** 수행:

1. **테스트**:
   - 주요 함수는 자동으로 테스트 케이스 생성
   - 생성한 코드는 즉시 pytest 실행
   - 실패 시 코드 수정 및 재테스트 (최대 3회)

2. **린팅**:
   - Python: ruff 자동 실행 및 수정
   - TypeScript: eslint 자동 실행 및 수정

3. **타입 체크**:
   - Python: mypy 실행 (에러 발생 시 타입 힌트 추가)
   - TypeScript: tsc 실행 (에러 발생 시 타입 수정)

4. **문서화**:
   - 주요 클래스/함수는 자동으로 docstring 생성
   - API 엔드포인트는 자동으로 OpenAPI 스키마 추가

### TodoWrite Integration

모든 자율 실행 시 TodoWrite를 **필수로** 사용:

1. **작업 시작 전**: 모든 태스크를 todo list에 추가
2. **작업 중**: 정확히 1개 태스크만 in_progress 상태 유지
3. **작업 완료 즉시**: completed로 변경 (배치 금지)
4. **새 작업 발견 시**: 즉시 todo list에 추가

이를 통해 사용자는 실시간으로 진행 상황을 파악할 수 있습니다.

### Communication Style in Autonomous Mode

자율 실행 모드에서는 다음 스타일로 소통:

1. **간결성**: 각 단계를 1-2문장으로 요약
2. **진행 상황**: 이모지로 시각적 표현 (✅ 완료, 🚀 시작, ⚠️ 주의)
3. **투명성**: 에러 발생 시 숨기지 않고 즉시 보고
4. **제안**: 완료 후 다음 단계를 명확히 제시

예시:
```
✅ Phase 0.1 완료 (메타데이터 제거 로직 테스트)
🚀 Phase 0.2 시작 (오디오 생성 엔드투엔드 테스트)

**병렬 그룹 1**: 테스트 스크립트 생성 (3개)
[Task 도구 3개 병렬 실행]

✅ 병렬 그룹 1 완료 (3/3 성공)
🚀 병렬 그룹 2 시작: 오디오 생성 실행
```
