"use client";

/**
 * Subtitle Editor Page
 *
 * SubtitleEditor 컴포넌트 테스트 페이지
 */

import React from 'react';
import SubtitleEditor from '@/components/SubtitleEditor';

export default function SubtitleEditorPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto">
        <SubtitleEditor projectId="test-project-123" />
      </div>
    </div>
  );
}
