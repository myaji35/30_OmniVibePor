// 분량 기반 스크립트 생성 API

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const {
      topic,
      campaign_name,
      platform,
      content_id,
      target_duration = 60, // 기본 60초
      spreadsheet_id = 'mock-spreadsheet-id', // 임시 spreadsheet_id
      regenerate = false // 기본값: 기존 스크립트 사용
    } = body

    // 🔍 기존 스크립트가 있는지 확인
    if (content_id && !regenerate) {
      console.log(`🔍 콘텐츠 ID ${content_id}의 저장된 스크립트 확인 중...`)
      const existingScript = await getScriptByContentId(content_id)

      if (existingScript) {
        console.log(`✅ 저장된 스크립트를 찾았습니다 (ID: ${existingScript.id})`)

        // AI 콘티 블록 재생성 (타임라인에 표시하기 위해)
        const blocks = await generateStoryboardBlocks(
          existingScript.hook || '',
          existingScript.body || '',
          existingScript.cta || '',
          target_duration
        )

        return Response.json({
          success: true,
          hook: existingScript.hook,
          script: existingScript.body,
          body: existingScript.body, // 호환성 위해 추가
          cta: existingScript.cta,
          blocks,
          metadata: {
            topic,
            campaign_name,
            platform,
            target_duration,
            actual_duration: blocks.reduce((sum, b) => sum + b.duration, 0),
            block_count: blocks.length,
            loaded_at: new Date().toISOString()
          },
          source: 'database',
          cached: true
        })
      } else {
        console.log(`ℹ️ 저장된 스크립트가 없습니다. 새로 생성합니다...`)
      }
    }

    // Anthropic API 직접 호출로 스크립트 생성
    const generatedScripts = await generateScriptWithAnthropic({
      topic,
      campaign_name,
      platform,
      target_duration
    })

    // AI 콘티 블록 자동 분할
    const blocks = await generateStoryboardBlocks(
      generatedScripts.hook,
      generatedScripts.body,
      generatedScripts.cta,
      target_duration
    )

    // 데이터베이스에 저장
    if (content_id) {
      await saveGeneratedScript({
        content_id,
        hook: generatedScripts.hook,
        body: generatedScripts.body,
        cta: generatedScripts.cta,
        total_duration: target_duration
      })
    }

    return Response.json({
      success: true,
      hook: generatedScripts.hook,
      script: generatedScripts.body,
      cta: generatedScripts.cta,
      blocks,
      metadata: {
        topic,
        campaign_name,
        platform,
        target_duration,
        actual_duration: blocks.reduce((sum, b) => sum + b.duration, 0),
        block_count: blocks.length,
        generated_at: new Date().toISOString()
      },
      source: 'generated'
    })
  } catch (error) {
    console.error('Script generation error:', error)
    return Response.json({
      success: false,
      error: '스크립트 생성 실패: ' + (error as Error).message
    }, { status: 500 })
  }
}

// Note: 이 함수는 더 이상 사용되지 않습니다 (백엔드 Writer Agent 사용)
// 백엔드 API: /api/v1/writer/generate

// AI 콘티 블록 자동 분할
async function generateStoryboardBlocks(
  hook: string,
  body: string,
  cta: string,
  target_duration: number
) {
  const blocks = []
  let currentTime = 0
  let blockId = 0

  // 훅 블록 생성 (씬 단위로 분할)
  const hookScenes = splitIntoScenes(hook, 'hook')
  for (const scene of hookScenes) {
    const duration = estimateSceneDuration(scene.content)
    blocks.push({
      id: `block-${blockId++}`,
      type: 'hook',
      content: scene.content,
      duration,
      scene_type: scene.scene_type,
      visual_suggestion: scene.visual_suggestion,
      effects: {
        fadeIn: currentTime === 0,
        zoomIn: scene.scene_type === 'attention_grabber'
      },
      timing: {
        start: currentTime,
        end: currentTime + duration
      },
      order: blocks.length
    })
    currentTime += duration
  }

  // 본문 블록 생성 (주제별로 분할)
  const bodyScenes = splitIntoScenes(body, 'body')
  for (const scene of bodyScenes) {
    const duration = estimateSceneDuration(scene.content)
    blocks.push({
      id: `block-${blockId++}`,
      type: 'body',
      content: scene.content,
      duration,
      scene_type: scene.scene_type,
      visual_suggestion: scene.visual_suggestion,
      effects: {
        slide: scene.scene_type === 'transition' ? 'left' : null
      },
      timing: {
        start: currentTime,
        end: currentTime + duration
      },
      order: blocks.length
    })
    currentTime += duration
  }

  // CTA 블록 생성
  const ctaScenes = splitIntoScenes(cta, 'cta')
  for (const scene of ctaScenes) {
    const duration = estimateSceneDuration(scene.content)
    blocks.push({
      id: `block-${blockId++}`,
      type: 'cta',
      content: scene.content,
      duration,
      scene_type: scene.scene_type,
      visual_suggestion: scene.visual_suggestion,
      effects: {
        highlight: true,
        fadeOut: currentTime + duration >= target_duration * 0.95
      },
      timing: {
        start: currentTime,
        end: currentTime + duration
      },
      order: blocks.length
    })
    currentTime += duration
  }

  // 🔧 타임라인 재조정: 목표 시간과 실제 시간 차이를 보정
  const actualDuration = currentTime
  const scaleFactor = target_duration / actualDuration

  // 오차가 10% 이상이면 모든 블록의 duration을 비율로 조정
  if (Math.abs(scaleFactor - 1) > 0.1) {
    let adjustedTime = 0
    blocks.forEach(block => {
      const oldDuration = block.duration
      const newDuration = Math.max(3, Math.round(oldDuration * scaleFactor))
      block.duration = newDuration
      block.timing.start = adjustedTime
      block.timing.end = adjustedTime + newDuration
      adjustedTime += newDuration
    })
  }

  return blocks
}

// 씬 단위로 분할 (AI 로직)
function splitIntoScenes(text: string, type: 'hook' | 'body' | 'cta') {
  // TODO: 실제로는 OpenAI API로 씬 분할
  // 여기서는 간단한 로직으로 구현

  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim())
  const scenes = []

  if (type === 'hook') {
    // 훅: 문제 제기 → 호기심 유발
    scenes.push({
      content: sentences[0] + '.',
      scene_type: 'attention_grabber',
      visual_suggestion: '임팩트 있는 비주얼, 강렬한 색상'
    })
    if (sentences[1]) {
      scenes.push({
        content: sentences.slice(1).join('. ') + '.',
        scene_type: 'curiosity',
        visual_suggestion: '질문을 던지는 비주얼'
      })
    }
  } else if (type === 'body') {
    // 본문: 주제별로 분할 (2-3문장씩)
    for (let i = 0; i < sentences.length; i += 2) {
      const content = sentences.slice(i, i + 2).join('. ') + '.'
      scenes.push({
        content,
        scene_type: i === 0 ? 'introduction' : 'explanation',
        visual_suggestion: `주제 ${Math.floor(i / 2) + 1} 관련 이미지/영상`
      })
    }
  } else {
    // CTA: 행동 유도
    scenes.push({
      content: text,
      scene_type: 'call_to_action',
      visual_suggestion: '구독/좋아요 버튼, 채널 로고'
    })
  }

  return scenes
}

// 씬 길이 추정
function estimateSceneDuration(content: string): number {
  const koreanChars = (content.match(/[가-힣]/g) || []).length
  const englishWords = (content.match(/[a-zA-Z]+/g) || []).length

  // 초당 6.5자 (한글), 3.5자 (영어)로 계산 (최소 3초 제한 고려)
  const koreanDuration = koreanChars / 6.5
  const englishDuration = englishWords / 3.5

  return Math.max(3, Math.ceil(koreanDuration + englishDuration))
}


import { getScriptByContentId, saveGeneratedScript } from '@/lib/db/service'

// Anthropic API를 직접 호출하여 스크립트 생성
async function generateScriptWithAnthropic({
  topic,
  campaign_name,
  platform,
  target_duration
}: {
  topic: string
  campaign_name: string
  platform: string
  target_duration: number
}) {
  const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY

  if (!ANTHROPIC_API_KEY) {
    throw new Error('ANTHROPIC_API_KEY가 설정되지 않았습니다')
  }

  const prompt = `당신은 ${platform} 플랫폼을 위한 전문 스크립트 작가입니다.

주제: ${topic}
캠페인명: ${campaign_name}
목표 영상 길이: ${target_duration}초

다음 형식으로 영상 스크립트를 작성해주세요:

### 훅 (Hook)
[시청자의 관심을 끄는 첫 3-5초 분량의 내용]

### 본문 (Body)
[주제에 대한 상세한 설명과 정보를 담은 메인 콘텐츠]

### CTA (Call-to-Action)
[구독, 좋아요, 댓글 등을 유도하는 마무리 멘트]

주의사항:
- ${platform} 플랫폼에 최적화된 톤과 스타일로 작성
- 총 ${target_duration}초 분량에 맞게 작성 (한국어 기준 초당 약 6.5자)
- 자연스럽고 대화체로 작성
- 구체적이고 흥미로운 내용으로 작성`

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 4096,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ]
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(`Anthropic API 호출 실패: ${error.error?.message || 'Unknown error'}`)
  }

  const data = await response.json()
  const generatedText = data.content[0].text

  // 생성된 텍스트에서 훅, 본문, CTA 분리
  const hookMatch = generatedText.match(/### 훅[\s\S]*?\n([\s\S]*?)(?=\n### |$)/i)
  const bodyMatch = generatedText.match(/### 본문[\s\S]*?\n([\s\S]*?)(?=\n### |$)/i)
  const ctaMatch = generatedText.match(/### CTA[\s\S]*?\n([\s\S]*?)(?=\n### |$)/i)

  return {
    hook: hookMatch ? hookMatch[1].trim() : '',
    body: bodyMatch ? bodyMatch[1].trim() : generatedText,
    cta: ctaMatch ? ctaMatch[1].trim() : ''
  }
}
