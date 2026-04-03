"""프레젠테이션 자동 생성 — 스크립트 → HTML 슬라이드 → PDF

ISS-009: 멀티포맷 콘텐츠 생산
"""
import logging
import os
import json
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../outputs/presentations")


class PresentationGenerator:
    """스크립트 기반 프레젠테이션 생성기"""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    async def generate(
        self,
        script: str,
        brand_name: str = "OmniVibe Pro",
        title: Optional[str] = None,
        theme: str = "dark",  # dark, light, corporate
        slide_count: int = 0,  # 0 = 자동
    ) -> dict:
        """스크립트 → 슬라이드 HTML → 결과 반환"""

        # 스크립트를 슬라이드로 분할
        slides = self._parse_script_to_slides(script, slide_count)

        # HTML 생성
        html = self._render_html(
            slides=slides,
            brand_name=brand_name,
            title=title or slides[0]["title"] if slides else "Presentation",
            theme=theme,
        )

        # 파일 저장
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"presentation_{ts}.html"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Presentation generated: {filename} ({len(slides)} slides)")

        return {
            "filename": filename,
            "filepath": filepath,
            "download_url": f"/outputs/presentations/{filename}",
            "slide_count": len(slides),
            "slides": slides,
        }

    def _parse_script_to_slides(self, script: str, max_slides: int = 0) -> list[dict]:
        """스크립트를 슬라이드 구조로 파싱"""
        lines = [l.strip() for l in script.strip().split("\n") if l.strip()]
        slides = []

        current_title = ""
        current_bullets = []

        for line in lines:
            # [Hook], [Body], [CTA] 등의 섹션 헤더
            if line.startswith("[") and "]" in line:
                if current_title or current_bullets:
                    slides.append({
                        "title": current_title or "Slide",
                        "bullets": current_bullets,
                        "type": "content",
                    })
                current_title = line.strip("[]").strip()
                current_bullets = []
            elif line.startswith("#"):
                if current_title or current_bullets:
                    slides.append({
                        "title": current_title or "Slide",
                        "bullets": current_bullets,
                        "type": "content",
                    })
                current_title = line.lstrip("#").strip()
                current_bullets = []
            else:
                current_bullets.append(line)

        # 마지막 슬라이드
        if current_title or current_bullets:
            slides.append({
                "title": current_title or "Slide",
                "bullets": current_bullets,
                "type": "content",
            })

        # 슬라이드가 없으면 전체를 하나로
        if not slides:
            slides = [{"title": "Content", "bullets": lines, "type": "content"}]

        # 최대 슬라이드 수 제한
        if max_slides > 0:
            slides = slides[:max_slides]

        return slides

    def _render_html(self, slides: list, brand_name: str, title: str, theme: str) -> str:
        """슬라이드를 프레젠테이션 HTML로 렌더링"""
        THEMES = {
            "dark": {"bg": "#0F172A", "text": "#F1F5F9", "accent": "#6366F1", "surface": "#1E293B"},
            "light": {"bg": "#FFFFFF", "text": "#1E293B", "accent": "#3B82F6", "surface": "#F8FAFC"},
            "corporate": {"bg": "#16325C", "text": "#FFFFFF", "accent": "#00A1E0", "surface": "#1E4D8C"},
        }
        t = THEMES.get(theme, THEMES["dark"])

        slides_html = ""
        for i, slide in enumerate(slides):
            bullets_html = "".join(f'<li>{b}</li>' for b in slide["bullets"])
            slides_html += f"""
            <div class="slide" id="slide-{i}">
                <div class="slide-number">{i+1} / {len(slides)}</div>
                <h2>{slide['title']}</h2>
                <ul>{bullets_html}</ul>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {brand_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Pretendard', 'Inter', sans-serif; background: {t['bg']}; color: {t['text']}; }}
.slide {{
    width: 100vw; height: 100vh;
    display: flex; flex-direction: column; justify-content: center;
    padding: 80px 120px; position: relative;
    page-break-after: always;
}}
.slide h2 {{
    font-size: 48px; font-weight: 800; margin-bottom: 40px;
    color: {t['accent']};
}}
.slide ul {{ list-style: none; }}
.slide li {{
    font-size: 28px; line-height: 1.8; padding: 8px 0;
    padding-left: 24px; position: relative;
}}
.slide li::before {{
    content: '→'; position: absolute; left: 0; color: {t['accent']};
}}
.slide-number {{
    position: absolute; bottom: 40px; right: 60px;
    font-size: 14px; opacity: 0.3; font-family: monospace;
}}
.brand {{
    position: absolute; bottom: 40px; left: 60px;
    font-size: 14px; opacity: 0.4; font-weight: 600;
}}
@media print {{
    .slide {{ page-break-after: always; }}
}}
</style>
</head>
<body>
{slides_html}
<script>
// 키보드 네비게이션
let current = 0;
const slides = document.querySelectorAll('.slide');
const total = slides.length;
function show(n) {{
    slides.forEach((s, i) => s.style.display = i === n ? 'flex' : 'none');
    current = n;
}}
show(0);
document.addEventListener('keydown', e => {{
    if (e.key === 'ArrowRight' || e.key === ' ') show(Math.min(current + 1, total - 1));
    if (e.key === 'ArrowLeft') show(Math.max(current - 1, 0));
}});
</script>
</body>
</html>"""


_generator: Optional[PresentationGenerator] = None

def get_presentation_generator() -> PresentationGenerator:
    global _generator
    if _generator is None:
        _generator = PresentationGenerator()
    return _generator
