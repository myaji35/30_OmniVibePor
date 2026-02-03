// 블록 관리 유틸리티 함수

import { ScriptBlock, reorderBlocks } from './types'

// 새 블록 생성
export function createBlock(
    type: ScriptBlock['type'],
    content: string = '',
    order: number = 0
): ScriptBlock {
    const id = `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    const defaultDuration = type === 'hook' ? 5 : type === 'cta' ? 5 : 10

    return {
        id,
        type,
        content: content || `${type === 'hook' ? '훅' : type === 'body' ? '본문' : 'CTA'} 스크립트를 입력하세요...`,
        duration: defaultDuration,
        effects: {
            fadeIn: type === 'hook',
            fadeOut: type === 'cta',
            highlight: type === 'cta'
        },
        media: {},
        timing: {
            start: 0,
            end: defaultDuration
        },
        order
    }
}

// 블록 복제
export function duplicateBlock(block: ScriptBlock, newOrder: number): ScriptBlock {
    return {
        ...block,
        id: `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        order: newOrder
    }
}

// 블록 삭제
export function deleteBlock(blocks: ScriptBlock[], blockId: string): ScriptBlock[] {
    return reorderBlocks(blocks.filter(b => b.id !== blockId))
}

// 블록 업데이트
export function updateBlock(
    blocks: ScriptBlock[],
    blockId: string,
    updates: Partial<ScriptBlock>
): ScriptBlock[] {
    return blocks.map(b =>
        b.id === blockId ? { ...b, ...updates } : b
    )
}

// 블록 추가
export function addBlock(
    blocks: ScriptBlock[],
    type: ScriptBlock['type'],
    position?: number
): ScriptBlock[] {
    const newBlock = createBlock(type, '', blocks.length)

    if (position !== undefined) {
        const newBlocks = [...blocks]
        newBlocks.splice(position, 0, newBlock)
        return reorderBlocks(newBlocks)
    }

    return reorderBlocks([...blocks, newBlock])
}

// 블록 이동
export function moveBlock(
    blocks: ScriptBlock[],
    fromIndex: number,
    toIndex: number
): ScriptBlock[] {
    const newBlocks = [...blocks]
    const [movedBlock] = newBlocks.splice(fromIndex, 1)
    newBlocks.splice(toIndex, 0, movedBlock)
    return reorderBlocks(newBlocks)
}

// 전체 duration 계산
export function getTotalDuration(blocks: ScriptBlock[]): number {
    return blocks.reduce((sum, block) => sum + block.duration, 0)
}

// 블록 타입별 개수 계산
export function getBlockCountByType(blocks: ScriptBlock[]): Record<ScriptBlock['type'], number> {
    return blocks.reduce((acc, block) => {
        acc[block.type] = (acc[block.type] || 0) + 1
        return acc
    }, {} as Record<ScriptBlock['type'], number>)
}
