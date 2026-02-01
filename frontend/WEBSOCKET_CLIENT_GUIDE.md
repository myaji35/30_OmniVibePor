# WebSocket 클라이언트 구현 가이드

**작성일**: 2026-02-02
**작성자**: Claude Code
**프로젝트**: OmniVibe Pro Frontend

---

## 개요

이 문서는 OmniVibe Pro 프론트엔드에 구현된 WebSocket 기반 실시간 진행률 추적 시스템을 설명합니다.

### 구현 목표

- **실시간 진행률 추적**: WebSocket을 통한 서버-클라이언트 양방향 통신
- **자동 재연결**: Exponential backoff 알고리즘으로 안정적인 재연결
- **폴링 Fallback**: WebSocket 실패 시 HTTP 폴링으로 자동 전환
- **Keep-alive**: 30초마다 ping/pong으로 연결 유지
- **TypeScript 완전 지원**: 모든 타입 안전성 보장

---

## 구현된 파일

### 1. `frontend/hooks/useWebSocket.ts` (244 라인)

**역할**: WebSocket 연결 관리 및 자동 재연결 로직

**주요 기능**:
- WebSocket 연결 및 자동 재연결 (exponential backoff)
- Keep-alive ping/pong (30초 간격)
- 폴링 Fallback (WebSocket 실패 시)
- 이벤트 핸들러 (onMessage, onProgress, onError, onCompleted)

**사용 예시**:
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const { isConnected, isFallback, reconnectAttempts } = useWebSocket({
  projectId: 'task_123',
  onProgress: (progress, message) => {
    console.log(`Progress: ${progress * 100}% - ${message}`)
  },
  onCompleted: (result) => {
    console.log('Task completed:', result)
  },
  onError: (error) => {
    console.error('Task failed:', error)
  }
})
```

**옵션**:
- `projectId` (required): 추적할 프로젝트/태스크 ID
- `onMessage`: 모든 WebSocket 메시지를 받는 콜백
- `onProgress`: 진행률 업데이트 콜백 (progress: 0-1, message: string)
- `onError`: 에러 발생 시 콜백
- `onCompleted`: 작업 완료 시 콜백
- `autoReconnect`: 자동 재연결 활성화 (기본값: true)
- `maxReconnectAttempts`: 최대 재연결 시도 횟수 (기본값: 5)
- `pollingFallback`: 폴링 Fallback 활성화 (기본값: true)
- `pollingInterval`: 폴링 간격 (기본값: 2000ms)
- `backendUrl`: 백엔드 URL (기본값: 'localhost:8000')

---

### 2. `frontend/components/ProgressBar.tsx` (191 라인)

**역할**: 실시간 진행률 표시 UI 컴포넌트

**주요 기능**:
- WebSocket 기반 실시간 진행률 업데이트
- 연결 상태 표시 (실시간 연결 / 폴링 모드 / 재연결 중)
- 진행률 바 (0-100%)
- 에러 메시지 표시
- 완료 메시지 표시
- Shimmer 애니메이션 (로딩 중 시각 효과)

**사용 예시**:
```typescript
import { ProgressBar } from '@/components/ProgressBar'

<ProgressBar
  projectId="audio_generation_12345"
  onCompleted={(result) => {
    console.log('Audio generated:', result)
    alert('오디오 생성 완료!')
  }}
  onError={(error) => {
    console.error('Generation failed:', error)
  }}
  showConnectionStatus={true}
  className="mt-4"
/>
```

**Props**:
- `projectId` (required): 추적할 프로젝트/태스크 ID
- `onCompleted`: 작업 완료 시 콜백
- `onError`: 에러 발생 시 콜백
- `className`: 추가 CSS 클래스
- `backendUrl`: 백엔드 URL (기본값: 'localhost:8000')
- `showConnectionStatus`: 연결 상태 표시 여부 (기본값: true)

---

### 3. `frontend/app/test-websocket/page.tsx` (234 라인)

**역할**: WebSocket 기능 테스트 전용 페이지

**주요 기능**:
- Task ID 입력 및 실시간 모니터링 시작
- ProgressBar 컴포넌트 통합 테스트
- 작업 완료 결과 JSON 표시
- 기능 설명 및 백엔드 설정 가이드

**접속 방법**:
1. 프론트엔드 실행: `npm run dev`
2. 브라우저에서 http://localhost:3020/test-websocket 접속
3. Task ID 입력 후 "연결 시작" 클릭

**예시 Task ID**:
- `test_task_001`
- `audio_generation_12345`

---

### 4. `frontend/app/globals.css` (업데이트)

**추가된 내용**:
- Shimmer 애니메이션 keyframe 정의
- ProgressBar의 로딩 효과를 위한 CSS

```css
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}
```

---

### 5. `frontend/components/DirectorPanel.tsx` (업데이트)

**변경 사항**:
- 기존 폴링 방식 제거
- ProgressBar 컴포넌트 통합
- WebSocket 기반 실시간 진행률 추적
- handleAudioCompleted / handleAudioError 핸들러 추가

**변경 전** (폴링 방식):
```typescript
// 2초마다 HTTP 요청으로 상태 확인
const pollInterval = setInterval(async () => {
  const response = await fetch(`/api/audio/status/${taskId}`)
  // ...
}, 2000)
```

**변경 후** (WebSocket 방식):
```typescript
{isGeneratingAudio && audioTaskId && (
  <ProgressBar
    projectId={audioTaskId}
    onCompleted={handleAudioCompleted}
    onError={handleAudioError}
    showConnectionStatus={true}
  />
)}
```

---

## 백엔드 요구사항

### WebSocket 엔드포인트

**URL**: `ws://localhost:8000/api/v1/ws/projects/{task_id}/stream`

**메시지 형식** (JSON):
```typescript
interface WebSocketMessage {
  type: 'connected' | 'progress' | 'error' | 'completed' | 'pong'
  project_id?: string
  task_name?: string
  progress?: number  // 0.0 - 1.0
  status?: string
  message?: string
  metadata?: Record<string, any>
  error?: string
  details?: Record<string, any>
  result?: Record<string, any>
  timestamp?: string
}
```

**예시 메시지**:

1. **연결 완료**:
```json
{
  "type": "connected",
  "project_id": "audio_generation_12345",
  "timestamp": "2026-02-02T08:00:00Z"
}
```

2. **진행률 업데이트**:
```json
{
  "type": "progress",
  "project_id": "audio_generation_12345",
  "task_name": "오디오 생성",
  "progress": 0.5,
  "message": "TTS 생성 중... (시도 2/5)",
  "timestamp": "2026-02-02T08:00:10Z"
}
```

3. **에러 발생**:
```json
{
  "type": "error",
  "project_id": "audio_generation_12345",
  "error": "ElevenLabs API 호출 실패",
  "details": {
    "status_code": 500,
    "reason": "Internal Server Error"
  },
  "timestamp": "2026-02-02T08:00:20Z"
}
```

4. **작업 완료**:
```json
{
  "type": "completed",
  "project_id": "audio_generation_12345",
  "result": {
    "audio_id": "audio_123",
    "file_path": "/media/audio/audio_123.mp3",
    "duration": 120.5,
    "accuracy": 0.97,
    "attempt": 2
  },
  "timestamp": "2026-02-02T08:01:00Z"
}
```

---

### 폴링 Fallback 엔드포인트 (선택사항)

**URL**: `GET /api/v1/projects/{task_id}/status`

**응답 형식** (JSON):
```typescript
{
  "project_id": "audio_generation_12345",
  "status": "running" | "completed" | "failed" | "error",
  "progress": 0.5,  // 0.0 - 1.0
  "message": "TTS 생성 중...",
  "result": {
    // 완료 시 결과 데이터
  },
  "error": "에러 메시지 (실패 시)"
}
```

---

## 테스트 방법

### 1. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

**접속**: http://localhost:3020

### 2. WebSocket 테스트 페이지 접속

**URL**: http://localhost:3020/test-websocket

**단계**:
1. Task ID 입력 (예: `test_task_001`)
2. "연결 시작" 클릭
3. 백엔드에서 WebSocket 메시지 전송 시 실시간 진행률 업데이트 확인

### 3. DirectorPanel 통합 테스트

**URL**: http://localhost:3020/production

**단계**:
1. Writer 단계에서 스크립트 작성
2. Director 단계로 이동
3. "Zero-Fault 오디오 생성" 클릭
4. ProgressBar에서 실시간 진행률 확인

---

## 기술 스택

- **React 18**: 훅 기반 컴포넌트
- **Next.js 14**: App Router
- **TypeScript 5**: 완전한 타입 안전성
- **Tailwind CSS 3**: 스타일링
- **WebSocket API**: 브라우저 네이티브 WebSocket

---

## 주요 기능 상세

### 1. 자동 재연결 (Exponential Backoff)

**알고리즘**:
```
delay = min(1000 * 2^(attempt), 30000)
```

**재연결 시도**:
- 1회: 1초 후
- 2회: 2초 후
- 3회: 4초 후
- 4회: 8초 후
- 5회: 16초 후
- 최대: 30초

**재연결 횟수**: 최대 5회 (설정 가능)

### 2. 폴링 Fallback

**전환 조건**:
- WebSocket 연결 실패
- 최대 재연결 시도 횟수 초과

**폴링 간격**: 2초 (설정 가능)

**동작**:
1. WebSocket 연결 실패 감지
2. 자동으로 HTTP 폴링으로 전환
3. UI에 "폴링 모드" 표시
4. 작업 완료/실패 시 폴링 중지

### 3. Keep-alive (Ping/Pong)

**목적**: WebSocket 연결 유지 및 타임아웃 방지

**동작**:
- 30초마다 클라이언트 → 서버로 "ping" 전송
- 서버는 "pong" 응답 (선택사항)
- 연결이 끊어지면 자동 재연결

---

## 트러블슈팅

### 1. "WebSocket connection failed"

**원인**: 백엔드 서버가 실행되지 않음 또는 WebSocket 엔드포인트 미구현

**해결**:
1. 백엔드 서버 실행 확인: `http://localhost:8000`
2. WebSocket 엔드포인트 구현 확인: `ws://localhost:8000/api/v1/ws/projects/{task_id}/stream`
3. 방화벽/네트워크 설정 확인

### 2. "Falling back to polling"

**원인**: WebSocket 연결이 최대 재연결 시도 횟수를 초과

**해결**:
1. 정상 동작: 폴링으로 대체되어 계속 작동
2. 백엔드 로그 확인하여 WebSocket 에러 원인 파악
3. 필요 시 `maxReconnectAttempts` 옵션 증가

### 3. "Progress stuck at 0%"

**원인**: 백엔드에서 WebSocket 메시지를 전송하지 않음

**해결**:
1. 백엔드 로그 확인
2. WebSocket 메시지 형식 확인 (`type: 'progress'`, `progress: 0.0-1.0`)
3. 브라우저 개발자 도구 → Network → WS 탭에서 메시지 확인

### 4. TypeScript 에러

**원인**: 타입 정의 불일치

**해결**:
```bash
cd frontend
npx tsc --noEmit
```
- 모든 타입 에러를 확인하고 수정

---

## 성능 최적화

### 1. 메모리 누수 방지

- `useEffect` cleanup 함수로 WebSocket 연결 해제
- `clearInterval`로 ping/polling 타이머 정리
- 컴포넌트 언마운트 시 자동 정리

### 2. 불필요한 리렌더링 방지

- `useCallback`으로 이벤트 핸들러 메모이제이션
- `useState`로 최소한의 상태만 관리

### 3. 네트워크 효율

- Keep-alive로 불필요한 재연결 방지
- 폴링은 WebSocket 실패 시에만 사용
- Exponential backoff로 서버 부하 감소

---

## 향후 개선 사항

### 1. Reconnect Token

**목적**: 재연결 시 이전 상태 복구

**구현**:
```typescript
const token = sessionStorage.getItem('ws_reconnect_token')
const wsUrl = `ws://localhost:8000/ws?token=${token}`
```

### 2. Message Queue

**목적**: 연결 끊김 중 메시지 손실 방지

**구현**:
```typescript
const messageQueue = useRef<WebSocketMessage[]>([])

ws.onopen = () => {
  messageQueue.current.forEach(msg => ws.send(JSON.stringify(msg)))
  messageQueue.current = []
}
```

### 3. Compression

**목적**: 네트워크 대역폭 절약

**구현**:
```typescript
ws.binaryType = 'arraybuffer'
// 백엔드에서 gzip 압축된 메시지 전송
```

---

## 코드 품질

### 빌드 결과

```
✓ Compiled successfully
✓ Generating static pages (17/17)
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /test-websocket                      4.12 kB        88.3 kB
```

### 린트 결과

- **신규 코드**: 0 에러, 0 경고
- **기존 코드**: 2 에러 (수정 완료), 6 경고 (기능 무관)

### 타입 체크 결과

- **신규 코드**: 0 타입 에러
- **TypeScript 완전 지원**: 모든 함수와 변수에 타입 정의

---

## 파일 통계

| 파일 | 라인 수 | 크기 |
|------|---------|------|
| `hooks/useWebSocket.ts` | 244 | 6.8KB |
| `components/ProgressBar.tsx` | 191 | - |
| `app/test-websocket/page.tsx` | 234 | - |
| **합계** | **669** | **6.8KB** |

---

## 사용 예시 (종합)

### 간단한 사용

```typescript
import { ProgressBar } from '@/components/ProgressBar'

export default function MyPage() {
  return (
    <ProgressBar
      projectId="task_123"
      onCompleted={(result) => alert('완료!')}
    />
  )
}
```

### 고급 사용 (커스텀 UI)

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

export default function MyPage() {
  const [progress, setProgress] = useState(0)

  const { isConnected, isFallback } = useWebSocket({
    projectId: 'task_123',
    onProgress: (prog, msg) => {
      setProgress(prog * 100)
      console.log(msg)
    },
    onCompleted: (result) => {
      console.log('Result:', result)
    }
  })

  return (
    <div>
      <p>진행률: {progress}%</p>
      <p>상태: {isFallback ? '폴링 모드' : isConnected ? '실시간 연결' : '연결 중'}</p>
    </div>
  )
}
```

---

## 결론

이번 구현으로 OmniVibe Pro 프론트엔드는 다음을 달성했습니다:

✅ **실시간 진행률 추적**: WebSocket 기반 양방향 통신
✅ **안정성**: 자동 재연결 + 폴링 Fallback
✅ **타입 안전성**: TypeScript 완전 지원
✅ **UX**: 연결 상태 표시, Shimmer 애니메이션, 에러 처리
✅ **확장성**: 재사용 가능한 훅 및 컴포넌트
✅ **테스트 가능**: 전용 테스트 페이지 제공

**다음 단계**: 백엔드 WebSocket 엔드포인트 구현 및 통합 테스트

---

**문의**: 이 가이드에 대한 질문이나 개선 사항이 있으면 팀에 문의하세요.
