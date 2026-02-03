/**
 * Subtitle Style Types
 *
 * 자막 스타일 및 에디터 관련 타입 정의
 */

export interface SubtitleStyle {
  font_family: string;
  font_size: number;
  font_color: string;
  background_color: string;
  background_opacity: number;
  position: 'top' | 'center' | 'bottom';
  vertical_offset: number;
  alignment: 'left' | 'center' | 'right';
  outline_width: number;
  outline_color: string;
  shadow_enabled: boolean;
  shadow_offset_x: number;
  shadow_offset_y: number;
}

export interface SubtitlePreset {
  name: string;
  description: string;
  style: SubtitleStyle;
}

export interface SubtitleEditorProps {
  projectId: string;
  initialStyle?: SubtitleStyle;
  onStyleChange?: (style: SubtitleStyle) => void;
  onPreviewRequest?: () => void;
}

export interface SubtitleAPIResponse {
  subtitle_id: string;
  project_id: string;
  style: SubtitleStyle;
  created_at: string;
  updated_at: string;
}

export interface SubtitlePreviewResponse {
  preview_url: string;
  thumbnail_url?: string;
  created_at: string;
}
