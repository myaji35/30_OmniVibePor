'use client';

import React, { useRef, useEffect, useState } from 'react';
import {
  getProjectSettings,
  createCustomPreset,
  ProjectSettings,
  CreatePresetRequest,
} from '@/lib/api/presets';

interface SavePresetModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSaved?: (presetId: string) => void;
}

interface PresetFormData {
  name: string;
  description: string;
  is_favorite: boolean;
}

interface ValidationErrors {
  name?: string;
  description?: string;
}

const SavePresetModal: React.FC<SavePresetModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onSaved,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [formData, setFormData] = useState<PresetFormData>({
    name: '',
    description: '',
    is_favorite: false,
  });
  const [projectSettings, setProjectSettings] = useState<ProjectSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [showPreview, setShowPreview] = useState(false);

  // Load project settings when modal opens
  useEffect(() => {
    if (isOpen && projectId) {
      setIsLoading(true);
      getProjectSettings(projectId)
        .then((settings) => {
          setProjectSettings(settings);
        })
        .catch((error) => {
          console.error('Failed to load project settings:', error);
          setErrorMessage('프로젝트 설정을 불러오는데 실패했습니다.');
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [isOpen, projectId]);

  // Handle dialog open/close
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      dialog.showModal();
    } else {
      dialog.close();
      // Reset form when closed
      setFormData({ name: '', description: '', is_favorite: false });
      setErrors({});
      setErrorMessage('');
      setShowPreview(false);
    }
  }, [isOpen]);

  // Handle dialog close event
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClose = () => {
      onClose();
    };

    dialog.addEventListener('close', handleClose);
    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = '프리셋 이름은 필수입니다.';
    } else if (formData.name.length > 50) {
      newErrors.name = '프리셋 이름은 50자를 초과할 수 없습니다.';
    }

    // Description validation
    if (formData.description && formData.description.length > 200) {
      newErrors.description = '설명은 200자를 초과할 수 없습니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleFavoriteToggle = () => {
    setFormData((prev) => ({ ...prev, is_favorite: !prev.is_favorite }));
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    if (!projectSettings) {
      setErrorMessage('프로젝트 설정을 불러오지 못했습니다.');
      return;
    }

    setIsSaving(true);
    setErrorMessage('');

    try {
      const presetData: CreatePresetRequest = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        is_favorite: formData.is_favorite,
        settings: projectSettings,
      };

      const result = await createCustomPreset(presetData);

      // Show success toast (you can customize this)
      console.log('Preset saved successfully:', result.preset_id);

      // Call onSaved callback
      if (onSaved) {
        onSaved(result.preset_id);
      }

      // Close modal
      onClose();
    } catch (error) {
      console.error('Failed to save preset:', error);
      setErrorMessage(
        error instanceof Error ? error.message : '프리셋 저장에 실패했습니다.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const rect = dialog.getBoundingClientRect();
    const isInDialog =
      e.clientX >= rect.left &&
      e.clientX <= rect.right &&
      e.clientY >= rect.top &&
      e.clientY <= rect.bottom;

    if (!isInDialog) {
      onClose();
    }
  };

  const isFormValid = formData.name.trim().length > 0 && !errors.name && !errors.description;

  return (
    <dialog
      ref={dialogRef}
      onClick={handleBackdropClick}
      className="backdrop:bg-black backdrop:bg-opacity-70 bg-transparent p-0 max-w-2xl w-full rounded-lg"
    >
      <div className="bg-white rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">프리셋 저장</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="닫기"
          >
            <svg
              className="w-6 h-6 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Error Message */}
          {errorMessage && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{errorMessage}</p>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <svg
                className="animate-spin h-8 w-8 text-blue-500"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
          )}

          {!isLoading && (
            <>
              {/* Preset Name */}
              <div>
                <label htmlFor="preset-name" className="block text-sm font-medium text-gray-700 mb-2">
                  프리셋 이름 <span className="text-red-500">*</span>
                </label>
                <input
                  id="preset-name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  maxLength={50}
                  placeholder="예: 유튜브 쇼츠 기본 프리셋"
                  className={`
                    w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    ${errors.name ? 'border-red-500' : 'border-gray-300'}
                  `}
                />
                <div className="flex justify-between mt-1">
                  {errors.name ? (
                    <p className="text-sm text-red-500">{errors.name}</p>
                  ) : (
                    <div />
                  )}
                  <p className="text-xs text-gray-500">{formData.name.length}/50</p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="preset-description" className="block text-sm font-medium text-gray-700 mb-2">
                  설명 (선택)
                </label>
                <textarea
                  id="preset-description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  maxLength={200}
                  rows={3}
                  placeholder="프리셋에 대한 간단한 설명을 입력하세요."
                  className={`
                    w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none
                    ${errors.description ? 'border-red-500' : 'border-gray-300'}
                  `}
                />
                <div className="flex justify-between mt-1">
                  {errors.description ? (
                    <p className="text-sm text-red-500">{errors.description}</p>
                  ) : (
                    <div />
                  )}
                  <p className="text-xs text-gray-500">{formData.description.length}/200</p>
                </div>
              </div>

              {/* Favorite Toggle */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleFavoriteToggle}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${formData.is_favorite ? 'bg-blue-500' : 'bg-gray-300'}
                  `}
                  aria-label="즐겨찾기 토글"
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${formData.is_favorite ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
                <label className="text-sm font-medium text-gray-700">즐겨찾기에 추가</label>
              </div>

              {/* Settings Preview */}
              {projectSettings && (
                <div>
                  <button
                    type="button"
                    onClick={() => setShowPreview(!showPreview)}
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <svg
                      className={`w-5 h-5 transition-transform ${showPreview ? 'rotate-90' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    설정 미리보기
                  </button>

                  {showPreview && (
                    <div className="mt-3 p-4 bg-gray-50 rounded-lg space-y-3">
                      {/* Subtitle Settings */}
                      {projectSettings.subtitle_style && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-700 mb-2">자막 스타일</h4>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {projectSettings.subtitle_style.font_family && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">폰트:</span>
                                <span className="text-gray-700">{projectSettings.subtitle_style.font_family}</span>
                              </div>
                            )}
                            {projectSettings.subtitle_style.font_size && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">크기:</span>
                                <span className="text-gray-700">{projectSettings.subtitle_style.font_size}px</span>
                              </div>
                            )}
                            {projectSettings.subtitle_style.position && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">위치:</span>
                                <span className="text-gray-700">{projectSettings.subtitle_style.position}</span>
                              </div>
                            )}
                            {projectSettings.subtitle_style.alignment && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">정렬:</span>
                                <span className="text-gray-700">{projectSettings.subtitle_style.alignment}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* BGM Settings */}
                      {projectSettings.bgm_settings && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-700 mb-2">BGM 설정</h4>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {projectSettings.bgm_settings.volume !== undefined && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">볼륨:</span>
                                <span className="text-gray-700">{projectSettings.bgm_settings.volume}%</span>
                              </div>
                            )}
                            {projectSettings.bgm_settings.track_name && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">트랙:</span>
                                <span className="text-gray-700 truncate">{projectSettings.bgm_settings.track_name}</span>
                              </div>
                            )}
                            {projectSettings.bgm_settings.fade_in !== undefined && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">페이드 인:</span>
                                <span className="text-gray-700">{projectSettings.bgm_settings.fade_in}s</span>
                              </div>
                            )}
                            {projectSettings.bgm_settings.fade_out !== undefined && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">페이드 아웃:</span>
                                <span className="text-gray-700">{projectSettings.bgm_settings.fade_out}s</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Video Settings */}
                      {projectSettings.video_settings && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-700 mb-2">영상 설정</h4>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {projectSettings.video_settings.resolution && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">해상도:</span>
                                <span className="text-gray-700">{projectSettings.video_settings.resolution}</span>
                              </div>
                            )}
                            {projectSettings.video_settings.fps && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">FPS:</span>
                                <span className="text-gray-700">{projectSettings.video_settings.fps}</span>
                              </div>
                            )}
                            {projectSettings.video_settings.aspect_ratio && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">비율:</span>
                                <span className="text-gray-700">{projectSettings.video_settings.aspect_ratio}</span>
                              </div>
                            )}
                            {projectSettings.video_settings.quality && (
                              <div className="flex gap-2">
                                <span className="text-gray-500">품질:</span>
                                <span className="text-gray-700">{projectSettings.video_settings.quality}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-6 py-2 text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors font-medium disabled:opacity-50"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            disabled={!isFormValid || isSaving || isLoading}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors
              ${
                isFormValid && !isSaving && !isLoading
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {isSaving ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                저장 중...
              </span>
            ) : (
              '저장'
            )}
          </button>
        </div>
      </div>
    </dialog>
  );
};

export default SavePresetModal;
