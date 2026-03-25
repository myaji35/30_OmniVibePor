/**
 * 프로젝트 컨텍스트 레이아웃 (N-4)
 *
 * /project/[id]/writer, /project/[id]/audio 등
 * 프로젝트 ID를 URL에 유지하면서 ProductionStepper를 공통으로 표시.
 */
import { ReactNode } from 'react'
import ProjectContextProvider from '@/components/ProjectContextProvider'

interface ProjectLayoutProps {
  children:  ReactNode
  params:    { id: string }
}

export default function ProjectLayout({ children, params }: ProjectLayoutProps) {
  return (
    <ProjectContextProvider projectId={params.id}>
      {children}
    </ProjectContextProvider>
  )
}
