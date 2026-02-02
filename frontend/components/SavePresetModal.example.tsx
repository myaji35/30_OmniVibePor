/**
 * SavePresetModal 사용 예시
 *
 * 이 파일은 SavePresetModal 컴포넌트의 사용법을 보여줍니다.
 */

'use client';

import React, { useState } from 'react';
import SavePresetModal from './SavePresetModal';

export default function SavePresetModalExample() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [savedPresetId, setSavedPresetId] = useState<string | null>(null);

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handlePresetSaved = (presetId: string) => {
    console.log('Preset saved with ID:', presetId);
    setSavedPresetId(presetId);

    // 토스트 알림 표시 (선택 사항)
    alert(`프리셋이 저장되었습니다! (ID: ${presetId})`);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">SavePresetModal 사용 예시</h1>

      <div className="space-y-4">
        <div>
          <button
            onClick={handleOpenModal}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
          >
            프리셋 저장 모달 열기
          </button>
        </div>

        {savedPresetId && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700">
              마지막으로 저장된 프리셋 ID: <strong>{savedPresetId}</strong>
            </p>
          </div>
        )}

        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">사용법</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
            <li>"프리셋 저장 모달 열기" 버튼 클릭</li>
            <li>프리셋 이름 입력 (필수, 최대 50자)</li>
            <li>설명 입력 (선택, 최대 200자)</li>
            <li>즐겨찾기 토글 선택 (선택)</li>
            <li>"설정 미리보기" 클릭하여 저장될 설정 확인</li>
            <li>"저장" 버튼 클릭하여 프리셋 저장</li>
          </ol>
        </div>

        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Props 설명</h2>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>
              <strong>projectId</strong> (string): 현재 프로젝트의 ID
            </li>
            <li>
              <strong>isOpen</strong> (boolean): 모달 열림/닫힘 상태
            </li>
            <li>
              <strong>onClose</strong> (function): 모달 닫기 콜백
            </li>
            <li>
              <strong>onSaved</strong> (function, 선택): 프리셋 저장 성공 시 콜백 (presetId를 인자로 받음)
            </li>
          </ul>
        </div>

        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">주의사항</h2>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-700">
            <li>프로젝트 ID가 유효해야 프로젝트 설정을 불러올 수 있습니다.</li>
            <li>백엔드 API 엔드포인트가 구현되어 있어야 정상 작동합니다.</li>
            <li>프리셋 이름은 필수 입력 항목입니다.</li>
            <li>모달 외부 클릭 시 자동으로 닫힙니다.</li>
          </ul>
        </div>
      </div>

      {/* SavePresetModal 컴포넌트 */}
      <SavePresetModal
        projectId="example-project-id-123"
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSaved={handlePresetSaved}
      />
    </div>
  );
}

/**
 * 실제 프로젝트에서 사용하는 예시:
 *
 * import SavePresetModal from '@/components/SavePresetModal';
 *
 * function MyProjectPage() {
 *   const [isModalOpen, setIsModalOpen] = useState(false);
 *   const projectId = useParams().projectId; // 또는 다른 방식으로 프로젝트 ID 가져오기
 *
 *   return (
 *     <>
 *       <button onClick={() => setIsModalOpen(true)}>
 *         프리셋으로 저장
 *       </button>
 *
 *       <SavePresetModal
 *         projectId={projectId}
 *         isOpen={isModalOpen}
 *         onClose={() => setIsModalOpen(false)}
 *         onSaved={(presetId) => {
 *           console.log('Saved preset:', presetId);
 *           // 프리셋 목록 갱신 등의 추가 작업
 *         }}
 *       />
 *     </>
 *   );
 * }
 */
