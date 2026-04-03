---
name: OmniVibe Pro 프로젝트 컨텍스트
description: OmniVibe Pro 프로젝트 현황 — 기술 스택, 개발 단계, 핵심 기능 현황
type: project
---

OmniVibe Pro는 Gagahoho Inc.(CEO 강승식)의 AI 기반 영상 자동화 SaaS.

**개발 현황 (2026-04-03 기준)**
- Phase 1~3 완료 (22페이지, 31개 API, 8개 Remotion Composition)
- Phase 4 (통합 테스트 + 런칭 준비) 진행 예정
- Phase 5 (전략→컨셉→생산→배포 풀파이프라인) 예정

**Why:** Phase 4 런칭 전에 비즈니스 관점 갭 분석이 필요한 시점.
**How to apply:** 기능 구현 요청 시 Phase 4 MVP 범위인지 Phase 5 기능인지 먼저 분류할 것.

**핵심 기술**
- Frontend: Next.js 14, Remotion 4, Tailwind, SLDS
- Backend: FastAPI, Celery, Redis, Neo4j, SQLite
- AI: edge-tts, ElevenLabs, OpenAI Whisper, Claude

**4-Tier 과금**: Free($0) / Creator($19) / Pro($49) / Enterprise($499)
