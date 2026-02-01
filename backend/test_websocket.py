"""WebSocket 테스트 스크립트

WebSocket 연결 및 이벤트 수신을 테스트합니다.

Usage:
    python test_websocket.py

    또는 프로젝트 ID 지정:
    python test_websocket.py campaign_001
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime


async def test_websocket(project_id: str = "test_project"):
    """WebSocket 연결 테스트"""
    uri = f"ws://localhost:8000/api/v1/ws/projects/{project_id}/stream"

    print(f"🔌 Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected successfully")

            # 연결 확인 메시지 수신
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Connected: {data}")

            # 비동기로 ping 전송 (keep-alive)
            async def send_ping():
                while True:
                    await asyncio.sleep(30)
                    try:
                        await websocket.send("ping")
                        print("🏓 Ping sent")
                    except Exception as e:
                        print(f"❌ Failed to send ping: {e}")
                        break

            # ping 태스크 시작
            ping_task = asyncio.create_task(send_ping())

            # 메시지 수신 대기
            print("👂 Listening for events...")

            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    event_type = data.get("type")

                    if event_type == "pong":
                        print(f"[{timestamp}] 🏓 Pong received")
                    elif event_type == "progress":
                        progress = data.get("progress", 0)
                        status = data.get("status", "")
                        message = data.get("message", "")
                        task_name = data.get("task_name", "")

                        print(f"[{timestamp}] 📊 Progress Update:")
                        print(f"  Task: {task_name}")
                        print(f"  Status: {status}")
                        print(f"  Progress: {progress * 100:.1f}%")
                        print(f"  Message: {message}")

                        if data.get("metadata"):
                            print(f"  Metadata: {json.dumps(data['metadata'], indent=2)}")

                    elif event_type == "status":
                        task_name = data.get("task_name", "")
                        status = data.get("status", "")
                        message = data.get("message", "")

                        print(f"[{timestamp}] 🔄 Status Change:")
                        print(f"  Task: {task_name}")
                        print(f"  Status: {status}")
                        print(f"  Message: {message}")

                    elif event_type == "error":
                        task_name = data.get("task_name", "")
                        error = data.get("error", "")
                        details = data.get("details", {})

                        print(f"[{timestamp}] ❌ Error:")
                        print(f"  Task: {task_name}")
                        print(f"  Error: {error}")
                        if details:
                            print(f"  Details: {json.dumps(details, indent=2)}")

                    elif event_type == "completed":
                        task_name = data.get("task_name", "")
                        result = data.get("result", {})

                        print(f"[{timestamp}] ✅ Completed:")
                        print(f"  Task: {task_name}")
                        print(f"  Result: {json.dumps(result, indent=2)}")

                    else:
                        print(f"[{timestamp}] ❓ Unknown event type: {event_type}")
                        print(f"  Data: {json.dumps(data, indent=2)}")

            except websockets.exceptions.ConnectionClosed:
                print("🔌 Connection closed by server")
                ping_task.cancel()
            except KeyboardInterrupt:
                print("\n⛔ Interrupted by user")
                ping_task.cancel()

    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_multiple_connections(project_id: str = "test_project", num_connections: int = 3):
    """여러 WebSocket 연결 동시 테스트"""
    print(f"🔌 Testing {num_connections} simultaneous connections to: {project_id}")

    async def single_connection(conn_id: int):
        uri = f"ws://localhost:8000/api/v1/ws/projects/{project_id}/stream"
        try:
            async with websockets.connect(uri) as websocket:
                response = await websocket.recv()
                print(f"✅ Connection {conn_id} established")

                # 10초 대기
                await asyncio.sleep(10)

                print(f"🔌 Connection {conn_id} closing")
        except Exception as e:
            print(f"❌ Connection {conn_id} failed: {e}")

    # 모든 연결을 동시에 시작
    tasks = [single_connection(i) for i in range(num_connections)]
    await asyncio.gather(*tasks)

    print("✅ All connections closed")


if __name__ == "__main__":
    # 프로젝트 ID를 인자로 받기
    project_id = sys.argv[1] if len(sys.argv) > 1 else "test_project"

    # 테스트 모드 선택
    if len(sys.argv) > 2 and sys.argv[2] == "multi":
        num_connections = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        asyncio.run(test_multiple_connections(project_id, num_connections))
    else:
        asyncio.run(test_websocket(project_id))
