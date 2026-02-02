/**
 * ClipReplacer Component Usage Example
 *
 * This file demonstrates how to use the ClipReplacer component
 * in your production workflow or section editor.
 */

'use client';

import React from 'react';
import ClipReplacer from './ClipReplacer';

/**
 * Example 1: Basic Usage
 *
 * Simply provide a sectionId to display the clip replacer
 */
export function BasicExample() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">섹션 클립 관리</h1>
      <ClipReplacer sectionId="section_123" />
    </div>
  );
}

/**
 * Example 2: With Callback
 *
 * Use the onClipReplaced callback to respond to clip changes
 */
export function WithCallbackExample() {
  const handleClipReplaced = (clipId: string) => {
    console.log('Clip replaced with:', clipId);
    // You can trigger other actions here:
    // - Reload the video timeline
    // - Update the production state
    // - Show a success notification
    alert(`클립이 교체되었습니다! (ID: ${clipId})`);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">섹션 클립 관리 (콜백 포함)</h1>
      <ClipReplacer
        sectionId="section_123"
        onClipReplaced={handleClipReplaced}
      />
    </div>
  );
}

/**
 * Example 3: Integration with Production Workflow
 *
 * Integrate ClipReplacer into a larger production workflow
 */
export function ProductionWorkflowExample() {
  const [selectedSectionId, setSelectedSectionId] = React.useState<string | null>(null);
  const [sections] = React.useState([
    { id: 'section_1', name: '훅', order: 1 },
    { id: 'section_2', name: '본문', order: 2 },
    { id: 'section_3', name: 'CTA', order: 3 },
  ]);

  const handleClipReplaced = (clipId: string) => {
    console.log(`Section ${selectedSectionId} clip replaced with ${clipId}`);
    // Reload video timeline, update state, etc.
  };

  return (
    <div className="container mx-auto p-4 grid grid-cols-3 gap-4">
      {/* Section List */}
      <div className="col-span-1 bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-bold mb-4">섹션 목록</h2>
        <div className="space-y-2">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setSelectedSectionId(section.id)}
              className={`
                w-full p-3 rounded-lg text-left transition-colors
                ${selectedSectionId === section.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 hover:bg-gray-200'
                }
              `}
            >
              {section.order}. {section.name}
            </button>
          ))}
        </div>
      </div>

      {/* Clip Replacer */}
      <div className="col-span-2">
        {selectedSectionId ? (
          <ClipReplacer
            sectionId={selectedSectionId}
            onClipReplaced={handleClipReplaced}
          />
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
            왼쪽에서 섹션을 선택하세요
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Example 4: Modal Integration
 *
 * Use ClipReplacer in a modal dialog
 */
export function ModalExample() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [sectionId, setSectionId] = React.useState<string>('section_123');

  return (
    <div className="container mx-auto p-4">
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
      >
        클립 관리 열기
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">클립 관리</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4">
              <ClipReplacer
                sectionId={sectionId}
                onClipReplaced={(clipId) => {
                  console.log('Replaced with:', clipId);
                  // Optionally close the modal after replacement
                  // setIsOpen(false);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
