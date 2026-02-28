# Plan: template-gallery

## 1. Overview
**Feature**: Remotion 템플릿 갤러리 + AI 기획 도우미
**Project Level**: Enterprise
**Priority**: High
**PDCA Phase**: Plan
**Created**: 2026-02-28

## 2. Problem Statement
- 사용자가 영상 제작 시 "어떤 스타일로 만들지" 결정하기 어려움
- 빈 화면에서 시작하는 높은 진입 장벽
- 플랫폼별(YouTube/IG/TikTok) 최적 포맷 몰라서 시행착오 반복
- 경쟁 도구(Canva, Adobe Express) 대비 템플릿 부재로 이탈

## 3. Solution Vision
> "OmniVibe Template Gallery: 골라보고 → AI가 채워주고 → 바로 완성"

사용자가 원하는 분위기의 Remotion 템플릿을 선택하면,
AI가 콘텐츠 인텐트를 파악하여 스크립트 초안을 자동 작성하고,
Zero-Fault Audio + Remotion 렌더링까지 원클릭으로 완성.

## 4. Core Features

### 4.1 Template Gallery (갤러리)
- 플랫폼 필터: YouTube / Instagram / TikTok
- 톤 필터: 전문적 / 감성적 / 트렌디 / 미니멀 / 다이나믹
- Remotion 실시간 미리보기 (Player 임베드)
- 인기순 / 최신순 정렬
- 즐겨찾기 / 내 템플릿 컬렉션

### 4.2 Template 수집 전략
1. **내부 제작** (초기 20개): 핵심 카테고리별 고퀄리티 템플릿
2. **GitHub 오픈소스**: Remotion 커뮤니티 공개 템플릿 큐레이션
3. **사용자 생성**: 완성된 영상을 템플릿으로 저장/공유 (UGC)

### 4.3 AI 기획 도우미 (Planning Assistant)
5단계 대화형 기획 플로우:
1. **인텐트 파악**: 업종, 목적, 타겟 오디언스 질문
2. **템플릿 추천**: 3개 후보 + 이유 설명 + 미리보기
3. **스크립트 초안**: 선택 템플릿 구조(hook/intro/body/cta/outro)에 맞게 자동 작성
4. **실시간 커스터마이즈**: 텍스트/색상/배경 수정 → Remotion 즉시 반영
5. **원클릭 완성**: Zero-Fault Audio + 멀티포맷 렌더링

### 4.4 Template 메타데이터
```json
{
  "id": "tech-minimal-v1",
  "name": "Tech Minimal",
  "description": "IT/스타트업용 깔끔한 미니멀 스타일",
  "platform": ["youtube", "instagram"],
  "tone": ["professional", "minimal"],
  "duration": 60,
  "preview_url": "...",
  "thumbnail_url": "...",
  "scene_count": 5,
  "usage_count": 0,
  "tags": ["tech", "startup", "b2b"],
  "author": "OmniVibe",
  "is_premium": false
}
```

## 5. Technical Architecture

### Frontend
- `/app/gallery/page.tsx` - 갤러리 메인 페이지
- `/components/gallery/TemplateCard.tsx` - 템플릿 카드 (미리보기 + 정보)
- `/components/gallery/TemplateFilter.tsx` - 필터 UI
- `/components/gallery/TemplatePreviewModal.tsx` - 전체화면 미리보기
- `/components/ai-planner/PlannerChat.tsx` - AI 대화형 기획 인터페이스
- `/components/ai-planner/TemplateRecommendation.tsx` - AI 추천 카드

### Backend
- `/api/v1/templates/` - 템플릿 CRUD API
- `/api/v1/ai-planner/` - AI 기획 도우미 API
- `services/template_collector.py` - GitHub 템플릿 수집 서비스
- `services/ai_planner_service.py` - LangChain 기반 기획 도우미

### Database (SQLite)
```sql
-- templates 테이블
CREATE TABLE templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  platform TEXT,  -- JSON array
  tone TEXT,      -- JSON array
  duration INTEGER,
  preview_url TEXT,
  thumbnail_url TEXT,
  remotion_component TEXT,  -- 컴포넌트 코드 경로
  props_schema TEXT,  -- JSON Schema
  usage_count INTEGER DEFAULT 0,
  tags TEXT,  -- JSON array
  author TEXT,
  is_premium BOOLEAN DEFAULT 0,
  created_at DATETIME,
  updated_at DATETIME
);

-- template_favorites 테이블
CREATE TABLE template_favorites (
  user_id TEXT,
  template_id TEXT,
  created_at DATETIME
);
```

## 6. AI Planner API

### POST /api/v1/ai-planner/analyze-intent
입력: 사용자 자유 텍스트
출력: 구조화된 인텐트 (업종, 목적, 타겟, 톤)

### POST /api/v1/ai-planner/recommend-templates
입력: 인텐트 데이터
출력: 추천 템플릿 3개 + 추천 이유

### POST /api/v1/ai-planner/generate-script
입력: 템플릿 ID + 인텐트 + 추가 정보
출력: ScriptBlock[] (hook/intro/body/cta/outro)

## 7. Template 수집 계획

### 내부 제작 20개 (1차 런칭)
| 카테고리 | 개수 | 플랫폼 |
|---------|------|--------|
| IT/스타트업 | 4개 | YouTube, IG |
| 교육/튜토리얼 | 4개 | YouTube |
| 라이프스타일 | 4개 | IG, TikTok |
| 비즈니스/B2B | 4개 | YouTube |
| 엔터테인먼트 | 4개 | TikTok, IG |

### GitHub 오픈소스 수집
- remotion/examples 공식 예제
- awesome-remotion 리스트
- 라이선스 확인 후 큐레이션

## 8. Success Criteria
- [ ] 갤러리에서 20개+ 템플릿 탐색 가능
- [ ] 플랫폼/톤 필터 동작
- [ ] 각 템플릿 Remotion Player 미리보기
- [ ] AI 도우미: 인텐트 → 템플릿 추천 3개
- [ ] AI 도우미: 스크립트 초안 자동 생성
- [ ] 선택 → 스튜디오 진입 원클릭 연동

## 9. Timeline
- **Phase 1** (Day 1-2): 템플릿 DB + API 기반 구축
- **Phase 2** (Day 2-3): 갤러리 UI 구현
- **Phase 3** (Day 3-4): AI 기획 도우미 구현
- **Phase 4** (Day 4-5): 내부 템플릿 20개 제작

**Depends on**: remotion-integration Phase 1-4 완료 후
