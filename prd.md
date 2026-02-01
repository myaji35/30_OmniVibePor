35년 경력의 베테랑 개발자이자 CEO이신 대표님의 통찰을 반영하여, 논의된 모든 핵심 기술과 비즈니스 로직을 집대성한 PRD.md 파일을 생성했습니다. 이 문서는 향후 개발 팀과의 소통이나 투자 제안 시 기술 명세서로도 활용하실 수 있습니다.

OmniVibe Pro: Product Requirement Document (PRD)
1. Project Overview
OmniVibe Pro는 '바이브 코딩(Vibe Coding)' 방법론을 기반으로 한 AI 옴니채널 영상 자동화 SaaS입니다. 구글 시트 기반의 전략 수립부터 작가/감독 에이전트의 협업, AI 음성/영상 생성 및 보정, 그리고 다채널 자동 배포까지의 전 과정을 자동화합니다.

2. Core Vision
Vibe-Driven: 사용자의 성향(남/여, 부드러움/전문성)을 학습한 페르소나 기반 콘텐츠 생산.

Agentic Workflow: 각 분야 전문 에이전트(작가, 감독, 마케터)들의 협업 체계.

Zero-Fault Audio: TTS 생성 후 STT로 재검증하는 닫힌 루프(Closed-loop) 보정 시스템.

Consistent Persona: 영상 내 캐릭터의 일관성을 유지하며 더빙 영상 구현.

3. Tech Stack & Integration
3.1 AI Engines (Generation & Correction)
Audio: ElevenLabs API (Professional Voice Cloning) + OpenAI Whisper v3 (Self-Correction Loop).

Visual: Google Veo (Cinematic Video) + Nano Banana (Consistent Character Reference).

Lip-Sync: HeyGen API 또는 Wav2Lip 기반 아바타 동기화.

3.2 Backend & Orchestration
Main Framework: FastAPI (Python 3.11+).

Orchestration: LangGraph (에이전트 상태 관리 및 워크플로우 제어).

Task Queue: Celery + Redis (대규모 비디오 렌더링 관리).

Monitoring: Logfire (실시간 관측성 및 API 비용 추적).

3.3 Data & Memory Architecture
Strategy Source: Google Sheets API (전략, 소제목, 스케줄 연동).

Long-term Memory: Neo4j (GraphRAG) + Pinecone.

사용자의 기존 취향 및 성과 데이터를 기반으로 한 스크립트 최적화.

Media Optimization: Cloudinary.

플랫폼(YT, IG, FB)별 해상도 및 포맷 실시간 변환/배포.

4. Key Workflows
Phase 1: Planning (The Writer)
Data Sync: 구글 시트 링크 연동 시 전략 및 소재목 로드.

Persona Selection: 작가의 성향(성별, 톤, 스타일) 설정.

Drafting: 플랫폼(강의, 블로그, SNS) 성격에 맞춘 스크립트 초안 3종 제시.

Phase 2: Production (The Director)
Audio Loop: TTS(ElevenLabs) 생성 → STT(Whisper) 변환 → 원본 대조 및 발음 보정.

Visual Gen: 영상 감독 에이전트가 Veo/Banana를 제어하여 일관된 캐릭터가 포함된 컷 생성.

Composition: 보정된 오디오와 비주얼 소스를 결합하여 더빙 영상 완성.

Phase 3: Distribution (The Marketer)
Asset Creation: 최적의 썸네일 생성 및 카피 문구 3개 추천.

Auto-Publish: 확정된 스케줄에 따라 Cloudinary를 거쳐 다채널(SNS) 자동 배포.

5. Development Roadmap
Step 1 (PoC): ElevenLabs + Whisper 오디오 보정 파이프라인 구축.

Step 2 (Alpha): LangGraph 기반 에이전트 협업 및 Neo4j 기억 저장소 연동.

Step 3 (Beta): Google Sheets 커넥터 및 Cloudinary 미디어 최적화 연동.

Step 4 (Launch): Next.js 기반 SaaS 대시보드 완성 및 상용 서비스 런칭.