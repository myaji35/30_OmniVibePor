# Salesforce Lightning Design System (SLDS) Components

> **OmniVibe Pro의 전문가급 UI 컴포넌트 라이브러리**

## 📋 Overview

Salesforce Lightning Design System을 기반으로 한 재사용 가능한 React 컴포넌트 라이브러리입니다.
모든 컴포넌트는 TypeScript로 작성되었으며, Tailwind CSS를 사용합니다.

## 🎨 Design Tokens

### Colors
```css
--slds-brand: #00A1E0           /* Primary Brand Color */
--slds-brand-dark: #0070D2      /* Hover/Active State */
--slds-success: #4BCA81         /* Success Messages */
--slds-warning: #FFB75D         /* Warning Messages */
--slds-error: #EA001E           /* Error Messages */
--slds-info: #5867E8            /* Info Messages */
```

### Spacing (8px Grid)
```css
--slds-xxx-small: 0.125rem      /* 2px */
--slds-xx-small: 0.25rem        /* 4px */
--slds-x-small: 0.5rem          /* 8px */
--slds-small: 0.75rem           /* 12px */
--slds-medium: 1rem             /* 16px - 기본 패딩 */
--slds-large: 1.5rem            /* 24px */
--slds-x-large: 2rem            /* 32px */
--slds-xx-large: 3rem           /* 48px */
```

## 📦 Components

### Base Components

#### Button
```tsx
import { Button } from '@/components/slds';

// Variants
<Button variant="brand">Primary Action</Button>
<Button variant="neutral">Secondary Action</Button>
<Button variant="destructive">Delete</Button>
<Button variant="success">Confirm</Button>
<Button variant="outline-brand">Outline</Button>

// Sizes
<Button size="small">Small</Button>
<Button size="medium">Medium</Button>
<Button size="large">Large</Button>

// With Icon
<Button
  variant="brand"
  icon={<PlusIcon className="w-4 h-4" />}
  iconPosition="left"
>
  New Campaign
</Button>
```

#### Badge
```tsx
import { Badge } from '@/components/slds';

<Badge variant="success">Published</Badge>
<Badge variant="warning">In Progress</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="info">Draft</Badge>
```

#### Input
```tsx
import { Input } from '@/components/slds';

<Input
  label="Campaign Name"
  placeholder="Enter campaign name..."
  helperText="This will be visible to your team"
/>

<Input
  label="Email"
  type="email"
  error="Invalid email format"
/>

<Input
  icon={<SearchIcon className="w-4 h-4" />}
  placeholder="Search..."
/>
```

### Layout Components

#### Card
```tsx
import { Card } from '@/components/slds';

// Basic Card
<Card title="Campaign Stats">
  <p>Your content here...</p>
</Card>

// With Icon & Action
<Card
  title="Recent Campaigns"
  icon={<VideoIcon className="w-5 h-5" />}
  headerAction={
    <Button variant="neutral" size="small">View All</Button>
  }
>
  <p>Content here...</p>
</Card>

// With Footer
<Card
  title="Performance"
  footer={
    <a href="#">View detailed report →</a>
  }
>
  <p>Content here...</p>
</Card>
```

### Feedback Components

#### ProgressBar
```tsx
import { ProgressBar } from '@/components/slds';

// Basic
<ProgressBar value={60} />

// With Label
<ProgressBar value={85} showLabel />

// Variants
<ProgressBar value={100} variant="success" />
<ProgressBar value={50} variant="warning" />
<ProgressBar value={25} variant="error" />

// Sizes
<ProgressBar value={60} size="small" />
<ProgressBar value={60} size="medium" />
<ProgressBar value={60} size="large" />
```

## 🚀 Usage Example

```tsx
'use client';

import React from 'react';
import { Card, Button, ProgressBar, Badge } from '@/components/slds';
import { VideoIcon, PlusIcon } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-slds-background p-slds-large">
      {/* Page Header */}
      <div className="mb-slds-large">
        <h1 className="text-slds-heading-large text-slds-text-heading">
          Dashboard
        </h1>
        <p className="text-slds-body-regular text-slds-text-weak">
          Overview of your campaigns
        </p>
      </div>

      {/* Quick Actions */}
      <Card title="Quick Actions" className="mb-slds-large">
        <div className="flex gap-slds-small">
          <Button variant="brand" icon={<PlusIcon className="w-4 h-4" />}>
            New Campaign
          </Button>
          <Button variant="outline-brand" icon={<VideoIcon className="w-4 h-4" />}>
            Generate Video
          </Button>
        </div>
      </Card>

      {/* Campaign Card */}
      <Card
        title="Recent Campaign"
        icon={<VideoIcon className="w-5 h-5" />}
        headerAction={<Badge variant="warning">In Progress</Badge>}
      >
        <div className="space-y-slds-small">
          <p className="text-slds-body-regular text-slds-text-heading">
            신제품 런칭 캠페인
          </p>
          <p className="text-slds-body-small text-slds-text-weak">
            3/5 videos done
          </p>
          <ProgressBar value={60} showLabel />
        </div>
      </Card>
    </div>
  );
}
```

## 🎯 Best Practices

### 1. Consistent Spacing
항상 SLDS spacing 토큰을 사용하세요:
```tsx
// ✅ Good
<div className="p-slds-medium mb-slds-large">

// ❌ Bad
<div className="p-4 mb-6">
```

### 2. Semantic Colors
상태에 맞는 색상을 사용하세요:
```tsx
// ✅ Good
<Badge variant="success">Published</Badge>
<Badge variant="error">Failed</Badge>

// ❌ Bad
<Badge className="bg-green-500">Published</Badge>
```

### 3. Accessibility
모든 interactive 요소에 적절한 label을 제공하세요:
```tsx
// ✅ Good
<Button aria-label="Delete campaign">
  <TrashIcon />
</Button>

// ❌ Bad
<button onClick={handleDelete}>
  <TrashIcon />
</button>
```

### 4. Responsive Design
Tailwind의 responsive utilities를 활용하세요:
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-slds-medium">
  {/* Cards */}
</div>
```

## 🔧 Development

### Adding New Components

1. 새 컴포넌트 파일 생성:
```bash
touch components/slds/base/NewComponent.tsx
```

2. 컴포넌트 작성:
```tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface NewComponentProps {
  // props...
}

export const NewComponent: React.FC<NewComponentProps> = (props) => {
  return (
    <div className={cn('base-styles', props.className)}>
      {/* component content */}
    </div>
  );
};
```

3. Export 추가:
```tsx
// components/slds/index.ts
export { NewComponent } from './base/NewComponent';
```

### Testing

```bash
# 개발 서버 실행
npm run dev

# TypeScript 타입 체크
npm run type-check

# Lint
npm run lint
```

## 📚 Resources

- [Salesforce Lightning Design System](https://www.lightningdesignsystem.com)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)

## 📝 License

Internal use only - Gagahoho, Inc.
