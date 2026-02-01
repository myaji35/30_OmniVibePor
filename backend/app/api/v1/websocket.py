"""WebSocket API 엔드포인트"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_manager import get_websocket_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/projects/{project_id}/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str
):
    """
    프로젝트 진행 상태 실시간 스트리밍

    연결 후 다음 이벤트를 수신합니다:

    **이벤트 타입**:
    - `connected`: 연결 성공 확인
    - `progress`: 진행률 업데이트
    - `status`: 작업 상태 변경
    - `error`: 에러 발생
    - `completed`: 작업 완료
    - `pong`: ping에 대한 응답

    **연결 예시 (JavaScript)**:
    ```javascript
    const ws = new WebSocket(
        "ws://localhost:8000/api/v1/ws/projects/campaign_001/stream"
    );

    ws.onopen = () => {
        console.log("WebSocket connected");

        // Keep-alive: 30초마다 ping 전송
        setInterval(() => {
            ws.send("ping");
        }, 30000);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case "connected":
                console.log("Connected to project:", data.project_id);
                break;
            case "progress":
                console.log(`Progress: ${data.progress * 100}%`);
                console.log(`Status: ${data.status}`);
                console.log(`Message: ${data.message}`);
                break;
            case "error":
                console.error(`Error in ${data.task_name}:`, data.error);
                break;
            case "completed":
                console.log(`Task ${data.task_name} completed:`, data.result);
                break;
            case "pong":
                console.log("Pong received");
                break;
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
    };
    ```

    **연결 예시 (Python)**:
    ```python
    import asyncio
    import websockets
    import json

    async def connect():
        uri = "ws://localhost:8000/api/v1/ws/projects/campaign_001/stream"

        async with websockets.connect(uri) as websocket:
            # 연결 확인
            response = await websocket.recv()
            print(f"Connected: {response}")

            # 메시지 수신 대기
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Received: {data['type']} - {data.get('message', '')}")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break

    asyncio.run(connect())
    ```

    Args:
        websocket: WebSocket 연결
        project_id: 프로젝트 ID
    """
    manager = get_websocket_manager()

    await manager.connect(websocket, project_id)

    try:
        # 연결 확인 메시지
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "message": "WebSocket connected successfully",
            "timestamp": manager.active_connections.get(project_id, set()).__len__()
        })

        # 클라이언트로부터 메시지 대기 (keep-alive)
        while True:
            data = await websocket.receive_text()

            # ping-pong for keep-alive
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": manager.active_connections.get(project_id, set()).__len__()
                })
            else:
                logger.warning(f"Unexpected message from client: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        logger.info(f"Client disconnected: {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id)


@router.get("/projects/{project_id}/connections")
async def get_active_connections(project_id: str):
    """
    현재 활성 연결 수 조회

    특정 프로젝트에 연결된 WebSocket 클라이언트 수를 반환합니다.

    Args:
        project_id: 프로젝트 ID

    Returns:
        활성 연결 정보

    Example:
        ```bash
        curl http://localhost:8000/api/v1/ws/projects/campaign_001/connections
        ```

        Response:
        ```json
        {
            "project_id": "campaign_001",
            "active_connections": 3
        }
        ```
    """
    manager = get_websocket_manager()

    count = manager.get_connection_count(project_id)

    return {
        "project_id": project_id,
        "active_connections": count
    }


@router.get("/connections")
async def get_all_connections():
    """
    모든 프로젝트의 활성 연결 수 조회

    디버깅 및 모니터링을 위해 모든 프로젝트의 WebSocket 연결 수를 반환합니다.

    Returns:
        모든 프로젝트의 활성 연결 정보

    Example:
        ```bash
        curl http://localhost:8000/api/v1/ws/connections
        ```

        Response:
        ```json
        {
            "total_projects": 3,
            "total_connections": 7,
            "projects": {
                "campaign_001": 3,
                "campaign_002": 2,
                "campaign_003": 2
            }
        }
        ```
    """
    manager = get_websocket_manager()

    connections = manager.get_all_connection_counts()

    return {
        "total_projects": len(connections),
        "total_connections": sum(connections.values()),
        "projects": connections
    }
