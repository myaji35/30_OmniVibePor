/**
 * Subtitle Presets
 *
 * 플랫폼별 자막 스타일 프리셋 정의
 */

import { SubtitlePreset, SubtitleStyle } from '@/lib/types/subtitle';

export const DEFAULT_SUBTITLE_STYLE: SubtitleStyle = {
  font_family: 'Roboto',
  font_size: 42,
  font_color: '#FFFFFF',
  background_color: '#000000',
  background_opacity: 0.7,
  position: 'bottom',
  vertical_offset: 80,
  alignment: 'center',
  outline_width: 2,
  outline_color: '#000000',
  shadow_enabled: true,
  shadow_offset_x: 2,
  shadow_offset_y: 2,
};

export const SUBTITLE_PRESETS: Record<string, SubtitlePreset> = {
  youtube: {
    name: 'YouTube',
    description: '유튜브 최적화 스타일 (큰 폰트, 명확한 배경)',
    style: {
      font_family: 'Roboto',
      font_size: 42,
      font_color: '#FFFFFF',
      background_color: '#000000',
      background_opacity: 0.7,
      position: 'bottom',
      vertical_offset: 80,
      alignment: 'center',
      outline_width: 2,
      outline_color: '#000000',
      shadow_enabled: true,
      shadow_offset_x: 2,
      shadow_offset_y: 2,
    },
  },
  tiktok: {
    name: 'TikTok',
    description: '틱톡 최적화 스타일 (중앙 배치, 강렬한 아웃라인)',
    style: {
      font_family: 'Montserrat',
      font_size: 48,
      font_color: '#FFFFFF',
      background_color: '#000000',
      background_opacity: 0.5,
      position: 'center',
      vertical_offset: 0,
      alignment: 'center',
      outline_width: 3,
      outline_color: '#FF0050',
      shadow_enabled: true,
      shadow_offset_x: 3,
      shadow_offset_y: 3,
    },
  },
  instagram: {
    name: 'Instagram',
    description: '인스타그램 최적화 스타일 (작은 폰트, 세련된 디자인)',
    style: {
      font_family: 'Poppins',
      font_size: 36,
      font_color: '#FFFFFF',
      background_color: '#1A1A1A',
      background_opacity: 0.6,
      position: 'bottom',
      vertical_offset: 100,
      alignment: 'center',
      outline_width: 1,
      outline_color: '#000000',
      shadow_enabled: true,
      shadow_offset_x: 1,
      shadow_offset_y: 1,
    },
  },
  minimal: {
    name: 'Minimal',
    description: '미니멀 스타일 (배경 없음, 깔끔한 아웃라인)',
    style: {
      font_family: 'Arial',
      font_size: 40,
      font_color: '#FFFFFF',
      background_color: '#000000',
      background_opacity: 0,
      position: 'bottom',
      vertical_offset: 60,
      alignment: 'center',
      outline_width: 3,
      outline_color: '#000000',
      shadow_enabled: false,
      shadow_offset_x: 0,
      shadow_offset_y: 0,
    },
  },
};

// 사용 가능한 폰트 목록
export const FONT_FAMILIES = [
  { value: 'Roboto', label: 'Roboto' },
  { value: 'Montserrat', label: 'Montserrat' },
  { value: 'Poppins', label: 'Poppins' },
  { value: 'Arial', label: 'Arial' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Noto Sans KR', label: 'Noto Sans KR (한글)' },
  { value: 'Nanum Gothic', label: 'Nanum Gothic (한글)' },
];

// 위치 옵션
export const POSITION_OPTIONS: Array<{ value: 'top' | 'center' | 'bottom'; label: string }> = [
  { value: 'top', label: '상단' },
  { value: 'center', label: '중앙' },
  { value: 'bottom', label: '하단' },
];

// 정렬 옵션
export const ALIGNMENT_OPTIONS: Array<{ value: 'left' | 'center' | 'right'; label: string }> = [
  { value: 'left', label: '왼쪽' },
  { value: 'center', label: '중앙' },
  { value: 'right', label: '오른쪽' },
];
