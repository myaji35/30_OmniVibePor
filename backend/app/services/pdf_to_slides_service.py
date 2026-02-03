"""PDF to Slides 변환 서비스"""
from typing import List, Dict
from pathlib import Path
import asyncio
import hashlib
import time
from pdf2image import convert_from_path
# Logfire는 optional
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()


class PDFToSlidesService:
    """
import logging
    PDF를 개별 슬라이드 이미지로 변환

    특징:
    - NotebookLM PDF 지원
    - 고해상도 PNG 출력 (1920x1080)
    - 슬라이드별 이미지 파일 생성
    - 메타데이터 추출 (총 페이지 수 등)
    """

    def __init__(self, output_dir: str = "./outputs/slides"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def convert_pdf_to_images(
        self,
        pdf_path: str,
        dpi: int = 300,
        format: str = "PNG"
    ) -> List[str]:
        """
        PDF를 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            dpi: 해상도 (기본값: 300)
            format: 출력 형식 (PNG, JPEG)

        Returns:
            이미지 파일 경로 리스트
            ["slide_1.png", "slide_2.png", ...]
        """
        with self.logger.span("pdf2image.convert") as span:
            pdf_file = Path(pdf_path)

            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # 파일명 해시 (충돌 방지)
            file_hash = hashlib.md5(pdf_path.encode()).hexdigest()[:8]
            timestamp = int(time.time())

            span.set_attribute("pdf_file", pdf_path)
            span.set_attribute("dpi", dpi)

            # PDF → 이미지 변환 (동기 작업을 비동기로 실행)
            images = await asyncio.to_thread(
                convert_from_path,
                pdf_path,
                dpi=dpi,
                fmt=format.lower()
            )

            total_pages = len(images)
            span.set_attribute("total_pages", total_pages)

            self.logger.info(f"Converted {total_pages} pages from PDF")

            # 이미지 저장
            image_paths = []
            for i, image in enumerate(images, start=1):
                filename = f"slide_{timestamp}_{file_hash}_{i:03d}.png"
                file_path = self.output_dir / filename

                # 이미지 저장 (비동기)
                await asyncio.to_thread(
                    image.save,
                    str(file_path),
                    format
                )

                image_paths.append(str(file_path))

                self.logger.info(f"Saved slide {i}/{total_pages}: {file_path}")

            return image_paths

    async def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """
        PDF 메타데이터 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            {
                "total_pages": 10,
                "file_size_mb": 2.5,
                "filename": "presentation.pdf"
            }
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        file_size_mb = pdf_file.stat().st_size / 1024 / 1024

        # 페이지 수 확인 (간단한 변환으로 확인)
        images = await asyncio.to_thread(
            convert_from_path,
            pdf_path,
            dpi=72,  # 낮은 DPI로 빠르게 확인
            last_page=1  # 첫 페이지만
        )

        # 실제 총 페이지 수는 PyPDF2로 확인하는 것이 더 빠름
        try:
            from PyPDF2 import PdfReader
            reader = await asyncio.to_thread(PdfReader, pdf_path)
            total_pages = len(reader.pages)
        except Exception:
            # PyPDF2 실패 시 pdf2image로 fallback
            images = await asyncio.to_thread(convert_from_path, pdf_path, dpi=72)
            total_pages = len(images)

        return {
            "total_pages": total_pages,
            "file_size_mb": round(file_size_mb, 2),
            "filename": pdf_file.name
        }

    async def save_uploaded_pdf(
        self,
        file_data: bytes,
        user_id: str,
        original_filename: str
    ) -> str:
        """
        업로드된 PDF 파일 저장

        Args:
            file_data: PDF 파일 바이트
            user_id: 사용자 ID
            original_filename: 원본 파일명

        Returns:
            저장된 파일 경로
        """
        # 파일명 생성
        timestamp = int(time.time())
        file_hash = hashlib.md5(file_data).hexdigest()[:8]
        filename = f"{user_id}_{timestamp}_{file_hash}.pdf"

        # PDF 저장 디렉토리
        pdf_dir = Path("./uploads/pdfs")
        pdf_dir.mkdir(parents=True, exist_ok=True)

        file_path = pdf_dir / filename

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(file_data)

        self.logger.info(f"Saved PDF: {file_path} ({len(file_data) / 1024:.2f} KB)")

        return str(file_path)


# 싱글톤 인스턴스
_pdf_to_slides_service_instance = None


def get_pdf_to_slides_service() -> PDFToSlidesService:
    """PDF to Slides 서비스 싱글톤 인스턴스"""
    global _pdf_to_slides_service_instance
    if _pdf_to_slides_service_instance is None:
        _pdf_to_slides_service_instance = PDFToSlidesService()
    return _pdf_to_slides_service_instance
