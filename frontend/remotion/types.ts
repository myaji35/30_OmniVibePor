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
