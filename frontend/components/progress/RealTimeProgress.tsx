/**
 * Real-Time Progress Component
 * WebSocket으로 Celery Task 진행 상태 실시간 표시
 */
import { useEffect, useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

interface ProgressEvent {
  content_id: number;
  stage: string;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  timestamp: string;
}

interface RealTimeProgressProps {
  contentId: number;
  onComplete?: (data: any) => void;
  onError?: (error: string) => void;
}

export function RealTimeProgress({ 
  contentId, 
  onComplete, 
  onError 
}: RealTimeProgressProps) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle');

  useEffect(() => {
    // WebSocket 연결
    const ws = new WebSocket(`ws://localhost:8000/ws/progress/${contentId}`);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setStatus('processing');
    };

    ws.onmessage = (event) => {
      const data: ProgressEvent = JSON.parse(event.data);
      
      setProgress(data.progress);
      setStage(data.stage);
      setMessage(data.message);

      if (data.status === 'completed') {
        setStatus('completed');
        onComplete?.(data);
        ws.close();
      } else if (data.status === 'failed') {
        setStatus('failed');
        onError?.(data.message);
        ws.close();
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setStatus('failed');
      onError?.('Connection failed');
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
    };

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [contentId]);

  return (
    <div className="w-full space-y-4 p-6 bg-white rounded-lg shadow-sm border">
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {status === 'completed' && '✅ Completed'}
          {status === 'failed' && '❌ Failed'}
          {status === 'processing' && '⏳ Processing'}
        </h3>
        
        {status === 'processing' && (
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
        )}
        {status === 'completed' && (
          <CheckCircle2 className="h-5 w-5 text-green-500" />
        )}
        {status === 'failed' && (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">{stage || 'Initializing...'}</span>
          <span className="font-medium">{progress}%</span>
        </div>
        
        <Progress value={progress} className="h-2" />
        
        <p className="text-sm text-gray-500">{message}</p>
      </div>

      {/* Stage Details */}
      <div className="grid grid-cols-5 gap-2 text-xs">
        {['Script', 'Storyboard', 'Audio', 'Video', 'Complete'].map((s, i) => (
          <div
            key={s}
            className={`
              text-center py-2 rounded
              ${progress >= (i + 1) * 20 
                ? 'bg-blue-100 text-blue-700 font-medium' 
                : 'bg-gray-100 text-gray-400'
              }
            `}
          >
            {s}
          </div>
        ))}
      </div>
    </div>
  );
}
