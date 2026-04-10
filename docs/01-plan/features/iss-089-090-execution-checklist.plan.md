# Execution Checklist — ISS-089 PostgreSQL + ISS-090 Marp Spike

**다음 세션 즉시 실행용 상세 체크리스트.**

- Created: 2026-04-10
- Preparing for: 다음 세션 P0 작업 2건

---

## 실행 순서 권장

1. **ISS-090 먼저** (1시간) — Path 1 gate 결정이 전체 Marp 전략에 영향
2. **ISS-089 다음** (2~3시간) — PostgreSQL 인프라, Path 1 결정 무관하게 필요

---

## ISS-090: Marp PPTX Editability Spike (1시간)

### Step 1: 테스트 마크다운 작성
`backend/test_marp_spike/test-marp.md`
```markdown
---
marp: true
theme: default
---

# 병의원 소개

## 레이저 IPL 시술

- 피부 톤 개선
- 색소 침착 완화
- 1회 시술 30분

---

## 가격표

| 시술 | 정가 | 이벤트가 |
|---|---|---|
| IPL | 30만원 | 20만원 |
| HIFU | 50만원 | 35만원 |
```

### Step 2: Marp CLI Docker 실행
```bash
docker run --rm -v $(pwd):/home/marp/app marpteam/marp-cli:latest \
  test-marp.md --pptx -o test-marp.pptx
```

### Step 3: PPTX 내부 구조 검사
```bash
unzip -p test-marp.pptx ppt/slides/slide1.xml | head -50
# 확인: <a:t> (텍스트) vs <p:pic> (이미지)
```

### Step 4: python-pptx 읽기/수정/재저장
```python
from pptx import Presentation
prs = Presentation('test-marp.pptx')
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if 'IPL' in run.text:
                        run.text = run.text.replace('30만원', '25만원')
prs.save('test-marp-edited.pptx')
```

### Step 5: macOS Keynote/PowerPoint 수동 열기
```bash
open test-marp-edited.pptx
```

### Acceptance
- [ ] Marp CLI Docker 실행
- [ ] slide1.xml에서 `<a:t>` 태그 확인
- [ ] python-pptx 수정 성공
- [ ] Keynote open 성공
- [ ] verdict 기록

### Gate
- **GO**: `editable_text=true AND edit_and_resave=successful`
- **NOGO**: ISS-064 Path 1 제거, Path 2+3만 유지

---

## ISS-089: Phase 0-B Alembic + PostgreSQL 16 컨테이너

### Step 1: Docker Compose postgres service 추가
```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: omnivibe-postgres
    environment:
      POSTGRES_USER: omnivibe
      POSTGRES_PASSWORD: omnivibe2026
      POSTGRES_DB: omnivibe_dev
    volumes:
      - omnivibe_pg_data:/var/lib/postgresql/data
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U omnivibe"]
      interval: 5s
volumes:
  omnivibe_pg_data:
```

### Step 2: backend/.env.example
```
DATABASE_URL=postgresql+asyncpg://omnivibe:omnivibe2026@localhost:5432/omnivibe_dev
DATABASE_URL_SQLITE=sqlite+aiosqlite:///./omni_db.sqlite
```

### Step 3: Alembic init
```bash
cd backend && source venv/bin/activate
alembic init alembic
```

### Step 4: alembic/env.py
- `from app.db.base import Base`
- 모든 모델 import (client/campaign/content_schedule/generated_script/storyboard_block/resource_library/ab_test)
- `target_metadata = Base.metadata`
- `sqlalchemy.url`을 env DATABASE_URL로

### Step 5: Initial revision
```bash
alembic revision --autogenerate -m "001 initial 7 tables"
```

### Step 6: Apply
```bash
docker compose up -d postgres
alembic upgrade head
psql postgresql://omnivibe:omnivibe2026@localhost:5432/omnivibe_dev -c "\dt"
```

### Step 7: Backend 기동
```bash
DATABASE_URL="postgresql+asyncpg://..." uvicorn app.main:app --port 8030
curl http://localhost:8030/health
```

### Acceptance
- [ ] docker-compose postgres service
- [ ] alembic init 완료
- [ ] revision 001 생성 (7 테이블)
- [ ] upgrade head 성공
- [ ] backend PG로 기동
- [ ] SQLite fallback 동작

### Risks
- **R1**: Stage 1 모델 부분 정의 → FK/index 놓칠 수 있음. **대응**: 수동 revision 검토
- **R2**: asyncpg Python 3.14 호환 이슈. **대응**: pip install 재확인
- **R3**: resource_library Stage 2 미완 → revision 002로 분리

---

## 다음 세션 실행 명령 템플릿

```
대표님 지시: "ISS-090 먼저 실행해줘"
→ 본 체크리스트 § ISS-090 Step 1-5 순차 실행
→ Gate 결정 → ISS-064 plan 업데이트

대표님 지시: "ISS-089 진행"
→ 본 체크리스트 § ISS-089 Step 1-7 순차 실행
→ SQLAlchemy Stage 1 모델 기반 revision 001 생성
```

---

**Linked**:
- `docs/01-plan/features/marp-slide-system.plan.md` (ISS-064)
- `docs/01-plan/features/firecrawl-brand-onboarding.plan.md` (ISS-085)
- `docs/01-plan/features/notebooklm-to-marp-mapping.plan.md` (ISS-088)
