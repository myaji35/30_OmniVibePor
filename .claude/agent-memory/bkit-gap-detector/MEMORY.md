# Gap Detector Memory

## Project: OmniVibe Pro

### Key Paths
- Plan docs: `docs/01-plan/features/`
- Design docs: `docs/02-design/features/`
- Analysis output: `docs/03-analysis/`
- Frontend Remotion: `frontend/remotion/`
- Backend API v1: `backend/app/api/v1/`
- Backend services: `backend/app/services/`
- Router registration: `backend/app/api/v1/__init__.py`

### Analysis Patterns
- Always check `__init__.py` for router registration (common gap)
- Celery tasks use `self.update_state()` for progress but may lack WebSocket manager direct push
- Frontend types in `remotion/types.ts` must match backend Pydantic models in `models/render.py`
- `package.json` confirms actual npm dependency versions

### Past Analyses
- **remotion-integration** (2026-02-28): Match Rate 87%. Main gaps: WebSocket direct push (60%), Cloudinary upload TODO. Strengths: all 5 scenes implemented, type system 100% consistent.
- **upload** (2026-02-28): Match Rate 75%. Critical bugs: `slide_count` vs `total_slides` field mismatch (always returns 0), DPI 150 vs 200 mismatch, Studio page ignores `presentation_id`/`voice_id` query params. Upload page uses local interfaces instead of shared `lib/types/presentation.ts` types.

### Common Patterns Found
- Frontend pages sometimes define local interfaces instead of importing from `lib/types/` - leads to field name drift
- Fallback chains referencing non-existent backend fields (e.g., `data.id`, `data.elevenlabs_voice_id`) - defensive coding that masks real issues
- Query param send/receive asymmetry between pages - always verify both ends
