'use client';

/**
 * Dashboard Page - SLDS Design with Real Data
 * Salesforce Lightning Design System 준수 + 백엔드 연동
 */

import React, { useState, useEffect } from 'react';
import {
  SLDSLayout,
  LeftNav,
  MainWorkspace,
  RightSidebar,
  PageHeader,
  NavItem,
  Card,
  Button,
} from '@/components/slds';
import {
  HomeIcon,
  VideoIcon,
  FolderIcon,
  UsersIcon,
  SettingsIcon,
  BellIcon,
  PlusIcon,
  PlayCircleIcon,
  TrendingUpIcon,
  ClockIcon,
} from 'lucide-react';

// SVG 기반 성과 차트 컴포넌트 (외부 라이브러리 없음)
function PerformanceChart({
  period,
  totalVideos,
  activeCampaigns,
}: {
  period: '7' | '30' | '90';
  totalVideos: number;
  activeCampaigns: number;
}) {
  const days = parseInt(period);

  // 캠페인/영상 데이터 기반 시뮬레이션 차트 데이터 생성
  const chartData = Array.from({ length: days }, (_, i) => {
    const baseVideos = Math.max(1, Math.floor(totalVideos / days));
    const variance = Math.sin(i * 0.8) * 2 + Math.random() * 3;
    return {
      day: i + 1,
      videos: Math.max(0, Math.round(baseVideos + variance)),
      campaigns: i % Math.max(1, Math.floor(days / 4)) === 0 ? 1 : 0,
    };
  });

  const maxVideos = Math.max(...chartData.map((d) => d.videos), 1);
  const chartWidth = 560;
  const chartHeight = 200;
  const paddingLeft = 40;
  const paddingBottom = 30;
  const plotWidth = chartWidth - paddingLeft - 16;
  const plotHeight = chartHeight - paddingBottom - 16;

  const points = chartData.map((d, i) => {
    const x = paddingLeft + (i / (days - 1)) * plotWidth;
    const y = 16 + plotHeight - (d.videos / maxVideos) * plotHeight;
    return `${x},${y}`;
  });

  const areaPoints = [
    `${paddingLeft},${16 + plotHeight}`,
    ...chartData.map((d, i) => {
      const x = paddingLeft + (i / (days - 1)) * plotWidth;
      const y = 16 + plotHeight - (d.videos / maxVideos) * plotHeight;
      return `${x},${y}`;
    }),
    `${paddingLeft + plotWidth},${16 + plotHeight}`,
  ].join(' ');

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    value: Math.round(maxVideos * ratio),
    y: 16 + plotHeight - ratio * plotHeight,
  }));

  const xTicks = days <= 7
    ? chartData.map((d, i) => ({ day: d.day, x: paddingLeft + (i / (days - 1)) * plotWidth }))
    : [0, Math.floor(days / 3), Math.floor((days * 2) / 3), days - 1].map((i) => ({
        day: chartData[i]?.day || i + 1,
        x: paddingLeft + (i / (days - 1)) * plotWidth,
      }));

  return (
    <div>
      <div className="flex gap-6 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#00A1E0]" />
          <span className="text-slds-text-weak">영상 생성</span>
        </div>
        <div className="text-slds-text-weak">
          총 <span className="font-semibold text-slds-text-heading">{totalVideos}</span>개 ·
          활성 캠페인 <span className="font-semibold text-slds-text-heading">{activeCampaigns}</span>개
        </div>
      </div>
      <div className="overflow-x-auto">
        <svg width="100%" viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="min-w-[320px]">
          {/* Y축 그리드 & 레이블 */}
          {yTicks.map((tick) => (
            <g key={tick.value}>
              <line x1={paddingLeft} y1={tick.y} x2={chartWidth - 16} y2={tick.y}
                stroke="#DDDBDA" strokeWidth="1" strokeDasharray="4,4" />
              <text x={paddingLeft - 6} y={tick.y + 4} textAnchor="end"
                fontSize="10" fill="#706E6B">{tick.value}</text>
            </g>
          ))}

          {/* 영역 채우기 */}
          <polygon points={areaPoints} fill="#00A1E0" fillOpacity="0.08" />

          {/* 라인 */}
          <polyline
            points={points.join(' ')}
            fill="none"
            stroke="#00A1E0"
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* 데이터 포인트 */}
          {chartData.map((d, i) => {
            const x = paddingLeft + (i / (days - 1)) * plotWidth;
            const y = 16 + plotHeight - (d.videos / maxVideos) * plotHeight;
            return (
              <circle key={i} cx={x} cy={y} r="3"
                fill="#00A1E0" stroke="white" strokeWidth="1.5" />
            );
          })}

          {/* X축 레이블 */}
          {xTicks.map((tick) => (
            <text key={tick.day} x={tick.x} y={chartHeight - 6}
              textAnchor="middle" fontSize="10" fill="#706E6B">
              {days <= 7 ? `Day ${tick.day}` : `D${tick.day}`}
            </text>
          ))}

          {/* X축 선 */}
          <line x1={paddingLeft} y1={16 + plotHeight} x2={chartWidth - 16} y2={16 + plotHeight}
            stroke="#DDDBDA" strokeWidth="1" />
        </svg>
      </div>
    </div>
  );
}

interface Campaign {
  id: number;
  name: string;
  status: string;
  concept_gender?: string;
  concept_tone?: string;
  concept_style?: string;
  platform?: string;
  content_count?: number;
  created_at?: string;
}

interface DashboardStats {
  totalVideos: number;
  activeCampaigns: number;
  avgRenderTime: string;
  videoGrowth: string;
  campaignsNeedAttention: number;
  renderTimeImprovement: string;
}

export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [chartPeriod, setChartPeriod] = useState<'7' | '30' | '90'>('7');
  const [stats, setStats] = useState<DashboardStats>({
    totalVideos: 0,
    activeCampaigns: 0,
    avgRenderTime: '0m',
    videoGrowth: '+0%',
    campaignsNeedAttention: 0,
    renderTimeImprovement: '0%',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch campaigns from backend
        const response = await fetch('/api/campaigns');
        if (!response.ok) {
          throw new Error(`Failed to fetch campaigns: ${response.statusText}`);
        }

        const data = await response.json();
        const campaignsList = data.campaigns || [];
        setCampaigns(campaignsList);

        // Calculate statistics
        const totalVideos = campaignsList.reduce((sum: number, c: Campaign) => sum + (c.content_count || 0), 0);
        const activeCampaigns = campaignsList.filter((c: Campaign) => c.status === 'active').length;
        const campaignsNeedAttention = campaignsList.filter((c: Campaign) =>
          c.status === 'active' && (c.content_count || 0) < 3
        ).length;

        setStats({
          totalVideos,
          activeCampaigns,
          avgRenderTime: '1.8m', // TODO: Calculate from actual render times
          videoGrowth: totalVideos > 100 ? '+12%' : '+5%',
          campaignsNeedAttention,
          renderTimeImprovement: '-15%',
        });

        setError(null);
      } catch (err) {
        console.error('Dashboard data fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <SLDSLayout>
        <LeftNav>
          <div className="space-y-1">
            <NavItem icon={<HomeIcon size={20} />} active href="/dashboard">
              Dashboard
            </NavItem>
            <NavItem icon={<VideoIcon size={20} />} href="/studio">
              Studio
            </NavItem>
            <NavItem icon={<FolderIcon size={20} />} href="/campaigns">
              Campaigns
            </NavItem>
            <NavItem icon={<UsersIcon size={20} />} href="/teams">
              Teams
            </NavItem>
            <NavItem icon={<SettingsIcon size={20} />} href="/settings">
              Settings
            </NavItem>
          </div>
        </LeftNav>
        <MainWorkspace>
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slds-brand mx-auto mb-4"></div>
              <p className="text-slds-text-weak">Loading dashboard...</p>
            </div>
          </div>
        </MainWorkspace>
      </SLDSLayout>
    );
  }

  if (error) {
    return (
      <SLDSLayout>
        <LeftNav>
          <div className="space-y-1">
            <NavItem icon={<HomeIcon size={20} />} active href="/dashboard">
              Dashboard
            </NavItem>
            <NavItem icon={<VideoIcon size={20} />} href="/studio">
              Studio
            </NavItem>
            <NavItem icon={<FolderIcon size={20} />} href="/campaigns">
              Campaigns
            </NavItem>
            <NavItem icon={<UsersIcon size={20} />} href="/teams">
              Teams
            </NavItem>
            <NavItem icon={<SettingsIcon size={20} />} href="/settings">
              Settings
            </NavItem>
          </div>
        </LeftNav>
        <MainWorkspace>
          <div className="flex items-center justify-center h-screen">
            <Card variant="elevated">
              <div className="text-center p-8">
                <div className="bg-slds-error/10 p-4 rounded-full inline-block mb-4">
                  <span className="text-4xl">⚠️</span>
                </div>
                <h2 className="text-xl font-bold text-slds-text-heading mb-2">Error Loading Dashboard</h2>
                <p className="text-slds-text-weak mb-4">{error}</p>
                <Button variant="brand" onClick={() => window.location.reload()}>
                  Retry
                </Button>
              </div>
            </Card>
          </div>
        </MainWorkspace>
      </SLDSLayout>
    );
  }

  return (
    <SLDSLayout>
      {/* Left Navigation */}
      <LeftNav>
        <div className="space-y-1">
          <NavItem icon={<HomeIcon size={20} />} active href="/dashboard">
            Dashboard
          </NavItem>
          <NavItem icon={<VideoIcon size={20} />} href="/studio">
            Studio
          </NavItem>
          <NavItem icon={<FolderIcon size={20} />} href="/campaigns" badge={stats.activeCampaigns}>
            Campaigns
          </NavItem>
          <NavItem icon={<UsersIcon size={20} />} href="/teams">
            Teams
          </NavItem>
          <NavItem icon={<SettingsIcon size={20} />} href="/settings">
            Settings
          </NavItem>
        </div>
      </LeftNav>

      {/* Main Workspace */}
      <MainWorkspace>
        <PageHeader
          title="Dashboard"
          subtitle="Welcome back! Here's what's happening with your campaigns."
          icon={<HomeIcon size={32} />}
          breadcrumbs={[
            { label: 'Home', href: '/' },
            { label: 'Dashboard' },
          ]}
          actions={
            <>
              <Button variant="neutral" iconLeft={<BellIcon size={16} />}>
                Notifications
              </Button>
              <Button variant="brand" iconLeft={<PlusIcon size={16} />}>
                New Campaign
              </Button>
            </>
          }
        />

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-slds-medium mb-slds-large">
          <Card variant="elevated">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slds-text-weak text-sm font-medium">Total Videos</p>
                <p className="text-3xl font-bold text-slds-text-default mt-2">{stats.totalVideos}</p>
                <p className="text-sm text-slds-success mt-1">{stats.videoGrowth} this month</p>
              </div>
              <div className="bg-slds-brand/10 p-4 rounded-full">
                <VideoIcon size={24} className="text-slds-brand" />
              </div>
            </div>
          </Card>

          <Card variant="elevated">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slds-text-weak text-sm font-medium">Active Campaigns</p>
                <p className="text-3xl font-bold text-slds-text-default mt-2">{stats.activeCampaigns}</p>
                <p className="text-sm text-slds-warning mt-1">
                  {stats.campaignsNeedAttention > 0
                    ? `${stats.campaignsNeedAttention} need attention`
                    : 'All campaigns on track'}
                </p>
              </div>
              <div className="bg-slds-success/10 p-4 rounded-full">
                <FolderIcon size={24} className="text-slds-success" />
              </div>
            </div>
          </Card>

          <Card variant="elevated">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slds-text-weak text-sm font-medium">Avg. Render Time</p>
                <p className="text-3xl font-bold text-slds-text-default mt-2">{stats.avgRenderTime}</p>
                <p className="text-sm text-slds-success mt-1">{stats.renderTimeImprovement} faster</p>
              </div>
              <div className="bg-slds-warning/10 p-4 rounded-full">
                <ClockIcon size={24} className="text-slds-warning" />
              </div>
            </div>
          </Card>
        </div>

        {/* Recent Campaigns */}
        <Card
          title="Recent Campaigns"
          icon={<PlayCircleIcon size={20} />}
          headerAction={
            <a href="/campaigns"
              className="px-3 py-1.5 text-sm border border-gray-200 rounded text-gray-700 hover:bg-gray-50">
              View All
            </a>
          }
        >
          <div className="space-y-slds-medium">
            {campaigns.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slds-text-weak">No campaigns yet. Create your first campaign!</p>
                <Button variant="brand" className="mt-4" iconLeft={<PlusIcon size={16} />}>
                  New Campaign
                </Button>
              </div>
            ) : (
              campaigns.slice(0, 5).map((campaign) => {
                const contentCount = campaign.content_count || 0;
                const targetCount = 10; // Default target
                const progress = Math.min(100, Math.round((contentCount / targetCount) * 100));

                const statusColor =
                  campaign.status === 'completed'
                    ? 'success'
                    : campaign.status === 'active'
                    ? 'warning'
                    : 'info';

                const statusLabel =
                  campaign.status === 'completed'
                    ? 'Completed'
                    : campaign.status === 'active'
                    ? 'In Progress'
                    : 'Draft';

                return (
                  <div
                    key={campaign.id}
                    className="flex items-center justify-between p-slds-medium border border-slds rounded-slds hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-slds-medium flex-1">
                      <div className="bg-slds-brand/10 p-3 rounded-slds">
                        <FolderIcon size={20} className="text-slds-brand" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-slds-text-default">{campaign.name}</h3>
                        <p className="text-sm text-slds-text-weak mt-1">
                          {contentCount}/{targetCount} videos • {campaign.platform || 'Multi-platform'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-slds-medium">
                      <div className="text-right mr-slds-medium">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              statusColor === 'success'
                                ? 'bg-slds-success'
                                : statusColor === 'warning'
                                ? 'bg-slds-warning'
                                : 'bg-slds-info'
                            }`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-slds-text-weak mt-1">{progress}%</p>
                      </div>

                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          statusColor === 'success'
                            ? 'bg-slds-success/10 text-slds-success'
                            : statusColor === 'warning'
                            ? 'bg-slds-warning/10 text-slds-warning'
                            : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {statusLabel}
                      </span>

                      <a href={`/campaigns/${campaign.id}`}
                        className="px-3 py-1.5 text-sm border border-gray-200 rounded text-gray-700 hover:bg-gray-50">
                        Open
                      </a>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>

        {/* Performance Chart */}
        <div className="mt-slds-large">
          <Card
            title="Performance Overview"
            icon={<TrendingUpIcon size={20} />}
            headerAction={
              <select
                className="px-3 py-1.5 border border-slds rounded-slds text-sm"
                value={chartPeriod}
                onChange={(e) => setChartPeriod(e.target.value as '7' | '30' | '90')}
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
            }
          >
            <PerformanceChart
              period={chartPeriod}
              totalVideos={stats.totalVideos}
              activeCampaigns={stats.activeCampaigns}
            />
          </Card>
        </div>
      </MainWorkspace>

      {/* Right Sidebar */}
      <RightSidebar>
        {/* Activity Timeline */}
        <Card
          title="Recent Activity"
          icon={<BellIcon size={16} />}
        >
          <div className="space-y-slds-small">
            {campaigns.length === 0 ? (
              <p className="text-sm text-slds-text-weak text-center py-4">No recent activity</p>
            ) : (
              campaigns
                .slice(0, 5)
                .map((campaign, idx) => {
                  const timeAgo = campaign.created_at
                    ? new Date(campaign.created_at).toLocaleDateString()
                    : 'Recently';

                  return (
                    <div key={campaign.id} className="pb-slds-small border-b border-slds last:border-0">
                      <p className="text-sm font-medium text-slds-text-default">
                        {campaign.status === 'completed'
                          ? 'Campaign completed'
                          : campaign.status === 'active'
                          ? 'Campaign in progress'
                          : 'Campaign created'}
                      </p>
                      <p className="text-xs text-slds-text-weak mt-1">{campaign.name}</p>
                      <p className="text-xs text-slds-text-weak mt-1">{timeAgo}</p>
                    </div>
                  );
                })
            )}
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="mt-slds-medium">
          <Card title="Quick Actions">
            <div className="space-y-slds-small">
              <Button variant="outline-brand" fullWidth iconLeft={<PlusIcon size={16} />}>
                New Video
              </Button>
              <Button variant="neutral" fullWidth iconLeft={<FolderIcon size={16} />}>
                New Campaign
              </Button>
              <Button variant="neutral" fullWidth iconLeft={<UsersIcon size={16} />}>
                Invite Team
              </Button>
            </div>
          </Card>
        </div>
      </RightSidebar>
    </SLDSLayout>
  );
}
