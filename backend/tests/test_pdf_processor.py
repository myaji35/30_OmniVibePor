"""PDFProcessor 테스트 스크립트"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_processor import PDFProcessor, PDFProcessorError


async def test_pdf_processor():
    """PDFProcessor 기본 동작 테스트"""
    print("=" * 60)
    print("PDFProcessor 테스트 시작")
    print("=" * 60)

    # PDFProcessor 인스턴스 생성
    processor = PDFProcessor(output_dir="/tmp/omnivibe_test_slides")
    print(f"✅ PDFProcessor 인스턴스 생성 완료")
    print(f"   출력 디렉토리: {processor.output_dir}")

    # 테스트 PDF 파일 경로 (실제 PDF 파일이 있어야 함)
    test_pdf_path = "/tmp/test_presentation.pdf"
    test_project_id = "proj_test123"

    if not Path(test_pdf_path).exists():
        print(f"\n⚠️  테스트 PDF 파일이 없습니다: {test_pdf_path}")
        print(f"   테스트를 위해 PDF 파일을 {test_pdf_path}에 배치해주세요.")
        print("\n✅ PDFProcessor 클래스 로드 및 초기화 테스트 성공")
        return

    try:
        # PDF 처리 실행
        print(f"\n📄 PDF 처리 시작...")
        result = await processor.process_pdf(
            pdf_path=test_pdf_path,
            project_id=test_project_id,
            dpi=150  # 테스트용으로 낮은 DPI 사용
        )

        print(f"\n✅ PDF 처리 완료!")
        print(f"   Presentation ID: {result['presentation_id']}")
        print(f"   PDF 파일명: {result['pdf_filename']}")
        print(f"   총 슬라이드 수: {result['total_slides']}")

        # 슬라이드 정보 출력
        print(f"\n📊 슬라이드 정보:")
        for slide in result['slides']:
            print(f"   - 슬라이드 {slide['slide_number']}: "
                  f"텍스트 {slide['word_count']}단어, "
                  f"신뢰도 {slide['confidence']:.1f}%")
            if slide['extracted_text']:
                preview = slide['extracted_text'][:50]
                print(f"     미리보기: {preview}...")

        # Neo4j 조회 테스트
        print(f"\n🔍 Neo4j에서 프레젠테이션 조회 중...")
        presentations = processor.get_project_presentations(test_project_id)
        print(f"   조회된 프레젠테이션 수: {len(presentations)}")

        if presentations:
            pres_id = presentations[0]['presentation_id']
            slides = processor.get_presentation_slides(pres_id)
            print(f"   조회된 슬라이드 수: {len(slides)}")

    except PDFProcessorError as e:
        print(f"\n❌ PDF 처리 실패: {e}")
        return
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("✅ PDFProcessor 테스트 완료!")
    print("=" * 60)


def test_imports():
    """모듈 import 테스트"""
    print("=" * 60)
    print("모듈 import 테스트")
    print("=" * 60)

    try:
        from app.models.neo4j_models import SlideDataModel, PresentationModel
        print("✅ Pydantic 모델 import 성공")

        from app.services.pdf_processor import PDFProcessor, get_pdf_processor
        print("✅ PDFProcessor import 성공")

        from pdf2image import convert_from_path
        print("✅ pdf2image import 성공")

        from PIL import Image
        print("✅ Pillow import 성공")

        import pytesseract
        print("✅ pytesseract import 성공")

        # Tesseract 설치 확인
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract 버전: {version}")
        except Exception as e:
            print(f"⚠️  Tesseract 실행 파일 확인 실패: {e}")
            print(f"   Tesseract OCR이 시스템에 설치되어 있어야 합니다.")

        print("\n" + "=" * 60)
        print("✅ 모든 모듈 import 성공!")
        print("=" * 60)

    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 1. Import 테스트
    test_imports()

    print("\n")

    # 2. PDFProcessor 동작 테스트
    asyncio.run(test_pdf_processor())
