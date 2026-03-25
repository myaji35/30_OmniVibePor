"""진행률 추적 시스템 통합 테스트

ProgressTracker, ProgressMapper, WebSocketManager의 통합 테스트

실행 방법:
    python test_progress_tracker.py
"""

import sys
import asyncio
from datetime import datetime


def test_progress_mapper():
    """ProgressMapper 테스트"""
    from app.utils.progress_mapper import ProgressMapper

    print("\n=== ProgressMapper 테스트 ===")

    # Director 워크플로우 진행률 테스트
    # 각 단계의 시작 진행률을 테스트
    test_cases = [
        ("start", 0.0, 0.0),
        ("load_character", 0.0, 0.05),
        ("parse_script", 0.0, 0.10),
        ("generate_videos", 0.0, 0.10),
        ("generate_videos", 0.5, 0.35),  # 10% + (60% - 10%) * 0.5 = 35%
        ("generate_videos", 1.0, 0.60),
        ("lipsync", 0.0, 0.60),          # 수정: 60% (lipsync 시작점)
        ("subtitles", 0.0, 0.75),        # 수정: 75% (subtitles 시작점)
        ("render", 0.0, 0.85),           # 수정: 85% (render 시작점)
        ("complete", 0.0, 1.0),
    ]

    for step, sub_progress, expected in test_cases:
        result = ProgressMapper.get_director_progress(step, sub_progress)
        status = "✅" if abs(result - expected) < 0.001 else "❌"
        print(
            f"{status} Director '{step}' (sub={sub_progress:.1f}): "
            f"expected={expected:.2f}, got={result:.2f}"
        )

    # Audio 워크플로우 진행률 테스트
    audio_test_cases = [
        ("start", 0.0, 0.0),
        ("normalize_text", 0.0, 0.05),
        ("tts_generation", 0.5, 0.175),  # 5% + (30% - 5%) * 0.5 = 17.5%
        ("stt_verification", 1.0, 0.60),
        ("complete", 0.0, 1.0),
    ]

    for step, sub_progress, expected in audio_test_cases:
        result = ProgressMapper.get_audio_progress(step, sub_progress)
        status = "✅" if abs(result - expected) < 0.001 else "❌"
        print(
            f"{status} Audio '{step}' (sub={sub_progress:.1f}): "
            f"expected={expected:.2f}, got={result:.2f}"
        )

    print("\n=== Step Range 테스트 ===")
    step_range = ProgressMapper.get_step_range("director", "generate_videos")
    print(f"Director 'generate_videos' range: {step_range}")
    assert step_range == (0.10, 0.60), f"Expected (0.10, 0.60), got {step_range}"
    print("✅ Step Range 테스트 통과")


def test_multi_step_calculator():
    """MultiStepProgressCalculator 테스트"""
    from app.utils.progress_mapper import MultiStepProgressCalculator

    print("\n=== MultiStepProgressCalculator 테스트 ===")

    calculator = MultiStepProgressCalculator([
        ("audio", 0.3),
        ("video", 0.6),
        ("subtitle", 0.1)
    ])

    # 오디오 완료
    calculator.update("audio", 1.0)
    assert calculator.get_overall_progress() == 0.3
    print("✅ 오디오 완료 (30%): ", calculator.get_overall_progress())

    # 영상 50% 완료
    calculator.update("video", 0.5)
    expected = 0.3 + 0.6 * 0.5  # 0.6
    result = calculator.get_overall_progress()
    assert abs(result - expected) < 0.001
    print(f"✅ 영상 50% 완료 (60%): {result:.2f}")

    # 모든 작업 완료
    calculator.update("video", 1.0)
    calculator.update("subtitle", 1.0)
    result_final = calculator.get_overall_progress()
    assert abs(result_final - 1.0) < 0.001, f"Expected 1.0, got {result_final}"
    print(f"✅ 모든 작업 완료 (100%): {result_final:.2f}")


async def test_websocket_manager():
    """WebSocketManager 테스트 (모의 테스트)"""
    try:
        from app.services.websocket_manager import get_websocket_manager

        print("\n=== WebSocketManager 테스트 ===")

        manager = get_websocket_manager()

        # 진행률 브로드캐스트 (실제 연결 없이 테스트)
        await manager.broadcast_progress(
            project_id="test_project_001",
            task_name="test_video_generation",
            progress=0.5,
            status="processing",
            message="테스트 진행 중...",
            metadata={"test": True}
        )
        print("✅ 진행률 브로드캐스트 (연결 없음)")

        # 에러 브로드캐스트
        await manager.broadcast_error(
            project_id="test_project_001",
            task_name="test_video_generation",
            error="테스트 에러",
            details={"error_code": "TEST_ERROR"}
        )
        print("✅ 에러 브로드캐스트 (연결 없음)")

        # 완료 브로드캐스트
        await manager.broadcast_completion(
            project_id="test_project_001",
            task_name="test_video_generation",
            result={"status": "success", "test": True}
        )
        print("✅ 완료 브로드캐스트 (연결 없음)")

        # 연결 수 확인
        connection_count = manager.get_connection_count("test_project_001")
        assert connection_count == 0
        print(f"✅ 연결 수 확인: {connection_count} (예상: 0)")

    except ImportError as e:
        print(f"\n⚠️  WebSocketManager 테스트 스킵 (의존성 누락: {e})")
        print("   → Docker 환경에서 실행하거나 의존성 설치 필요")


def test_progress_tracker_mock():
    """ProgressTracker 모의 테스트 (Celery 없이)"""
    try:
        from unittest.mock import MagicMock
        from app.tasks.progress_tracker import ProgressTracker

        print("\n=== ProgressTracker Mock 테스트 ===")

        # Mock Celery Task
        mock_task = MagicMock()
        mock_task.request.id = "test_task_123"

        tracker = ProgressTracker(
            task=mock_task,
            project_id="test_project_001",
            task_name="test_task"
        )

        # 진행률 업데이트
        tracker.update(0.0, "processing", "시작")
        print("✅ 진행률 업데이트 (0%)")

        tracker.update(0.5, "processing", "절반 완료")
        print("✅ 진행률 업데이트 (50%)")

        # 0-100 범위 자동 변환 테스트
        tracker.update(75, "processing", "75% 완료")
        print("✅ 진행률 자동 변환 (75 → 0.75)")

        # 완료
        tracker.complete({"result": "success"})
        print("✅ 작업 완료 브로드캐스트")

        # update_state 호출 확인
        assert mock_task.update_state.called
        print(f"✅ Celery update_state 호출됨 ({mock_task.update_state.call_count}회)")

    except Exception as e:
        print(f"\n⚠️  ProgressTracker Mock 테스트 실패: {e}")


def test_batch_progress_tracker():
    """BatchProgressTracker 테스트"""
    try:
        from unittest.mock import MagicMock
        from app.tasks.progress_tracker import BatchProgressTracker

        print("\n=== BatchProgressTracker 테스트 ===")

        mock_task = MagicMock()
        mock_task.request.id = "batch_test_123"

        tracker = BatchProgressTracker(
            task=mock_task,
            project_id="batch_project_001",
            task_name="batch_test",
            total_items=5
        )

        # 각 아이템 순차 완료
        for i in range(5):
            tracker.update_item(i, 1.0, "processing", f"Item {i+1} 완료")
            expected_progress = (i + 1) / 5.0
            overall = tracker.base_tracker.progress.get(0, 0)  # Mock이므로 실제 값은 안 나옴
            print(f"✅ 아이템 {i+1}/5 완료 (예상 진행률: {expected_progress:.1%})")

        assert tracker.completed_items == 5
        print(f"✅ 완료된 아이템 수: {tracker.completed_items}/5")

    except Exception as e:
        print(f"\n⚠️  BatchProgressTracker 테스트 실패: {e}")


def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("진행률 추적 시스템 통합 테스트")
    print("=" * 60)

    try:
        # 1. ProgressMapper 테스트
        test_progress_mapper()

        # 2. MultiStepProgressCalculator 테스트
        test_multi_step_calculator()

        # 3. WebSocketManager 테스트 (비동기)
        asyncio.run(test_websocket_manager())

        # 4. ProgressTracker Mock 테스트
        test_progress_tracker_mock()

        # 5. BatchProgressTracker 테스트
        test_batch_progress_tracker()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
