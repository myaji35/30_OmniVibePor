import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OmniVibe Pro - AI Video Automation',
  description: 'AI-powered Omnichannel Video Automation SaaS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
