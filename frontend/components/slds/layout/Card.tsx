'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  icon?: string | React.ReactNode;
  action?: React.ReactNode;
  footer?: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, icon, action, footer, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'bg-white rounded-lg border border-slds-border shadow-sm',
          className
        )}
        {...props}
      >
        {(title || icon || action) && (
          <div className="px-slds-medium py-slds-small border-b border-slds-border flex items-center justify-between">
            <div className="flex items-center gap-slds-x-small">
              {icon && (
                <span className="text-xl">{icon}</span>
              )}
              {title && (
                <h3 className="text-lg font-semibold text-slds-text-heading">
                  {title}
                </h3>
              )}
            </div>
            {action && <div>{action}</div>}
          </div>
        )}
        <div className="p-slds-medium">{children}</div>
        {footer && (
          <div className="px-slds-medium py-slds-small border-t border-slds-border">
            {footer}
          </div>
        )}
      </div>
    );
  }
);

Card.displayName = 'Card';
