"use client";

/**
 * ProjectList - 프로젝트 목록 UI
 *
 * REALPLAN.md Phase 1.5 구현
 *
 * 기능:
 * - 프로젝트 목록 조회 (페이징)
 * - 상태별 필터링 (draft, script_ready, production, published, archived)
 * - 프로젝트 생성 모달
 * - 프로젝트 카드 클릭 시 상세 페이지로 이동
 */

import React, { useState, useEffect } from 'react';
import { useProduction } from '@/lib/contexts/ProductionContext';

// ==================== Types ====================

interface Project {
  project_id: string;
  title: string;
  topic: string;
  platform: string;
  status: 'draft' | 'script_ready' | 'production' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
  persona_id?: string;
}

interface ProjectListProps {
  userId: string;
  onSelectProject?: (projectId: string) => void;
}

// ==================== Helper Functions ====================

function getStatusColor(status: Project['status']): string {
  const colors = {
    draft: 'bg-gray-100 text-gray-800',
    script_ready: 'bg-blue-100 text-blue-800',
    production: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800',
    archived: 'bg-red-100 text-red-800',
  };
  return colors[status];
}

function getStatusLabel(status: Project['status']): string {
  const labels = {
    draft: '초안',
    script_ready: '스크립트 완료',
    production: '제작 중',
    published: '발행됨',
    archived: '보관됨',
  };
  return labels[status];
}

function getPlatformIcon(platform: string): string {
  const icons: Record<string, string> = {
    youtube: '📺',
    instagram: '📷',
    facebook: '👥',
    tiktok: '🎵',
  };
  return icons[platform] || '🎬';
}

// ==================== Component ====================

export default function ProjectList({ userId, onSelectProject }: ProjectListProps) {
  const { setProject } = useProduction();

  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<Project['status'] | 'all'>('all');
  const [page, setPage] = useState(1);
  const [totalProjects, setTotalProjects] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const pageSize = 12;

  // 프로젝트 목록 조회
  useEffect(() => {
    fetchProjects();
  }, [userId, selectedStatus, page]);

  async function fetchProjects() {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (selectedStatus !== 'all') {
        params.append('status', selectedStatus);
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/users/${userId}/projects?${params}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.statusText}`);
      }

      const data = await response.json();
      setProjects(data.projects);
      setTotalProjects(data.total);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch projects:', err);
    } finally {
      setIsLoading(false);
    }
  }

  // 프로젝트 선택
  function handleSelectProject(project: Project) {
    setProject(project.project_id, project.title, project.topic, project.platform);

    if (onSelectProject) {
      onSelectProject(project.project_id);
    }
  }

  // 총 페이지 수
  const totalPages = Math.ceil(totalProjects / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">프로젝트</h1>
          <p className="text-gray-600 mt-1">영상 제작 프로젝트를 관리하세요</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          + 새 프로젝트
        </button>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(['all', 'draft', 'script_ready', 'production', 'published', 'archived'] as const).map(
          (status) => (
            <button
              key={status}
              onClick={() => {
                setSelectedStatus(status);
                setPage(1);
              }}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                selectedStatus === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status === 'all' ? '전체' : getStatusLabel(status as Project['status'])}
            </button>
          )
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-lg h-48 animate-pulse" />
          ))}
        </div>
      )}

      {/* Project Grid */}
      {!isLoading && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.project_id}
              onClick={() => handleSelectProject(project)}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
            >
              {/* Platform Icon & Status */}
              <div className="flex justify-between items-start mb-4">
                <span className="text-4xl">{getPlatformIcon(project.platform)}</span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    project.status
                  )}`}
                >
                  {getStatusLabel(project.status)}
                </span>
              </div>

              {/* Title */}
              <h3 className="text-xl font-semibold text-gray-900 mb-2 line-clamp-2">
                {project.title}
              </h3>

              {/* Topic */}
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.topic}</p>

              {/* Metadata */}
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>{new Date(project.created_at).toLocaleDateString('ko-KR')}</span>
                <span className="capitalize">{project.platform}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && projects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">프로젝트가 없습니다</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            첫 프로젝트 만들기
          </button>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            이전
          </button>

          <span className="px-4 py-2 text-gray-700">
            {page} / {totalPages}
          </span>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            다음
          </button>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <CreateProjectModal
          userId={userId}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchProjects();
          }}
        />
      )}
    </div>
  );
}

// ==================== Create Project Modal ====================

interface CreateProjectModalProps {
  userId: string;
  onClose: () => void;
  onSuccess: () => void;
}

function CreateProjectModal({ userId, onClose, onSuccess }: CreateProjectModalProps) {
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState<'youtube' | 'instagram' | 'facebook' | 'tiktok'>(
    'youtube'
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          title,
          topic,
          platform,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create project');
      }

      onSuccess();
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to create project:', err);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">새 프로젝트 생성</h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">제목</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: 건강한 식습관 가이드"
            />
          </div>

          {/* Topic */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">주제</label>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              maxLength={500}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="영상의 주제와 목적을 설명하세요"
            />
          </div>

          {/* Platform */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">플랫폼</label>
            <div className="grid grid-cols-2 gap-2">
              {(['youtube', 'instagram', 'facebook', 'tiktok'] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPlatform(p)}
                  className={`px-4 py-3 border rounded-lg text-center transition-colors ${
                    platform === p
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-2xl mb-1">{getPlatformIcon(p)}</div>
                  <div className="text-sm capitalize">{p}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? '생성 중...' : '생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
