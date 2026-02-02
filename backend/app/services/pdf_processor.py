"""PDF 프로세서 - PDF를 이미지로 변환하고 OCR로 텍스트 추출"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import uuid

from pdf2image import convert_from_path
from PIL import Image
import pytesseract

from app.models.neo4j_models import SlideDataModel, PresentationModel
from app.services.neo4j_client import get_neo4j_client


logger = logging.getLogger(__name__)


class PDFProcessorError(Exception):
    """PDF 프로세서 에러"""
    pass


class PDFProcessor:
    """PDF 처리 및 OCR 텍스트 추출"""

    def __init__(self, output_dir: str = "/app/outputs/slides"):
        """
        Args:
            output_dir: 슬라이드 이미지 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.neo4j_client = get_neo4j_client()

    async def process_pdf(
        self,
        pdf_path: str,
        project_id: str,
        dpi: int = 200,
        lang: str = "kor+eng"
    ) -> Dict[str, Any]:
        """
        PDF 처리 메인 함수

        Args:
            pdf_path: PDF 파일 경로
            project_id: 프로젝트 ID
            dpi: 이미지 변환 DPI (기본: 200)
            lang: OCR 언어 (기본: kor+eng)

        Returns:
            {
                "presentation_id": str,
                "project_id": str,
                "pdf_filename": str,
                "total_slides": int,
                "slides": [SlideDataModel, ...]
            }

        Raises:
            PDFProcessorError: PDF 처리 실패 시
        """
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise PDFProcessorError(f"PDF 파일이 존재하지 않습니다: {pdf_path}")

            # 프레젠테이션 ID 생성
            presentation_id = f"pres_{uuid.uuid4().hex[:12]}"
            presentation_dir = self.output_dir / presentation_id
            presentation_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"PDF 처리 시작: {pdf_file.name} (project_id={project_id})")

            # 1. PDF → 이미지 변환
            image_paths = self.pdf_to_images(
                pdf_path=str(pdf_file),
                output_dir=str(presentation_dir),
                dpi=dpi
            )

            logger.info(f"PDF → 이미지 변환 완료: {len(image_paths)}장")

            # 2. 각 이미지에서 OCR 텍스트 추출
            slides_data = []
            for idx, img_path in enumerate(image_paths, start=1):
                slide_data = self._process_slide(
                    image_path=img_path,
                    slide_number=idx,
                    lang=lang
                )
                slides_data.append(slide_data)

            logger.info(f"OCR 텍스트 추출 완료: {len(slides_data)}장")

            # 3. Neo4j에 저장
            presentation_model = PresentationModel(
                presentation_id=presentation_id,
                pdf_filename=pdf_file.name,
                total_slides=len(slides_data)
            )

            self._save_to_neo4j(
                project_id=project_id,
                presentation=presentation_model,
                slides=slides_data
            )

            logger.info(f"Neo4j 저장 완료: presentation_id={presentation_id}")

            return {
                "presentation_id": presentation_id,
                "project_id": project_id,
                "pdf_filename": pdf_file.name,
                "total_slides": len(slides_data),
                "slides": [slide.model_dump() for slide in slides_data]
            }

        except Exception as e:
            logger.error(f"PDF 처리 실패: {e}")
            raise PDFProcessorError(f"PDF 처리 중 오류 발생: {e}")

    def pdf_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        dpi: int = 200
    ) -> List[str]:
        """
        PDF → 이미지 변환

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 출력 디렉토리
            dpi: 변환 DPI

        Returns:
            변환된 이미지 파일 경로 리스트

        Raises:
            PDFProcessorError: 변환 실패 시
        """
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []

            for idx, image in enumerate(images, start=1):
                # PNG로 저장
                img_filename = f"slide_{idx:03d}.png"
                img_path = Path(output_dir) / img_filename

                # 이미지 최적화 (해상도 제한)
                optimized_img = self.optimize_image(image, max_width=1920)
                optimized_img.save(str(img_path), "PNG", optimize=True)

                image_paths.append(str(img_path))

            return image_paths

        except Exception as e:
            logger.error(f"PDF → 이미지 변환 실패: {e}")
            raise PDFProcessorError(f"PDF 변환 중 오류 발생: {e}")

    def extract_text_from_image(
        self,
        image_path: str,
        lang: str = "kor+eng"
    ) -> Dict[str, Any]:
        """
        OCR 텍스트 추출

        Args:
            image_path: 이미지 파일 경로
            lang: OCR 언어

        Returns:
            {
                "text": str,
                "confidence": float,
                "word_count": int
            }

        Raises:
            PDFProcessorError: OCR 실패 시
        """
        try:
            image = Image.open(image_path)

            # Tesseract OCR 실행
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                output_type=pytesseract.Output.DICT
            )

            # 신뢰도 계산 (평균)
            confidences = [
                float(conf) for conf in data['conf'] if conf != '-1'
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # 텍스트 추출
            text = pytesseract.image_to_string(image, lang=lang).strip()
            word_count = len(text.split()) if text else 0

            return {
                "text": text,
                "confidence": round(avg_confidence, 2),
                "word_count": word_count
            }

        except Exception as e:
            logger.warning(f"OCR 텍스트 추출 실패: {image_path} - {e}")
            # OCR 실패 시 기본값 반환
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0
            }

    def optimize_image(
        self,
        image: Image.Image,
        max_width: int = 1920
    ) -> Image.Image:
        """
        이미지 최적화 (해상도 제한)

        Args:
            image: PIL Image 객체
            max_width: 최대 너비 (픽셀)

        Returns:
            최적화된 PIL Image 객체
        """
        width, height = image.size

        if width > max_width:
            # 비율 유지하며 리사이즈
            ratio = max_width / width
            new_height = int(height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)

        return image

    def _process_slide(
        self,
        image_path: str,
        slide_number: int,
        lang: str = "kor+eng"
    ) -> SlideDataModel:
        """
        슬라이드 처리 (이미지 → OCR)

        Args:
            image_path: 이미지 파일 경로
            slide_number: 슬라이드 번호
            lang: OCR 언어

        Returns:
            SlideDataModel
        """
        ocr_result = self.extract_text_from_image(image_path, lang=lang)

        slide_data = SlideDataModel(
            slide_number=slide_number,
            image_path=image_path,
            extracted_text=ocr_result["text"],
            confidence=ocr_result["confidence"],
            word_count=ocr_result["word_count"]
        )

        return slide_data

    def _save_to_neo4j(
        self,
        project_id: str,
        presentation: PresentationModel,
        slides: List[SlideDataModel]
    ) -> None:
        """
        Neo4j에 프레젠테이션 및 슬라이드 데이터 저장

        Args:
            project_id: 프로젝트 ID
            presentation: 프레젠테이션 모델
            slides: 슬라이드 모델 리스트
        """
        # 1. 프레젠테이션 노드 생성 및 프로젝트 연결
        create_presentation_query = """
        MATCH (proj:Project {project_id: $project_id})
        CREATE (pres:Presentation {
            presentation_id: $presentation_id,
            pdf_filename: $pdf_filename,
            total_slides: $total_slides,
            created_at: datetime($created_at)
        })
        CREATE (proj)-[:HAS_PRESENTATION]->(pres)
        RETURN pres.presentation_id as presentation_id
        """

        self.neo4j_client.query(
            create_presentation_query,
            {
                "project_id": project_id,
                "presentation_id": presentation.presentation_id,
                "pdf_filename": presentation.pdf_filename,
                "total_slides": presentation.total_slides,
                "created_at": presentation.created_at.isoformat()
            }
        )

        # 2. 슬라이드 노드 생성 및 프레젠테이션 연결
        for slide in slides:
            create_slide_query = """
            MATCH (pres:Presentation {presentation_id: $presentation_id})
            CREATE (slide:Slide {
                slide_id: $slide_id,
                slide_number: $slide_number,
                image_path: $image_path,
                extracted_text: $extracted_text,
                confidence: $confidence,
                word_count: $word_count,
                created_at: datetime($created_at)
            })
            CREATE (pres)-[:HAS_SLIDE]->(slide)
            RETURN slide.slide_id as slide_id
            """

            self.neo4j_client.query(
                create_slide_query,
                {
                    "presentation_id": presentation.presentation_id,
                    "slide_id": slide.slide_id,
                    "slide_number": slide.slide_number,
                    "image_path": slide.image_path,
                    "extracted_text": slide.extracted_text,
                    "confidence": slide.confidence,
                    "word_count": slide.word_count,
                    "created_at": slide.created_at.isoformat()
                }
            )

    def get_presentation_slides(self, presentation_id: str) -> List[Dict[str, Any]]:
        """
        프레젠테이션의 모든 슬라이드 조회

        Args:
            presentation_id: 프레젠테이션 ID

        Returns:
            슬라이드 데이터 리스트
        """
        query = """
        MATCH (pres:Presentation {presentation_id: $presentation_id})-[:HAS_SLIDE]->(slide:Slide)
        RETURN slide.slide_id as slide_id,
               slide.slide_number as slide_number,
               slide.image_path as image_path,
               slide.extracted_text as extracted_text,
               slide.confidence as confidence,
               slide.word_count as word_count,
               slide.created_at as created_at
        ORDER BY slide.slide_number ASC
        """

        results = self.neo4j_client.query(query, {"presentation_id": presentation_id})

        # Neo4j DateTime을 Python datetime으로 변환
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()

        return results

    def get_project_presentations(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 프레젠테이션 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            프레젠테이션 데이터 리스트
        """
        query = """
        MATCH (proj:Project {project_id: $project_id})-[:HAS_PRESENTATION]->(pres:Presentation)
        RETURN pres.presentation_id as presentation_id,
               pres.pdf_filename as pdf_filename,
               pres.total_slides as total_slides,
               pres.created_at as created_at
        ORDER BY pres.created_at DESC
        """

        results = self.neo4j_client.query(query, {"project_id": project_id})

        # Neo4j DateTime을 Python datetime으로 변환
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()

        return results


# 싱글톤 인스턴스
_pdf_processor_instance = None


def get_pdf_processor() -> PDFProcessor:
    """PDFProcessor 싱글톤 인스턴스"""
    global _pdf_processor_instance
    if _pdf_processor_instance is None:
        _pdf_processor_instance = PDFProcessor()
    return _pdf_processor_instance
