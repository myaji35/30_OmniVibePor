// Storyboard 블록 타입 정의
export interface StoryboardBlock {
  id: string
  order: number
  script: string
  start_time: number
  end_time: number
  keywords: string[]
  visual_concept: VisualConcept
  background_type: 'uploaded' | 'ai_generated' | 'stock' | 'solid_color'
  background_url?: string
  background_prompt?: string
  background_color?: string
  transition_effect: 'fade' | 'slide' | 'dissolve' | 'zoom'
  subtitle_preset: 'normal' | 'bold' | 'minimal' | 'news'
}

export interface VisualConcept {
  mood: string
  color_tone: string
  background_style: string
}

// 스크립트로부터 콘티 블록 자동 생성
export function generateStoryboardBlocks(
  script: string,
  campaignConcept?: {
    mood?: string
    color_tone?: string
    style?: string
  }
): StoryboardBlock[] {
  const blocks: StoryboardBlock[] = []

  // 문장 단위로 분할
  const sentences = script
    .split(/[.!?]\s+/)
    .filter(s => s.trim().length > 0)

  let currentTime = 0

  sentences.forEach((sentence, index) => {
    const duration = estimateDuration(sentence)
    const keywords = extractKeywords(sentence)

    blocks.push({
      id: `storyboard-${index}`,
      order: index,
      script: sentence.trim(),
      start_time: currentTime,
      end_time: currentTime + duration,
      keywords,
      visual_concept: {
        mood: campaignConcept?.mood || 'professional',
        color_tone: campaignConcept?.color_tone || 'warm',
        background_style: campaignConcept?.style || 'modern'
      },
      background_type: 'ai_generated',
      transition_effect: index === 0 ? 'fade' : 'dissolve',
      subtitle_preset: 'normal'
    })

    currentTime += duration
  })

  return blocks
}

// 문장 길이로 대략적인 재생 시간 추정 (한글 기준)
function estimateDuration(text: string): number {
  const koreanChars = (text.match(/[가-힣]/g) || []).length
  const englishWords = (text.match(/[a-zA-Z]+/g) || []).length

  const koreanDuration = koreanChars / 4.5
  const englishDuration = englishWords / 2.5

  return Math.max(2, Math.ceil(koreanDuration + englishDuration))
}

// 키워드 추출 (간단한 구현)
function extractKeywords(text: string): string[] {
  // 실제로는 형태소 분석이나 TF-IDF를 사용할 수 있음
  const words = text
    .replace(/[^\w\s가-힣]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 2)

  // 중복 제거 및 최대 5개까지
  return Array.from(new Set(words)).slice(0, 5)
}

// 전환 효과 아이콘 반환
export function getTransitionIcon(effect: StoryboardBlock['transition_effect']): string {
  switch (effect) {
    case 'fade':
      return '⚫ Fade'
    case 'slide':
      return '➡️ Slide'
    case 'dissolve':
      return '💧 Dissolve'
    case 'zoom':
      return '🔍 Zoom'
    default:
      return effect
  }
}

// 자막 프리셋별 설정 반환
export function getSubtitlePresetConfig(preset: StoryboardBlock['subtitle_preset']) {
  switch (preset) {
    case 'normal':
      return {
        fontSize: '24px',
        fontWeight: '400',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        padding: '8px 16px'
      }
    case 'bold':
      return {
        fontSize: '32px',
        fontWeight: '700',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: '12px 24px'
      }
    case 'minimal':
      return {
        fontSize: '20px',
        fontWeight: '300',
        backgroundColor: 'transparent',
        padding: '4px 8px'
      }
    case 'news':
      return {
        fontSize: '28px',
        fontWeight: '600',
        backgroundColor: 'rgba(255, 0, 0, 0.8)',
        padding: '10px 20px'
      }
    default:
      return {
        fontSize: '24px',
        fontWeight: '400',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        padding: '8px 16px'
      }
  }
}
