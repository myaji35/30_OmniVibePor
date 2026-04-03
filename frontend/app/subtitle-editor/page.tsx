"use client";

/**
 * Subtitle Editor Page
 *
 * SubtitleEditor 컴포넌트 테스트 페이지
 */

import React from 'react';
import SubtitleEditor from '@/components/SubtitleEditor';
import AppShell from '@/components/AppShell';

export default function SubtitleEditorPage() {
  return (
    <AppShell>
      <div className="max-w-5xl mx-auto py-8 px-6">
        <SubtitleEditor projectId="test-project-123" />
      </div>
    </AppShell>
  );
}
