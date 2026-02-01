/**
 * WebSocket 자동 재연결 훅
 *
 * Features:
 * - 자동 재연결 (exponential backoff)
 * - Fallback to 폴링 (WebSocket 실패 시)
 * - Keep-alive ping/pong
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: 'connected' | 'progress' | 'error' | 'completed' | 'pong'
  project_id?: string
  task_name?: string
  progress?: number
  status?: string
  message?: string
  metadata?: Record<string, any>
  error?: string
  details?: Record<string, any>
  result?: Record<string, any>
  timestamp?: string
}

export interface UseWebSocketOptions {
  projectId: string
  onMessage?: (message: WebSocketMessage) => void
  onProgress?: (progress: number, message: string) => void
  onError?: (error: string) => void
  onCompleted?: (result: any) => void
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  pollingFallback?: boolean
  pollingInterval?: number
  backendUrl?: string
}

export function useWebSocket({
  projectId,
  onMessage,
  onProgress,
  onError,
  onCompleted,
  autoReconnect = true,
  maxReconnectAttempts = 5,
  pollingFallback = true,
  pollingInterval = 2000,
  backendUrl = 'localhost:8000'
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [isFallback, setIsFallback] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // WebSocket 연결
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const wsUrl = `ws://${backendUrl}/api/v1/ws/projects/${projectId}/stream`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[WebSocket] Connected to:', wsUrl)
        setIsConnected(true)
        setReconnectAttempts(0)
        setIsFallback(false)

        // Keep-alive ping (30초마다)
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
            console.log('[WebSocket] Ping sent')
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('[WebSocket] Message received:', message)

          // 콜백 호출
          onMessage?.(message)

          if (message.type === 'progress' && message.progress !== undefined) {
            onProgress?.(message.progress, message.message || '')
          }

          if (message.type === 'error') {
            onError?.(message.error || 'Unknown error')
          }

          if (message.type === 'completed') {
            onCompleted?.(message.result)
          }
        } catch (parseError) {
          console.error('[WebSocket] Failed to parse message:', parseError)
        }
      }

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
      }

      ws.onclose = (event) => {
        console.log('[WebSocket] Closed:', event.code, event.reason)
        setIsConnected(false)

        // ping 중지
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }

        // 자동 재연결
        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          console.log(`[WebSocket] Reconnecting in ${delay}ms... (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            connect()
          }, delay)
        } else if (pollingFallback && reconnectAttempts >= maxReconnectAttempts) {
          // WebSocket 실패 → 폴링으로 전환
          console.log('[WebSocket] Max reconnect attempts reached. Falling back to polling...')
          setIsFallback(true)
          startPolling()
        }
      }

      wsRef.current = ws

    } catch (error) {
      console.error('[WebSocket] Failed to create WebSocket:', error)

      if (pollingFallback) {
        console.log('[WebSocket] Falling back to polling...')
        setIsFallback(true)
        startPolling()
      }
    }
  }, [projectId, reconnectAttempts, onMessage, onProgress, onError, onCompleted, autoReconnect, maxReconnectAttempts, pollingFallback, backendUrl])

  // 폴링 시작 (Fallback)
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      return
    }

    const poll = async () => {
      try {
        // /api/v1/projects/{id}/status 엔드포인트 호출
        const response = await fetch(`http://${backendUrl}/api/v1/projects/${projectId}/status`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        console.log('[Polling] Status received:', data)

        // WebSocket 메시지 형식으로 변환
        const progress = typeof data.progress === 'number' ? data.progress : 0

        onProgress?.(progress, data.message || data.status || '')

        if (data.status === 'completed') {
          onCompleted?.(data.result || data)
          stopPolling()
        }

        if (data.status === 'failed' || data.status === 'error') {
          onError?.(data.error || 'Task failed')
          stopPolling()
        }

      } catch (error) {
        console.error('[Polling] Error:', error)
        // 폴링 에러는 조용히 처리 (다음 폴링에서 재시도)
      }
    }

    // 즉시 1회 실행 후 interval
    poll()
    pollingIntervalRef.current = setInterval(poll, pollingInterval)
  }, [projectId, onProgress, onCompleted, onError, pollingInterval, backendUrl])

  // 폴링 중지
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
      console.log('[Polling] Stopped')
    }
  }, [])

  // 연결 종료
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting...')

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }

    stopPolling()
  }, [stopPolling])

  // Mount/Unmount
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    isFallback,
    reconnectAttempts,
    disconnect
  }
}
