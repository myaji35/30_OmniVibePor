/**
 * Promo Video i18n — 영어/한국어 텍스트 분리
 */
export interface PromoTexts {
  // Scene 1: Hook
  hookTitle: string;
  hookHighlight: string;
  hookSub: string;
  // Scene 2: SVG
  svgLabel: string;
  svgTitle: string;
  // Scene 3: 3D
  tdLabel: string;
  tdBadge: string;
  // Scene 4: Ken Burns
  kbLabel: string;
  kbTitle: string;
  kbSub: string;
  // Scene 5: Clip-Path
  cpLabel: string;
  cpBefore: string;
  cpAfter: string;
  // Scene 6: Char Reveal
  crLabel: string;
  crLines: string[];
  // Scene 7: Bar Chart
  bcLabel: string;
  bcBars: string[];
  // Scene 8: CTA
  ctaTitle: string;
  ctaHighlight: string;
  ctaSub: string;
  ctaButton: string;
  ctaUrl: string;
}

export const EN: PromoTexts = {
  hookTitle: 'Remotion',
  hookHighlight: 'Showcase',
  hookSub: 'Every feature. One video.',
  svgLabel: 'SVG PATH ANIMATION',
  svgTitle: 'Programmatic SVG Animation',
  tdLabel: '3D CSS TRANSFORMS',
  tdBadge: 'perspective: 1200px',
  kbLabel: 'KEN BURNS EFFECT',
  kbTitle: 'Cinematic Image Panning',
  kbSub: 'scale() + translate() over 180 frames',
  cpLabel: 'CLIP-PATH WIPE TRANSITION',
  cpBefore: 'BEFORE',
  cpAfter: 'AFTER',
  crLabel: 'CHARACTER-BY-CHARACTER REVEAL',
  crLines: [
    'const video = await renderVideo({',
    '  template: "youtube",',
    '  script: aiGeneratedScript,',
    '  voice: clonedVoice,',
    '});',
  ],
  bcLabel: 'DATA-DRIVEN ANIMATION',
  bcBars: ['Render', 'Audio', 'Script', 'Upload', 'Deploy'],
  ctaTitle: 'Built with',
  ctaHighlight: 'Remotion',
  ctaSub: 'spring() · interpolate() · Sequence · Img · SVG · 3D · clipPath',
  ctaButton: 'OmniVibe Pro →',
  ctaUrl: 'omnivibepro.com',
};

export const KO: PromoTexts = {
  hookTitle: 'Remotion',
  hookHighlight: '쇼케이스',
  hookSub: '모든 기능. 하나의 영상.',
  svgLabel: 'SVG 경로 애니메이션',
  svgTitle: '프로그래밍 기반 SVG 드로잉',
  tdLabel: '3D CSS 변환',
  tdBadge: 'perspective: 1200px',
  kbLabel: '켄 번스 효과',
  kbTitle: '시네마틱 이미지 패닝',
  kbSub: 'scale() + translate() — 180프레임',
  cpLabel: '클립패스 와이프 전환',
  cpBefore: '변경 전',
  cpAfter: '변경 후',
  crLabel: '글자별 순차 타이핑',
  crLines: [
    'const 영상 = await 렌더링({',
    '  템플릿: "유튜브",',
    '  스크립트: AI생성스크립트,',
    '  음성: 클론된보이스,',
    '});',
  ],
  bcLabel: '데이터 기반 애니메이션',
  bcBars: ['렌더링', '오디오', '스크립트', '업로드', '배포'],
  ctaTitle: '',
  ctaHighlight: 'Remotion으로 제작',
  ctaSub: 'spring() · interpolate() · Sequence · Img · SVG · 3D · clipPath',
  ctaButton: 'OmniVibe Pro 시작하기 →',
  ctaUrl: 'omnivibepro.com',
};
