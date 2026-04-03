"use client";

/**
 * Production Page - 통합 프로덕션 대시보드
 *
 * REALPLAN.md Phase 2 구현
 *
 * Writer → Director → Marketer → Deployment 통합 워크플로우
 */

import React from 'react';
import { ProductionProvider } from '@/lib/contexts/ProductionContext';
import ProductionDashboard from '@/components/ProductionDashboard';
import AppShell from '@/components/AppShell';

export default function ProductionPage() {
  return (
    <AppShell>
      <ProductionProvider>
        <ProductionDashboard />
      </ProductionProvider>
    </AppShell>
  );
}
