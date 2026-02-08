'use client';

import React from 'react';
import { Card } from '@/components/slds/layout/Card';
import { Button } from '@/components/slds/base/Button';
import { ProgressBar } from '@/components/slds/feedback/ProgressBar';
import { Badge } from '@/components/slds/base/Badge';
import {
  PlusIcon,
  VideoIcon,
  TrendingUpIcon,
  UsersIcon,
  ActivityIcon,
  PlayCircleIcon,
  BarChart3Icon
} from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-slds-background p-slds-large">
      {/* Page Header */}
      <div className="mb-slds-large">
        <h1 className="text-slds-heading-large text-slds-text-heading mb-slds-x-small">
          Dashboard
        </h1>
        <p className="text-slds-body-regular text-slds-text-weak">
          Overview of your campaigns and content performance
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-slds-medium mb-slds-large">
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-slds-small">
            <div className="p-slds-small bg-slds-brand/10 rounded-slds-sm">
              <VideoIcon className="w-6 h-6 text-slds-brand" />
            </div>
            <div>
              <p className="text-slds-body-small text-slds-text-weak">Total Videos</p>
              <p className="text-2xl font-bold text-slds-text-heading">247</p>
              <p className="text-slds-body-small text-slds-success">↑ +12% from last month</p>
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-slds-small">
            <div className="p-slds-small bg-slds-success/10 rounded-slds-sm">
              <TrendingUpIcon className="w-6 h-6 text-slds-success" />
            </div>
            <div>
              <p className="text-slds-body-small text-slds-text-weak">Avg. CTR</p>
              <p className="text-2xl font-bold text-slds-text-heading">8.5%</p>
              <p className="text-slds-body-small text-slds-success">↑ +2.1% vs avg</p>
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-slds-small">
            <div className="p-slds-small bg-slds-warning/10 rounded-slds-sm">
              <UsersIcon className="w-6 h-6 text-slds-warning" />
            </div>
            <div>
              <p className="text-slds-body-small text-slds-text-weak">Active Campaigns</p>
              <p className="text-2xl font-bold text-slds-text-heading">12</p>
              <p className="text-slds-body-small text-slds-text-weak">+2 new this week</p>
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-slds-small">
            <div className="p-slds-small bg-slds-info/10 rounded-slds-sm">
              <ActivityIcon className="w-6 h-6 text-slds-info" />
            </div>
            <div>
              <p className="text-slds-body-small text-slds-text-weak">Published Today</p>
              <p className="text-2xl font-bold text-slds-text-heading">3</p>
              <Badge variant="error">🔥 Hot streak!</Badge>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card
        title="Quick Actions"
        className="mb-slds-large"
      >
        <div className="flex gap-slds-small">
          <Button variant="brand" icon={<PlusIcon className="w-4 h-4" />}>
            New Campaign
          </Button>
          <Button variant="outline-brand" icon={<VideoIcon className="w-4 h-4" />}>
            Generate Video
          </Button>
          <Button variant="neutral" icon={<BarChart3Icon className="w-4 h-4" />}>
            View Analytics
          </Button>
        </div>
      </Card>

      {/* Recent Campaigns */}
      <Card
        title="Recent Campaigns"
        icon={<PlayCircleIcon className="w-5 h-5" />}
        headerAction={
          <Button variant="neutral" size="small">View All</Button>
        }
      >
        <div className="space-y-slds-medium">
          {[
            {
              name: '신제품 런칭 캠페인',
              status: 'In Progress',
              progress: 60,
              videos: '3/5 videos done',
              badge: 'warning'
            },
            {
              name: 'MZ세대 타겟 시리즈',
              status: 'Active',
              progress: 100,
              videos: '10/10 videos done',
              badge: 'success'
            },
            {
              name: '브랜드 리뉴얼 프로모션',
              status: 'Planning',
              progress: 20,
              videos: '1/8 videos done',
              badge: 'info'
            },
          ].map((campaign, idx) => (
            <div
              key={idx}
              className="flex items-center gap-slds-medium p-slds-small border border-slds-border rounded-slds-sm hover:bg-slds-background transition-colors cursor-pointer"
            >
              <div className="flex-shrink-0 w-16 h-16 bg-slds-brand/20 rounded-slds-sm flex items-center justify-center">
                <VideoIcon className="w-8 h-8 text-slds-brand" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-slds-small mb-slds-xx-small">
                  <h3 className="text-slds-heading-small text-slds-text-heading">
                    {campaign.name}
                  </h3>
                  <Badge variant={campaign.badge as any}>{campaign.status}</Badge>
                </div>
                <p className="text-slds-body-small text-slds-text-weak mb-slds-x-small">
                  {campaign.videos}
                </p>
                <ProgressBar value={campaign.progress} showLabel />
              </div>
              <Button variant="neutral" size="small">
                Continue →
              </Button>
            </div>
          ))}
        </div>
      </Card>

      {/* Performance Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-slds-medium mt-slds-large">
        <Card
          title="Top Performing Videos"
          icon={<TrendingUpIcon className="w-5 h-5" />}
        >
          <div className="space-y-slds-small">
            {[
              { title: 'AI 에디터 완벽 가이드', views: '15.2K', ctr: '12.3%' },
              { title: '영상 제작 자동화 팁', views: '12.8K', ctr: '10.5%' },
              { title: 'MZ세대 마케팅 전략', views: '9.5K', ctr: '9.8%' },
            ].map((video, idx) => (
              <div key={idx} className="flex items-center justify-between p-slds-small bg-slds-background rounded-slds-sm">
                <div>
                  <p className="text-slds-body-regular font-medium text-slds-text-heading">
                    {video.title}
                  </p>
                  <p className="text-slds-body-small text-slds-text-weak">
                    Views: {video.views}
                  </p>
                </div>
                <Badge variant="success">CTR: {video.ctr}</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title="Recent Activity"
          icon={<ActivityIcon className="w-5 h-5" />}
        >
          <div className="space-y-slds-small">
            {[
              { action: '영상 게시됨', item: '"AI 에디터 가이드"', time: '2 hours ago' },
              { action: '캠페인 생성됨', item: '"신제품 런칭"', time: '5 hours ago' },
              { action: '스크립트 생성됨', item: '"MZ 마케팅 #3"', time: '1 day ago' },
            ].map((activity, idx) => (
              <div key={idx} className="flex items-start gap-slds-small p-slds-small">
                <div className="w-2 h-2 rounded-full bg-slds-brand mt-1.5" />
                <div className="flex-1">
                  <p className="text-slds-body-regular text-slds-text-heading">
                    {activity.action}: <span className="font-medium">{activity.item}</span>
                  </p>
                  <p className="text-slds-body-small text-slds-text-weak">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
