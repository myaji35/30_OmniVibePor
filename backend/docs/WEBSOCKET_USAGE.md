# WebSocket 실시간 진행 상태 시스템

## 개요

OmniVibe Pro는 WebSocket을 통해 프로젝트 작업의 실시간 진행 상태를 클라이언트에 브로드캐스트합니다.

## 아키텍처

```
┌──────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Frontend   │◄────────┤ ConnectionManager├─────────┤ Celery Task │
│  (Next.js)   │ WebSocket└──────────────────┘         │   Worker    │
└──────────────┘                   │                   └─────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │  project_id: {    │
                         │    ws1, ws2, ws3  │
                         │  }                │
                         └───────────────────┘
```

**핵심 구조**:
- `ConnectionManager`: 프로젝트별 WebSocket 연결 관리
- 프로젝트 ID 기반 브로드캐스트 (같은 프로젝트의 모든 클라이언트에게 전송)
- 싱글톤 패턴으로 전역 상태 관리

## 엔드포인트

### 1. WebSocket 연결

```
ws://localhost:8000/api/v1/ws/projects/{project_id}/stream
```

**파라미터**:
- `project_id`: 프로젝트 고유 ID (예: `campaign_001`)

**이벤트 타입**:

| 타입 | 설명 | 필드 |
|------|------|------|
| `connected` | 연결 성공 | `project_id`, `message` |
| `progress` | 진행률 업데이트 | `task_name`, `progress`, `status`, `message`, `metadata` |
| `status` | 작업 상태 변경 | `task_name`, `status`, `message`, `metadata` |
| `error` | 에러 발생 | `task_name`, `error`, `details` |
| `completed` | 작업 완료 | `task_name`, `result` |
| `pong` | Keep-alive 응답 | - |

### 2. 활성 연결 수 조회

```http
GET /api/v1/ws/projects/{project_id}/connections
```

**응답 예시**:
```json
{
  "project_id": "campaign_001",
  "active_connections": 3
}
```

### 3. 전체 연결 통계

```http
GET /api/v1/ws/connections
```

**응답 예시**:
```json
{
  "total_projects": 5,
  "total_connections": 12,
  "projects": {
    "campaign_001": 3,
    "campaign_002": 2,
    "campaign_003": 7
  }
}
```

## 클라이언트 구현

### JavaScript / Next.js

```javascript
// utils/websocket.js
class ProjectWebSocket {
  constructor(projectId) {
    this.projectId = projectId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = {};
  }

  connect() {
    const url = `ws://localhost:8000/api/v1/ws/projects/${this.projectId}/stream`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.startKeepAlive();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket closed');
      this.stopKeepAlive();
      this.reconnect();
    };
  }

  handleEvent(data) {
    const { type } = data;

    // 타입별 리스너 호출
    if (this.listeners[type]) {
      this.listeners[type].forEach(callback => callback(data));
    }

    // 모든 이벤트 리스너 호출
    if (this.listeners['*']) {
      this.listeners['*'].forEach(callback => callback(data));
    }
  }

  on(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

  off(eventType, callback) {
    if (this.listeners[eventType]) {
      this.listeners[eventType] = this.listeners[eventType].filter(
        cb => cb !== callback
      );
    }
  }

  startKeepAlive() {
    this.keepAliveInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // 30초마다
  }

  stopKeepAlive() {
    if (this.keepAliveInterval) {
      clearInterval(this.keepAliveInterval);
    }
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect() {
    this.stopKeepAlive();
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default ProjectWebSocket;
```

### React Hook 사용 예시

```jsx
// hooks/useProjectWebSocket.js
import { useEffect, useRef, useState } from 'react';
import ProjectWebSocket from '../utils/websocket';

export function useProjectWebSocket(projectId) {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectId) return;

    wsRef.current = new ProjectWebSocket(projectId);

    // 연결 성공
    wsRef.current.on('connected', () => {
      setIsConnected(true);
    });

    // 진행률 업데이트
    wsRef.current.on('progress', (data) => {
      setProgress(data.progress);
      setStatus(data.status);
    });

    // 에러 발생
    wsRef.current.on('error', (data) => {
      setError(data.error);
    });

    // 완료
    wsRef.current.on('completed', (data) => {
      setProgress(1.0);
      setStatus('completed');
    });

    wsRef.current.connect();

    return () => {
      wsRef.current.disconnect();
    };
  }, [projectId]);

  return { isConnected, progress, status, error, ws: wsRef.current };
}
```

### 컴포넌트에서 사용

```jsx
// components/ProjectProgress.jsx
import { useProjectWebSocket } from '../hooks/useProjectWebSocket';

export default function ProjectProgress({ projectId }) {
  const { isConnected, progress, status, error } = useProjectWebSocket(projectId);

  return (
    <div className="project-progress">
      <div className="connection-status">
        {isConnected ? '✅ Connected' : '🔌 Connecting...'}
      </div>

      {error && (
        <div className="error">
          ❌ Error: {error}
        </div>
      )}

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      <div className="status">
        Status: {status} ({Math.round(progress * 100)}%)
      </div>
    </div>
  );
}
```

### Python 클라이언트

```python
# client.py
import asyncio
import websockets
import json
from typing import Callable, Dict

class ProjectWebSocketClient:
    def __init__(self, project_id: str, base_url: str = "ws://localhost:8000"):
        self.project_id = project_id
        self.base_url = base_url
        self.ws = None
        self.listeners: Dict[str, list] = {}

    async def connect(self):
        """WebSocket 연결"""
        uri = f"{self.base_url}/api/v1/ws/projects/{self.project_id}/stream"

        self.ws = await websockets.connect(uri)
        print(f"✅ Connected to {uri}")

        # 연결 확인 메시지 수신
        response = await self.ws.recv()
        data = json.loads(response)
        self._emit('connected', data)

    async def listen(self):
        """메시지 수신 루프"""
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)

                event_type = data.get('type')
                self._emit(event_type, data)
                self._emit('*', data)  # 모든 이벤트 리스너

        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            self._emit('disconnected', {})

    def on(self, event_type: str, callback: Callable):
        """이벤트 리스너 등록"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def _emit(self, event_type: str, data: dict):
        """이벤트 발생"""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(data)

    async def close(self):
        """연결 종료"""
        if self.ws:
            await self.ws.close()


# 사용 예시
async def main():
    client = ProjectWebSocketClient("campaign_001")

    # 이벤트 리스너 등록
    def on_progress(data):
        progress = data.get('progress', 0)
        status = data.get('status', '')
        print(f"📊 Progress: {progress * 100:.1f}% - {status}")

    def on_error(data):
        error = data.get('error', '')
        print(f"❌ Error: {error}")

    def on_completed(data):
        result = data.get('result', {})
        print(f"✅ Completed: {result}")

    client.on('progress', on_progress)
    client.on('error', on_error)
    client.on('completed', on_completed)

    # 연결 및 수신
    await client.connect()
    await client.listen()

if __name__ == "__main__":
    asyncio.run(main())
```

## 서버에서 브로드캐스트

### Celery Task에서 사용

```python
from celery import shared_task
from app.services.websocket_manager import get_websocket_manager
import asyncio

@shared_task(bind=True)
def generate_video(self, project_id: str, script: str):
    """영상 생성 작업"""
    manager = get_websocket_manager()

    # 진행률 브로드캐스트를 위한 헬퍼
    async def broadcast_progress(progress: float, message: str):
        await manager.broadcast_progress(
            project_id=project_id,
            task_name="video_generation",
            progress=progress,
            status="in_progress",
            message=message
        )

    try:
        # 1. TTS 생성
        asyncio.run(broadcast_progress(0.1, "Generating TTS audio..."))
        audio_url = generate_tts(script)

        # 2. 영상 생성
        asyncio.run(broadcast_progress(0.5, "Generating video with Veo..."))
        video_url = generate_veo_video(script)

        # 3. 립싱크 처리
        asyncio.run(broadcast_progress(0.8, "Processing lipsync..."))
        final_url = process_lipsync(video_url, audio_url)

        # 완료
        asyncio.run(
            manager.broadcast_completion(
                project_id=project_id,
                task_name="video_generation",
                result={"video_url": final_url}
            )
        )

        return final_url

    except Exception as e:
        # 에러 브로드캐스트
        asyncio.run(
            manager.broadcast_error(
                project_id=project_id,
                task_name="video_generation",
                error=str(e)
            )
        )
        raise
```

### FastAPI 엔드포인트에서 사용

```python
from fastapi import APIRouter, BackgroundTasks
from app.services.websocket_manager import get_websocket_manager

router = APIRouter()

@router.post("/projects/{project_id}/generate")
async def generate_content(
    project_id: str,
    script: str,
    background_tasks: BackgroundTasks
):
    """컨텐츠 생성 (비동기)"""
    manager = get_websocket_manager()

    # 작업 시작 알림
    await manager.broadcast_status(
        project_id=project_id,
        task_name="content_generation",
        status="queued",
        message="Task queued for processing"
    )

    # Celery 작업 큐에 추가
    task = generate_video.delay(project_id, script)

    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Connect to WebSocket for real-time updates"
    }
```

## 테스트

### 단일 연결 테스트

```bash
# 기본 테스트
python test_websocket.py

# 프로젝트 ID 지정
python test_websocket.py campaign_001
```

### 동시 연결 테스트

```bash
# 3개의 동시 연결 테스트
python test_websocket.py campaign_001 multi 3

# 10개의 동시 연결 테스트
python test_websocket.py campaign_001 multi 10
```

### curl을 사용한 HTTP 엔드포인트 테스트

```bash
# 활성 연결 수 조회
curl http://localhost:8000/api/v1/ws/projects/campaign_001/connections

# 전체 연결 통계
curl http://localhost:8000/api/v1/ws/connections
```

## 프로덕션 고려사항

### 1. 인증 추가

```python
from fastapi import WebSocket, Depends, HTTPException
from app.core.auth import verify_token

@router.websocket("/projects/{project_id}/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(...)
):
    # 토큰 검증
    user = verify_token(token)
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # 프로젝트 접근 권한 확인
    if not user.can_access_project(project_id):
        await websocket.close(code=1008, reason="Forbidden")
        return

    # 연결 진행...
```

### 2. 스케일링 (Redis Pub/Sub)

여러 서버 인스턴스에서 WebSocket을 지원하려면 Redis Pub/Sub 사용:

```python
import redis.asyncio as redis

class ConnectionManager:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
        self.active_connections = {}

    async def subscribe_to_redis(self):
        """Redis 채널 구독"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("websocket_events")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                project_id = data['project_id']
                await self.send_to_project(project_id, data)

    async def broadcast_progress(self, project_id: str, ...):
        """Redis를 통해 모든 서버에 브로드캐스트"""
        event = {...}

        # 로컬 연결에 전송
        await self.send_to_project(project_id, event)

        # Redis를 통해 다른 서버에도 전송
        await self.redis.publish("websocket_events", json.dumps(event))
```

### 3. 모니터링

```python
from app.services.websocket_manager import get_websocket_manager

@router.get("/ws/health")
async def websocket_health():
    """WebSocket 시스템 헬스 체크"""
    manager = get_websocket_manager()
    connections = manager.get_all_connection_counts()

    return {
        "status": "healthy",
        "total_projects": len(connections),
        "total_connections": sum(connections.values()),
        "projects": connections
    }
```

## 문제 해결

### 연결이 자주 끊기는 경우

1. **Keep-alive 주기 조정**: 30초 → 60초
2. **리버스 프록시 타임아웃 설정** (Nginx):
   ```nginx
   location /api/v1/ws/ {
       proxy_pass http://backend;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_read_timeout 3600s;  # 1시간
       proxy_send_timeout 3600s;
   }
   ```

### 메모리 사용량 증가

- 연결 수 제한 설정
- 비활성 연결 자동 정리
- Redis로 스케일 아웃

### 메시지 누락

- Celery에서 `acks_late=True` 설정
- 중요한 이벤트는 DB에도 저장
- 클라이언트 재연결 시 마지막 상태 조회

## 참고 자료

- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [websockets Library](https://websockets.readthedocs.io/)
- [WebSocket Protocol (RFC 6455)](https://datatracker.ietf.org/doc/html/rfc6455)
