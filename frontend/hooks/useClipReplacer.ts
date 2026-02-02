import { useState, useEffect, useCallback } from 'react';
import {
  getAlternativeClips,
  generateAlternativeClips,
  getClipGenerationProgress,
  replaceClip,
  deleteAlternativeClip,
  AlternativeClipsData,
  ClipGenerationProgress,
} from '@/lib/api/clips';

interface UseClipReplacerReturn {
  data: AlternativeClipsData | null;
  isLoading: boolean;
  isGenerating: boolean;
  generationProgress: ClipGenerationProgress | null;
  error: string | null;
  refreshClips: () => Promise<void>;
  generateClips: () => Promise<void>;
  replaceCurrentClip: (clipId: string) => Promise<void>;
  deleteClip: (clipId: string) => Promise<void>;
}

export function useClipReplacer(sectionId: string): UseClipReplacerReturn {
  const [data, setData] = useState<AlternativeClipsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<ClipGenerationProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // Fetch alternative clips
  const refreshClips = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const clipsData = await getAlternativeClips(sectionId);
      setData(clipsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch clips');
    } finally {
      setIsLoading(false);
    }
  }, [sectionId]);

  // Generate new alternative clips
  const generateClips = useCallback(async () => {
    setIsGenerating(true);
    setError(null);
    setGenerationProgress({
      status: 'pending',
      progress: 0,
      message: 'AI 영상 생성 요청 중...',
    });

    try {
      const { task_id } = await generateAlternativeClips(sectionId);
      setCurrentTaskId(task_id);
      setGenerationProgress({
        status: 'generating',
        progress: 10,
        message: 'AI 영상 생성 중... (약 50초 소요)',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate clips');
      setIsGenerating(false);
      setGenerationProgress(null);
    }
  }, [sectionId]);

  // Replace the current clip with an alternative
  const replaceCurrentClip = useCallback(
    async (clipId: string) => {
      setError(null);

      try {
        await replaceClip(sectionId, clipId);
        await refreshClips();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to replace clip');
        throw err;
      }
    },
    [sectionId, refreshClips]
  );

  // Delete an alternative clip
  const deleteClip = useCallback(
    async (clipId: string) => {
      setError(null);

      try {
        await deleteAlternativeClip(sectionId, clipId);
        await refreshClips();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete clip');
        throw err;
      }
    },
    [sectionId, refreshClips]
  );

  // Poll for generation progress
  useEffect(() => {
    if (!currentTaskId || !isGenerating) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const progress = await getClipGenerationProgress(currentTaskId);
        setGenerationProgress(progress);

        if (progress.status === 'completed') {
          setIsGenerating(false);
          setCurrentTaskId(null);
          setGenerationProgress(null);
          await refreshClips();
        } else if (progress.status === 'failed') {
          setError(progress.message || 'Clip generation failed');
          setIsGenerating(false);
          setCurrentTaskId(null);
          setGenerationProgress(null);
        }
      } catch (err) {
        console.error('Failed to fetch generation progress:', err);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [currentTaskId, isGenerating, refreshClips]);

  // Initial fetch
  useEffect(() => {
    refreshClips();
  }, [refreshClips]);

  return {
    data,
    isLoading,
    isGenerating,
    generationProgress,
    error,
    refreshClips,
    generateClips,
    replaceCurrentClip,
    deleteClip,
  };
}
