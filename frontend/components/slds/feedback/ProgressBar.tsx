'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
}

export const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  ({ className, value, max = 100, variant = 'default', showLabel = false, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    const variantStyles = {
      default: 'bg-slds-brand',
      success: 'bg-slds-success',
      warning: 'bg-slds-warning',
      error: 'bg-slds-error'
    };

    return (
      <div ref={ref} className={cn('w-full', className)} {...props}>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-300',
              variantStyles[variant]
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showLabel && (
          <div className="mt-slds-xxx-small text-xs text-slds-text-weak text-right">
            {Math.round(percentage)}%
          </div>
        )}
      </div>
    );
  }
);

ProgressBar.displayName = 'ProgressBar';
