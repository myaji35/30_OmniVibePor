/**
 * API utilities for clip replacement operations
 */

export interface Clip {
  clip_id: string;
  video_path: string;
  thumbnail_url: string;
  prompt: string;
  variation?: 'camera_angle' | 'lighting' | 'color_tone';
  created_at: string;
}

export interface AlternativeClipsData {
  section_id: string;
  current_clip: Clip;
  alternatives: Clip[];
}

export interface ClipGenerationProgress {
  status: 'pending' | 'generating' | 'completed' | 'failed';
  progress: number; // 0-100
  message: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get alternative clips for a section
 */
export async function getAlternativeClips(sectionId: string): Promise<AlternativeClipsData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sections/${sectionId}/alternative-clips`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch alternative clips: ${response.status}`);
  }

  return response.json();
}

/**
 * Generate new alternative clips for a section
 */
export async function generateAlternativeClips(sectionId: string): Promise<{ task_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sections/${sectionId}/alternative-clips`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to generate alternative clips: ${response.status}`);
  }

  return response.json();
}

/**
 * Check the progress of clip generation
 */
export async function getClipGenerationProgress(taskId: string): Promise<ClipGenerationProgress> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/progress`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch generation progress: ${response.status}`);
  }

  return response.json();
}

/**
 * Replace the current clip with an alternative
 */
export async function replaceClip(sectionId: string, clipId: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sections/${sectionId}/clip`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ clip_id: clipId }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to replace clip: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete an alternative clip
 */
export async function deleteAlternativeClip(sectionId: string, clipId: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sections/${sectionId}/alternative-clips/${clipId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to delete alternative clip: ${response.status}`);
  }

  return response.json();
}
