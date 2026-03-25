"""섹션 API 테스트 스크립트

콘티 섹션 API의 기본 동작을 검증합니다.
"""
import sys
import uuid


def test_section_models():
    """Pydantic 모델 임포트 및 생성 테스트"""
    print("=" * 60)
    print("1. Pydantic 모델 테스트")
    print("=" * 60)

    try:
        from app.models.neo4j_models import (
            SectionType,
            SectionModel,
            SectionDetailModel,
            SectionMetadataModel,
            ProjectSectionsResponse
        )

        # SectionType 테스트
        print("✓ SectionType enum 임포트 성공")
        assert SectionType.HOOK.value == "hook"
        assert SectionType.BODY.value == "body"
        assert SectionType.CTA.value == "cta"
        print("✓ SectionType 값 검증 성공")

        # SectionModel 테스트
        section = SectionModel(
            type=SectionType.HOOK,
            order=0,
            script="안녕하세요! 오늘은 AI 영상 제작에 대해 알려드리겠습니다.",
            start_time=0.0,
            end_time=5.0,
            duration=5.0
        )
        print(f"✓ SectionModel 생성 성공: {section.section_id}")

        # SectionMetadataModel 테스트
        metadata = SectionMetadataModel(
            word_count=15,
            estimated_duration=5.0,
            actual_duration=5.2
        )
        print("✓ SectionMetadataModel 생성 성공")

        # SectionDetailModel 테스트
        detail = SectionDetailModel(
            section_id=section.section_id,
            type=section.type,
            order=section.order,
            script=section.script,
            start_time=section.start_time,
            end_time=section.end_time,
            duration=section.duration,
            metadata=metadata
        )
        print(f"✓ SectionDetailModel 생성 성공: {detail.section_id}")

        # ProjectSectionsResponse 테스트
        response = ProjectSectionsResponse(
            project_id="proj_test123",
            sections=[detail],
            total_duration=5.2
        )
        print(f"✓ ProjectSectionsResponse 생성 성공: {response.project_id}")

        print("\n✅ 모델 테스트 완료\n")
        return True

    except Exception as e:
        print(f"\n❌ 모델 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_section_service():
    """섹션 서비스 임포트 테스트"""
    print("=" * 60)
    print("2. 섹션 서비스 테스트")
    print("=" * 60)

    try:
        from app.services.section_service import SectionService, get_section_service
        print("✓ SectionService 임포트 성공")

        # 서비스 클래스 메서드 확인
        assert hasattr(SectionService, "get_project_sections")
        assert hasattr(SectionService, "create_section")
        assert hasattr(SectionService, "update_section_media")
        assert hasattr(SectionService, "generate_section_thumbnail")
        assert hasattr(SectionService, "delete_section")
        print("✓ SectionService 메서드 확인 완료")

        print("\n✅ 서비스 테스트 완료\n")
        return True

    except Exception as e:
        print(f"\n❌ 서비스 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """API 라우트 임포트 테스트"""
    print("=" * 60)
    print("3. API 라우트 테스트")
    print("=" * 60)

    try:
        from app.api.v1.projects import (
            get_project_sections,
            create_project_section,
            update_section_media,
            SectionCreateRequest,
            SectionMediaUpdateRequest
        )
        print("✓ API 라우트 함수 임포트 성공")

        # Request 모델 테스트
        from app.models.neo4j_models import SectionType

        create_request = SectionCreateRequest(
            type=SectionType.HOOK,
            order=0,
            script="테스트 스크립트",
            start_time=0.0,
            end_time=5.0,
            word_count=10,
            estimated_duration=5.0
        )
        print("✓ SectionCreateRequest 생성 성공")

        media_request = SectionMediaUpdateRequest(
            video_clip_path="/path/to/clip.mp4",
            thumbnail_url="https://example.com/thumb.jpg"
        )
        print("✓ SectionMediaUpdateRequest 생성 성공")

        print("\n✅ API 라우트 테스트 완료\n")
        return True

    except Exception as e:
        print(f"\n❌ API 라우트 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_neo4j_schema():
    """Neo4j 스키마 업데이트 확인"""
    print("=" * 60)
    print("4. Neo4j 스키마 테스트")
    print("=" * 60)

    try:
        from app.services.neo4j_client import Neo4jClient
        print("✓ Neo4jClient 임포트 성공")

        # create_full_schema 메서드 확인
        assert hasattr(Neo4jClient, "create_full_schema")
        print("✓ create_full_schema 메서드 확인 완료")

        print("\n✅ Neo4j 스키마 테스트 완료\n")
        return True

    except Exception as e:
        print(f"\n❌ Neo4j 스키마 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 60)
    print("콘티 섹션 API 테스트 시작")
    print("=" * 60 + "\n")

    results = []

    # 각 테스트 실행
    results.append(("모델 테스트", test_section_models()))
    results.append(("서비스 테스트", test_section_service()))
    results.append(("API 라우트 테스트", test_api_routes()))
    results.append(("Neo4j 스키마 테스트", test_neo4j_schema()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "-" * 60)
    print(f"총 {passed}/{total} 테스트 통과")
    print("=" * 60 + "\n")

    if passed == total:
        print("🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
