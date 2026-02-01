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
