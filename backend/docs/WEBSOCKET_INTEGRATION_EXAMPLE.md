# WebSocket 통합 예시

## Celery Task와 WebSocket 통합

### 1. 기본 패턴

```python
from celery import shared_task
from app.services.websocket_manager import get_websocket_manager
import asyncio

@shared_task(bind=True)
def my_long_running_task(self, project_id: str):
    """장시간 실행 작업"""
    manager = get_websocket_manager()

    # 헬퍼 함수: 진행률 브로드캐스트
    def broadcast(progress: float, message: str):
        asyncio.run(
            manager.broadcast_progress(
                project_id=project_id,
                task_name="my_task",
                progress=progress,
                status="in_progress",
                message=message
            )
        )

    try:
        # 단계 1
        broadcast(0.2, "Step 1: Initializing...")
        step1_result = do_step1()

        # 단계 2
        broadcast(0.5, "Step 2: Processing...")
        step2_result = do_step2(step1_result)

        # 단계 3
        broadcast(0.8, "Step 3: Finalizing...")
        final_result = do_step3(step2_result)

        # 완료
        asyncio.run(
            manager.broadcast_completion(
                project_id=project_id,
                task_name="my_task",
                result={"output": final_result}
            )
        )

        return final_result

    except Exception as e:
        # 에러 브로드캐스트
        asyncio.run(
            manager.broadcast_error(
                project_id=project_id,
                task_name="my_task",
                error=str(e)
            )
        )
        raise
```

### 2. Zero-Fault Audio Loop 통합

```python
from celery import shared_task
from app.services.websocket_manager import get_websocket_manager
from app.services.audio_correction_loop import AudioCorrectionLoop
import asyncio

@shared_task(bind=True)
def generate_verified_audio(
    self,
    project_id: str,
    script: str,
    voice_id: str
):
    """검증된 오디오 생성 (WebSocket 진행률 포함)"""
    manager = get_websocket_manager()
    loop = AudioCorrectionLoop()

    def on_progress(progress: float, message: str, metadata: dict = None):
        """진행률 콜백"""
        asyncio.run(
            manager.broadcast_progress(
                project_id=project_id,
                task_name="audio_generation",
                progress=progress,
                status="in_progress",
                message=message,
                metadata=metadata
            )
        )

    try:
        # TTS 생성 시작
        on_progress(0.1, "Generating TTS audio...")

        result = loop.generate_verified_audio(
            text=script,
            voice_id=voice_id,
            on_progress=on_progress  # 진행률 콜백 전달
        )

        # 완료
        asyncio.run(
            manager.broadcast_completion(
                project_id=project_id,
                task_name="audio_generation",
                result={
                    "audio_url": result["audio_url"],
                    "accuracy": result["accuracy"],
                    "attempts": result["attempts"]
                }
            )
        )

        return result

    except Exception as e:
        asyncio.run(
            manager.broadcast_error(
                project_id=project_id,
                task_name="audio_generation",
                error=str(e),
                details={"voice_id": voice_id}
            )
        )
        raise
```

### 3. 다단계 파이프라인 통합

```python
from celery import shared_task, chain
from app.services.websocket_manager import get_websocket_manager
import asyncio

@shared_task(bind=True)
def step1_script_generation(self, project_id: str, topic: str):
    """1단계: 스크립트 생성"""
    manager = get_websocket_manager()

    asyncio.run(
        manager.broadcast_progress(
            project_id=project_id,
            task_name="pipeline",
            progress=0.25,
            status="in_progress",
            message="Generating script..."
        )
    )

    script = generate_script(topic)
    return {"project_id": project_id, "script": script}


@shared_task(bind=True)
def step2_audio_generation(self, data: dict):
    """2단계: 오디오 생성"""
    project_id = data["project_id"]
    script = data["script"]
    manager = get_websocket_manager()

    asyncio.run(
        manager.broadcast_progress(
            project_id=project_id,
            task_name="pipeline",
            progress=0.5,
            status="in_progress",
            message="Generating audio..."
        )
    )

    audio_url = generate_audio(script)
    data["audio_url"] = audio_url
    return data


@shared_task(bind=True)
def step3_video_generation(self, data: dict):
    """3단계: 영상 생성"""
    project_id = data["project_id"]
    manager = get_websocket_manager()

    asyncio.run(
        manager.broadcast_progress(
            project_id=project_id,
            task_name="pipeline",
            progress=0.75,
            status="in_progress",
            message="Generating video..."
        )
    )

    video_url = generate_video(data["script"])
    data["video_url"] = video_url
    return data


@shared_task(bind=True)
def step4_lipsync(self, data: dict):
    """4단계: 립싱크"""
    project_id = data["project_id"]
    manager = get_websocket_manager()

    asyncio.run(
        manager.broadcast_progress(
            project_id=project_id,
            task_name="pipeline",
            progress=0.9,
            status="in_progress",
            message="Processing lipsync..."
        )
    )

    final_url = process_lipsync(data["video_url"], data["audio_url"])

    # 완료
    asyncio.run(
        manager.broadcast_completion(
            project_id=project_id,
            task_name="pipeline",
            result={"final_video_url": final_url}
        )
    )

    return {"final_video_url": final_url}


# FastAPI 엔드포인트
from fastapi import APIRouter

router = APIRouter()

@router.post("/projects/{project_id}/generate-video")
async def generate_video_endpoint(project_id: str, topic: str):
    """비디오 생성 파이프라인"""
    manager = get_websocket_manager()

    # 시작 알림
    await manager.broadcast_status(
        project_id=project_id,
        task_name="pipeline",
        status="queued",
        message="Video generation pipeline started"
    )

    # Celery 체인 실행
    workflow = chain(
        step1_script_generation.s(project_id, topic),
        step2_audio_generation.s(),
        step3_video_generation.s(),
        step4_lipsync.s()
    )

    task = workflow.apply_async()

    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Connect to WebSocket for real-time updates",
        "websocket_url": f"ws://localhost:8000/api/v1/ws/projects/{project_id}/stream"
    }
```

### 4. AudioCorrectionLoop 수정 예시

`app/services/audio_correction_loop.py`에 진행률 콜백 추가:

```python
class AudioCorrectionLoop:
    def generate_verified_audio(
        self,
        text: str,
        voice_id: str,
        max_attempts: int = 5,
        target_accuracy: float = 0.95,
        on_progress: callable = None  # 추가
    ):
        """검증된 오디오 생성

        Args:
            on_progress: 진행률 콜백 (progress, message, metadata)
        """
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            if on_progress:
                on_progress(
                    progress=0.2 + (attempts / max_attempts) * 0.6,
                    message=f"Generating audio (attempt {attempts}/{max_attempts})...",
                    metadata={"attempt": attempts}
                )

            # TTS 생성
            audio_url = self.tts_service.generate(text, voice_id)

            if on_progress:
                on_progress(
                    progress=0.2 + (attempts / max_attempts) * 0.6 + 0.1,
                    message=f"Verifying audio (attempt {attempts})...",
                    metadata={"attempt": attempts}
                )

            # STT 검증
            transcribed = self.stt_service.transcribe(audio_url)
            accuracy = self._calculate_accuracy(text, transcribed)

            if on_progress:
                on_progress(
                    progress=0.2 + (attempts / max_attempts) * 0.6 + 0.2,
                    message=f"Accuracy: {accuracy * 100:.1f}%",
                    metadata={"attempt": attempts, "accuracy": accuracy}
                )

            if accuracy >= target_accuracy:
                return {
                    "audio_url": audio_url,
                    "accuracy": accuracy,
                    "attempts": attempts
                }

        raise Exception(f"Failed to generate accurate audio after {max_attempts} attempts")
```

### 5. Frontend 통합 (Next.js)

```jsx
// components/VideoGenerationProgress.jsx
import { useProjectWebSocket } from '../hooks/useProjectWebSocket';
import { useState } from 'react';

export default function VideoGenerationProgress({ projectId }) {
  const { isConnected, progress, status, error, ws } = useProjectWebSocket(projectId);
  const [messages, setMessages] = useState([]);

  // 모든 이벤트 수신
  if (ws) {
    ws.on('*', (data) => {
      setMessages(prev => [...prev, data]);
    });
  }

  return (
    <div className="video-progress-container">
      {/* 연결 상태 */}
      <div className="connection-badge">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {/* 진행률 바 */}
      <div className="progress-bar-container">
        <div
          className="progress-bar"
          style={{
            width: `${progress * 100}%`,
            backgroundColor: error ? 'red' : 'blue'
          }}
        />
        <span className="progress-text">
          {Math.round(progress * 100)}%
        </span>
      </div>

      {/* 현재 상태 */}
      <div className="current-status">
        <strong>Status:</strong> {status}
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {/* 이벤트 로그 */}
      <div className="event-log">
        <h3>Event Log</h3>
        <ul>
          {messages.slice(-10).reverse().map((msg, idx) => (
            <li key={idx}>
              <span className="timestamp">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
              <span className="event-type">{msg.type}</span>
              <span className="message">{msg.message}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

### 6. 페이지에서 사용

```jsx
// pages/projects/[id].jsx
import { useRouter } from 'next/router';
import VideoGenerationProgress from '../../components/VideoGenerationProgress';
import { useState } from 'react';

export default function ProjectPage() {
  const router = useRouter();
  const { id: projectId } = router.query;
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/projects/${projectId}/generate-video`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic: 'AI 트렌드 2026' })
        }
      );

      const data = await response.json();
      console.log('Task started:', data.task_id);
    } catch (error) {
      console.error('Failed to start generation:', error);
      setIsGenerating(false);
    }
  };

  return (
    <div className="project-page">
      <h1>Project: {projectId}</h1>

      {!isGenerating && (
        <button onClick={handleGenerate}>
          🎬 Generate Video
        </button>
      )}

      {isGenerating && (
        <VideoGenerationProgress projectId={projectId} />
      )}
    </div>
  );
}
```

## 디버깅 팁

### 1. 연결 확인

```bash
# WebSocket 연결 테스트
python test_websocket.py my_project

# 활성 연결 확인
curl http://localhost:8000/api/v1/ws/projects/my_project/connections
```

### 2. 수동 이벤트 전송 (테스트용)

```python
# test_manual_broadcast.py
import asyncio
from app.services.websocket_manager import get_websocket_manager

async def test_broadcast():
    manager = get_websocket_manager()

    # 진행률 전송
    await manager.broadcast_progress(
        project_id="test_project",
        task_name="manual_test",
        progress=0.5,
        status="in_progress",
        message="Manual test message"
    )

if __name__ == "__main__":
    asyncio.run(test_broadcast())
```

### 3. 로그 확인

```python
import logging

# WebSocket Manager 로그 활성화
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.services.websocket_manager")
logger.setLevel(logging.DEBUG)
```

## 주의사항

1. **asyncio.run()**: Celery worker에서는 새로운 이벤트 루프를 생성하므로 `asyncio.run()` 사용
2. **에러 처리**: 모든 브로드캐스트는 try-except로 감싸기 (WebSocket 에러로 인한 작업 실패 방지)
3. **메모리 누수**: 연결이 끊긴 클라이언트는 자동으로 정리됨
4. **스케일링**: 여러 서버 인스턴스에서는 Redis Pub/Sub 사용 필요
