/**
 * API utilities for custom preset operations
 */

export interface SubtitleStyle {
  font_family?: string;
  font_size?: number;
  color?: string;
  background_color?: string;
  position?: 'top' | 'middle' | 'bottom';
  alignment?: 'left' | 'center' | 'right';
}

export interface BGMSettings {
  volume?: number;
  fade_in?: number;
  fade_out?: number;
  track_url?: string;
  track_name?: string;
}

export interface VideoSettings {
  resolution?: string;
  fps?: number;
  aspect_ratio?: string;
  quality?: 'low' | 'medium' | 'high' | 'ultra';
}

export interface ProjectSettings {
  subtitle_style?: SubtitleStyle;
  bgm_settings?: BGMSettings;
  video_settings?: VideoSettings;
}

export interface CustomPreset {
  preset_id: string;
  name: string;
  description?: string;
  is_favorite: boolean;
  settings: ProjectSettings;
  created_at: string;
  updated_at: string;
}

export interface CreatePresetRequest {
  name: string;
  description?: string;
  is_favorite: boolean;
  settings: ProjectSettings;
}

export interface PresetListResponse {
  presets: CustomPreset[];
  total: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get project subtitle settings
 */
export async function getProjectSubtitleSettings(projectId: string): Promise<SubtitleStyle> {
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/subtitles`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch subtitle settings: ${response.status}`);
  }

  return response.json();
}

/**
 * Get project BGM settings
 */
export async function getProjectBGMSettings(projectId: string): Promise<BGMSettings> {
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/bgm`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch BGM settings: ${response.status}`);
  }

  return response.json();
}

/**
 * Get project video metadata settings
 */
export async function getProjectVideoSettings(projectId: string): Promise<VideoSettings> {
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/video/metadata`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch video settings: ${response.status}`);
  }

  return response.json();
}

/**
 * Get all project settings
 */
export async function getProjectSettings(projectId: string): Promise<ProjectSettings> {
  try {
    const [subtitleStyle, bgmSettings, videoSettings] = await Promise.all([
      getProjectSubtitleSettings(projectId).catch(() => undefined),
      getProjectBGMSettings(projectId).catch(() => undefined),
      getProjectVideoSettings(projectId).catch(() => undefined),
    ]);

    return {
      subtitle_style: subtitleStyle,
      bgm_settings: bgmSettings,
      video_settings: videoSettings,
    };
  } catch (error) {
    console.error('Failed to fetch project settings:', error);
    throw error;
  }
}

/**
 * Create a new custom preset
 */
export async function createCustomPreset(data: CreatePresetRequest): Promise<CustomPreset> {
  const response = await fetch(`${API_BASE_URL}/api/v1/presets/custom`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to create preset: ${response.status}`);
  }

  return response.json();
}

/**
 * Get all custom presets
 */
export async function getCustomPresets(): Promise<PresetListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/presets/custom`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch presets: ${response.status}`);
  }

  return response.json();
}

/**
 * Get a single custom preset by ID
 */
export async function getCustomPreset(presetId: string): Promise<CustomPreset> {
  const response = await fetch(`${API_BASE_URL}/api/v1/presets/custom/${presetId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to fetch preset: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete a custom preset
 */
export async function deleteCustomPreset(presetId: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/presets/custom/${presetId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to delete preset: ${response.status}`);
  }

  return response.json();
}

/**
 * Apply a preset to a project
 */
export async function applyPresetToProject(
  projectId: string,
  presetId: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/preset`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ preset_id: presetId }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `Failed to apply preset: ${response.status}`);
  }

  return response.json();
}
