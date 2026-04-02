export interface ScriptBlock {
  id?: number;
  type: 'hook' | 'intro' | 'body' | 'cta' | 'outro';
  text: string;
  startTime: number; // seconds
  duration: number; // seconds
  backgroundUrl?: string;
  animation?: 'fadeIn' | 'slideInUp' | 'slideInLeft' | 'zoomIn';
  fontSize?: number;
  textColor?: string;
  textAlign?: 'left' | 'center' | 'right';
  wordTimestamps?: WordTimestamp[];
  subtitleStyle?: 'default' | 'bold-center' | 'lower-third' | 'karaoke';
}

export interface BrandingConfig {
  logo: string;
  primaryColor: string;
  secondaryColor?: string;
  fontFamily?: string;
}

export interface VideoTemplateProps {
  blocks: ScriptBlock[];
  audioUrl: string;
  branding: BrandingConfig;
}

export interface RenderConfig {
  format: 'youtube' | 'instagram' | 'tiktok';
  fps: number;
  quality: 'low' | 'medium' | 'high';
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}
