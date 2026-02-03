/**
 * useAutoSave - 자동 저장 Hook
 *
 * REALPLAN.md Phase 2.4 구현
 *
 * 5초마다 ProductionContext → localStorage 저장
 * 새로고침 시에도 복구 가능
 */

import { useEffect, useRef } from 'react';
import { ProductionState } from '../contexts/ProductionContext';

interface UseAutoSaveOptions {
  enabled?: boolean;
  interval?: number; // ms
  storageKey?: string;
}

export function useAutoSave(
  state: ProductionState,
  options: UseAutoSaveOptions = {}
) {
  const {
    enabled = true,
    interval = 5000,
    storageKey = 'omnivibe_production_autosave',
  } = options;

  const lastSaved = useRef<number>(0);

  useEffect(() => {
    if (!enabled) return;
    if (typeof window === 'undefined') return; // SSR 체크

    const timer = setInterval(() => {
      try {
        // 변경사항이 있을 때만 저장
        const now = Date.now();
        if (now - lastSaved.current < interval) return;

        // localStorage에 저장
        const dataToSave = {
          ...state,
          savedAt: new Date().toISOString(),
        };

        localStorage.setItem(storageKey, JSON.stringify(dataToSave));
        lastSaved.current = now;

        console.log('[AutoSave] Production state saved to localStorage');
      } catch (err) {
        console.error('[AutoSave] Failed to save:', err);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [state, enabled, interval, storageKey]);

  // 복구 함수
  const restore = (): ProductionState | null => {
    if (typeof window === 'undefined') return null;

    try {
      const saved = localStorage.getItem(storageKey);
      if (!saved) return null;

      const data = JSON.parse(saved);
      console.log('[AutoSave] Production state restored from localStorage');
      return data as ProductionState;
    } catch (err) {
      console.error('[AutoSave] Failed to restore:', err);
      return null;
    }
  };

  // 초기화 함수
  const clear = () => {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(storageKey);
      console.log('[AutoSave] Production state cleared from localStorage');
    } catch (err) {
      console.error('[AutoSave] Failed to clear:', err);
    }
  };

  return { restore, clear };
}
