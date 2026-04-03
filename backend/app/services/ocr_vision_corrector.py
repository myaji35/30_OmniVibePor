"""OCR Vision Corrector — GPT-4 Vision으로 Tesseract OCR 결과 보정"""
import base64
import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OCRVisionCorrector:
    """
    Tesseract OCR 결과를 GPT-4 Vision으로 보정.

    사용 시나리오:
    - Tesseract OCR confidence가 낮을 때 (< 70%)
    - 한글/영문 혼합 슬라이드
    - 도표/차트 내 텍스트 인식
    """

    # confidence 이 값 이하일 때만 Vision 보정 실행
    CORRECTION_THRESHOLD = 70.0

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def correct_ocr(
        self,
        image_path: str,
        tesseract_text: str,
        tesseract_confidence: float,
        force: bool = False,
    ) -> dict:
        """
        OCR 결과를 GPT-4 Vision으로 보정.

        Args:
            image_path: 슬라이드 이미지 경로
            tesseract_text: Tesseract OCR 결과 텍스트
            tesseract_confidence: Tesseract 신뢰도 (0~100)
            force: True이면 신뢰도 무관하게 강제 보정

        Returns:
            {"text": str, "confidence": float, "corrected": bool, "method": str}
        """
        # 신뢰도가 충분하면 Tesseract 결과 그대로 반환
        if not force and tesseract_confidence >= self.CORRECTION_THRESHOLD:
            return {
                "text": tesseract_text,
                "confidence": tesseract_confidence,
                "corrected": False,
                "method": "tesseract",
            }

        # 이미지를 base64로 인코딩
        img_path = Path(image_path)
        if not img_path.exists():
            logger.warning(f"Image not found: {image_path}")
            return {
                "text": tesseract_text,
                "confidence": tesseract_confidence,
                "corrected": False,
                "method": "tesseract",
            }

        try:
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            ext = img_path.suffix.lower().lstrip(".")
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "이 슬라이드 이미지에서 모든 텍스트를 정확하게 추출하세요. "
                            "제목, 본문, 목록, 도표 내 텍스트, 차트 레이블을 모두 포함합니다. "
                            "원본 레이아웃 순서를 유지하고, 줄바꿈은 \\n으로 구분하세요. "
                            "텍스트만 출력하세요. 설명이나 주석은 포함하지 마세요."
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{img_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"참고용 Tesseract OCR 결과 (신뢰도 {tesseract_confidence:.0f}%):\n"
                                    f"{tesseract_text}\n\n"
                                    "위 OCR 결과를 이미지와 비교하여 정확한 텍스트를 추출해 주세요."
                                ),
                            },
                        ],
                    },
                ],
                max_tokens=2000,
                temperature=0.1,
            )

            corrected_text = response.choices[0].message.content.strip()

            logger.info(
                f"OCR Vision correction: {len(tesseract_text)} → {len(corrected_text)} chars "
                f"(confidence {tesseract_confidence:.0f}% → Vision)"
            )

            return {
                "text": corrected_text,
                "confidence": 95.0,  # Vision 보정 후 추정 신뢰도
                "corrected": True,
                "method": "gpt4-vision",
            }

        except Exception as e:
            logger.warning(f"GPT-4 Vision OCR correction failed: {e}")
            return {
                "text": tesseract_text,
                "confidence": tesseract_confidence,
                "corrected": False,
                "method": "tesseract",
            }


# 싱글턴
_corrector: Optional[OCRVisionCorrector] = None


def get_ocr_corrector() -> OCRVisionCorrector:
    global _corrector
    if _corrector is None:
        _corrector = OCRVisionCorrector()
    return _corrector
