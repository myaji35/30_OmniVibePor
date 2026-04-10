"""
NotebookLM Adapter — Path 2 (수동 PDF 업로드 경로)

하이브리드 전략:
- Path 1: Marp 자동 생성 (개발팀 SoT)
- Path 2: NotebookLM Studio 수동 생성 → 본 어댑터로 처리 ← 여기
- Path 3: 회원 자체 PDF 업로드

NotebookLM이 수동 생성한 PDF는 우측 하단에 "% NotebookLM" 워터마크가
찍혀 나옵니다. 본 어댑터는:
    1. PDF가 NotebookLM 출력인지 감지
    2. 맞으면 각 슬라이드 이미지의 우측 하단 ~3% 영역을 crop
    3. 아니면 no-op으로 그대로 통과

설계 원칙 (Atomic Option Group 패턴 — ISS-042 교훈):
- detect_notebooklm() = 감지 단일 책임
- crop_watermark_pil() = crop 단일 책임 (PIL 레벨)
- process_slides() = 통합 엔트리포인트
- verify_crop_applied() = co-located verifier

호환성:
- 기존 pdf_to_slides_service와 투명 호환
- 비-NotebookLM PDF는 바이트 단위로 동일 결과
- detect 실패 시 no-op (안전 기본값)

참고:
- NotebookLM Studio는 1376×768 해상도로 PDF 출력
- 워터마크는 우측 하단 약 30×10 px (3% × 1.3%)
- safety margin으로 crop 영역을 약간 크게 잡음 (4% × 2%)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 감지 상수
# ─────────────────────────────────────────────────────────────

NOTEBOOKLM_WATERMARK_MARKERS = (
    "NotebookLM",
    "% NotebookLM",
    "Made with NotebookLM",
)
"""PDF 텍스트 레이어에서 NotebookLM 출력을 식별하는 마커"""


# ─────────────────────────────────────────────────────────────
# Crop 파라미터 (safety margin 포함)
# ─────────────────────────────────────────────────────────────

# 워터마크 실측: ~30×10 px @ 1376×768 → (2.2%, 1.3%)
# safety margin → (4%, 2.5%) — 해상도 독립적
WATERMARK_CROP_WIDTH_RATIO = 0.04
WATERMARK_CROP_HEIGHT_RATIO = 0.025

# Crop 방식: replace with white (transparent 불가능 — JPEG 호환성)
WATERMARK_FILL_COLOR = (255, 255, 255)  # white


# ─────────────────────────────────────────────────────────────
# 감지 함수
# ─────────────────────────────────────────────────────────────

def detect_notebooklm_pdf(pdf_path: str) -> bool:
    """
    PDF가 NotebookLM이 생성한 것인지 감지.

    감지 전략 (순서):
        1. PyPDF2로 첫 페이지 텍스트 추출 → 마커 매칭
        2. PyPDF2 실패 시 metadata Creator/Producer 확인
        3. 전부 실패 시 False (안전 기본값 — 비NotebookLM 경로)

    Args:
        pdf_path: PDF 파일 절대 경로

    Returns:
        True if NotebookLM output detected, False otherwise.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        logger.warning(f"[notebooklm_adapter] PDF not found: {pdf_path}")
        return False

    # Strategy 1: pypdf 텍스트 레이어 스캔 (PyPDF2 fallback 포함)
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(pdf_path)

        # 첫 3페이지만 스캔 (성능)
        pages_to_scan = min(3, len(reader.pages))
        for i in range(pages_to_scan):
            try:
                text = reader.pages[i].extract_text() or ""
                for marker in NOTEBOOKLM_WATERMARK_MARKERS:
                    if marker in text:
                        logger.info(
                            f"[notebooklm_adapter] Detected NotebookLM via text layer "
                            f"(page {i+1}, marker='{marker}')"
                        )
                        return True
            except Exception as e:
                logger.debug(f"[notebooklm_adapter] Text extraction failed for page {i+1}: {e}")

        # Strategy 2: metadata Creator/Producer
        meta = reader.metadata
        if meta:
            creator = (meta.get("/Creator") or "") + (meta.get("/Producer") or "")
            if any(m in creator for m in NOTEBOOKLM_WATERMARK_MARKERS):
                logger.info(
                    f"[notebooklm_adapter] Detected NotebookLM via metadata "
                    f"(Creator/Producer='{creator}')"
                )
                return True

    except ImportError:
        logger.warning("[notebooklm_adapter] pypdf/PyPDF2 not available — skipping detection")
        return False
    except Exception as e:
        logger.warning(f"[notebooklm_adapter] Detection error: {e} — defaulting to False")
        return False

    logger.debug(f"[notebooklm_adapter] Not a NotebookLM PDF: {pdf_path}")
    return False


# ─────────────────────────────────────────────────────────────
# Crop 함수 (PIL 레벨, 단일 책임)
# ─────────────────────────────────────────────────────────────

def crop_watermark_pil(
    image: "Image.Image",
    width_ratio: float = WATERMARK_CROP_WIDTH_RATIO,
    height_ratio: float = WATERMARK_CROP_HEIGHT_RATIO,
    fill_color: Tuple[int, int, int] = WATERMARK_FILL_COLOR,
) -> "Image.Image":
    """
    PIL 이미지의 우측 하단 워터마크 영역을 fill_color로 덮음.

    **중요**: 이미지를 진짜로 crop(잘라내기)하지 않습니다.
    크기는 그대로 두고 우측 하단 박스를 색으로 채웁니다.
    → 기존 파이프라인(16:9 assumption)과 투명 호환.

    Args:
        image: PIL Image 객체
        width_ratio: 이미지 너비 대비 crop 영역 비율 (0.04 = 4%)
        height_ratio: 이미지 높이 대비 crop 영역 비율 (0.025 = 2.5%)
        fill_color: 채울 색상 RGB 튜플 (기본 white)

    Returns:
        워터마크가 제거된 새 PIL Image (원본 유지).
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("PIL/Pillow is not installed")

    width, height = image.size
    crop_w = int(width * width_ratio)
    crop_h = int(height * height_ratio)

    # 원본 복사 (부작용 방지)
    result = image.copy()

    # 우측 하단 박스 좌표
    left = width - crop_w
    top = height - crop_h
    right = width
    bottom = height

    # 흰색 박스로 덮음
    # RGBA 이미지 지원을 위해 mode 체크
    if result.mode == "RGBA":
        fill = (*fill_color, 255)
    elif result.mode == "L":
        fill = 255
    else:
        fill = fill_color

    # Image.new로 박스 생성 후 paste
    box = Image.new(result.mode, (crop_w, crop_h), fill)
    result.paste(box, (left, top))

    return result


# ─────────────────────────────────────────────────────────────
# 통합 엔트리포인트 (파일 경로 기반)
# ─────────────────────────────────────────────────────────────

def process_slide_image(
    image_path: str,
    output_path: Optional[str] = None,
) -> str:
    """
    슬라이드 이미지 파일 1개를 처리 (워터마크 제거).

    Args:
        image_path: 입력 이미지 경로
        output_path: 출력 경로 (None이면 원본 덮어쓰기)

    Returns:
        처리된 이미지의 경로.
    """
    if not PIL_AVAILABLE:
        logger.warning("[notebooklm_adapter] PIL not available — returning as-is")
        return image_path

    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    dst = Path(output_path) if output_path else src

    with Image.open(src) as img:
        processed = crop_watermark_pil(img)
        processed.save(str(dst))

    logger.debug(f"[notebooklm_adapter] Processed: {src.name} → {dst.name}")
    return str(dst)


def process_slides(
    image_paths: List[str],
    output_dir: Optional[str] = None,
) -> List[str]:
    """
    여러 슬라이드 이미지를 배치 처리.

    Args:
        image_paths: 입력 이미지 경로 리스트
        output_dir: 출력 디렉터리 (None이면 원본 덮어쓰기)

    Returns:
        처리된 이미지 경로 리스트.
    """
    results = []
    for img_path in image_paths:
        if output_dir:
            out = str(Path(output_dir) / Path(img_path).name)
        else:
            out = None
        processed = process_slide_image(img_path, out)
        results.append(processed)

    logger.info(f"[notebooklm_adapter] Processed {len(results)} slides")
    return results


# ─────────────────────────────────────────────────────────────
# Co-located Verifier (ISS-042 교훈)
# ─────────────────────────────────────────────────────────────

def verify_crop_applied(
    original_path: str,
    processed_path: str,
    tolerance: int = 5,
) -> bool:
    """
    Crop이 실제로 적용되었는지 검증.

    전략:
        1. 두 이미지 모두 로드
        2. 우측 하단 WATERMARK_CROP 영역 픽셀 샘플링
        3. processed가 fill_color에 가까우면 True

    Args:
        original_path: 원본 이미지 경로
        processed_path: 처리된 이미지 경로
        tolerance: RGB 채널별 허용 오차 (0~255)

    Returns:
        True if crop area is fill_color in processed, False otherwise.
    """
    if not PIL_AVAILABLE:
        return False

    try:
        with Image.open(processed_path) as img:
            if img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")

            width, height = img.size
            # 우측 하단 중앙 픽셀 샘플
            sample_x = width - int(width * WATERMARK_CROP_WIDTH_RATIO * 0.5)
            sample_y = height - int(height * WATERMARK_CROP_HEIGHT_RATIO * 0.5)

            pixel = img.getpixel((sample_x, sample_y))

            # fill color 비교
            if isinstance(pixel, int):  # L mode
                return abs(pixel - 255) <= tolerance
            elif len(pixel) >= 3:
                r, g, b = pixel[:3]
                fr, fg, fb = WATERMARK_FILL_COLOR
                return (
                    abs(r - fr) <= tolerance
                    and abs(g - fg) <= tolerance
                    and abs(b - fb) <= tolerance
                )
            return False

    except Exception as e:
        logger.warning(f"[notebooklm_adapter] Verify error: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# Public API — PDF 업로드 경로와 연결되는 통합 헬퍼
# ─────────────────────────────────────────────────────────────

def adapt_notebooklm_slides(
    pdf_path: str,
    image_paths: List[str],
    force: bool = False,
) -> Tuple[List[str], bool]:
    """
    PDF가 NotebookLM 출력이면 슬라이드 이미지들을 처리하고,
    아니면 no-op으로 그대로 반환.

    이 함수가 `pdf_to_slides_service.convert_pdf_to_images()` 직후에
    호출되는 표준 진입점입니다.

    Args:
        pdf_path: 원본 PDF 경로 (감지용)
        image_paths: pdf2image가 추출한 슬라이드 이미지 경로 리스트
        force: True면 감지 무시하고 강제 crop (테스트용)

    Returns:
        (processed_paths, was_notebooklm)
        - processed_paths: 처리된 (또는 그대로인) 이미지 경로 리스트
        - was_notebooklm: True면 NotebookLM으로 감지되어 처리됨
    """
    is_notebooklm = force or detect_notebooklm_pdf(pdf_path)

    if not is_notebooklm:
        logger.info(f"[notebooklm_adapter] Not NotebookLM PDF, passing through: {pdf_path}")
        return image_paths, False

    logger.info(
        f"[notebooklm_adapter] NotebookLM PDF detected — "
        f"removing watermark from {len(image_paths)} slides"
    )
    processed = process_slides(image_paths)
    return processed, True
