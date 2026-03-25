'use client'

/**
 * ProjectContextProvider — 프로젝트 ID를 하위 트리 전체에 공급
 *
 * 사용법:
 *   const { projectId } = useProjectContext()
 */
import { createContext, useContext, ReactNode } from 'react'
import ProductionStepper from '@/components/ProductionStepper'

interface ProjectContextValue {
  projectId: string
}

const ProjectContext = createContext<ProjectContextValue>({ projectId: '' })

export function useProjectContext() {
  return useContext(ProjectContext)
}

interface Props {
  projectId: string
  children:  ReactNode
}

export default function ProjectContextProvider({ projectId, children }: Props) {
  return (
    <ProjectContext.Provider value={{ projectId }}>
      {/* 프로젝트 URL 구조에서는 항상 스테퍼 노출 */}
      <div className="px-6 py-3 border-b border-white/[0.05] bg-[#0f1117]/60">
        <ProductionStepper />
      </div>
      {children}
    </ProjectContext.Provider>
  )
}
