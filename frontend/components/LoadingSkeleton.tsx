/**
 * LoadingSkeleton - 로딩 스켈레톤 UI
 *
 * REALPLAN.md Phase 2.6 구현
 *
 * 다양한 컴포넌트용 스켈레톤 제공
 */

import React from 'react';

// ==================== Base Skeleton ====================

export function Skeleton({ className = '', ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      {...props}
    />
  );
}

// ==================== Specialized Skeletons ====================

export function ProjectCardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <Skeleton className="h-12 w-12 rounded" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>

      <Skeleton className="h-6 w-3/4 mb-2" />
      <Skeleton className="h-4 w-full mb-1" />
      <Skeleton className="h-4 w-5/6 mb-4" />

      <div className="flex justify-between items-center">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}

export function ScriptEditorSkeleton() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-6">
          <div className="text-center">
            <Skeleton className="h-8 w-16 mb-1 mx-auto" />
            <Skeleton className="h-4 w-12 mx-auto" />
          </div>
          <div className="text-center">
            <Skeleton className="h-8 w-16 mb-1 mx-auto" />
            <Skeleton className="h-4 w-16 mx-auto" />
          </div>
        </div>
      </div>

      <Skeleton className="h-[500px] w-full mb-2 rounded-lg" />
      <div className="flex justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-48" />
      </div>

      <div className="flex justify-between items-center mt-6">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-12 w-48" />
      </div>
    </div>
  );
}

export function AudioPlayerSkeleton() {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <div className="flex items-start gap-4 mb-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="flex-1">
          <Skeleton className="h-5 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
      </div>
      <Skeleton className="h-12 w-full rounded" />
    </div>
  );
}

export function ProgressStepsSkeleton() {
  return (
    <div className="flex items-center justify-between">
      {[...Array(4)].map((_, i) => (
        <React.Fragment key={i}>
          <div className="flex items-center gap-3">
            <Skeleton className="h-12 w-12 rounded-full" />
            <Skeleton className="h-5 w-16" />
          </div>
          {i < 3 && <Skeleton className="flex-1 h-1 mx-2" />}
        </React.Fragment>
      ))}
    </div>
  );
}

// ==================== Layout Skeletons ====================

export function ProjectListSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-64" />
        </div>
        <Skeleton className="h-12 w-36 rounded-lg" />
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-2">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-24 rounded-lg" />
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <ProjectCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

export function ProductionDashboardSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <Skeleton className="h-8 w-64 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
            <Skeleton className="h-8 w-24 rounded-full" />
          </div>

          <ProgressStepsSkeleton />

          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
          <ScriptEditorSkeleton />
        </div>
      </main>
    </div>
  );
}
