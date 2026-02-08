'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'brand' | 'neutral' | 'destructive' | 'success' | 'outline-brand';
  size?: 'small' | 'medium' | 'large';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'brand', size = 'medium', icon, iconPosition = 'left', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-semibold rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantStyles = {
      brand: 'bg-slds-brand text-white hover:bg-slds-brand-dark focus:ring-slds-brand',
      neutral: 'bg-gray-100 text-slds-text-heading hover:bg-gray-200 focus:ring-gray-300',
      destructive: 'bg-slds-error text-white hover:bg-red-700 focus:ring-slds-error',
      success: 'bg-slds-success text-white hover:bg-green-600 focus:ring-slds-success',
      'outline-brand': 'border-2 border-slds-brand text-slds-brand bg-white hover:bg-blue-50 focus:ring-slds-brand'
    };

    const sizeStyles = {
      small: 'px-slds-small py-slds-xx-small text-sm gap-slds-xx-small',
      medium: 'px-slds-medium py-slds-x-small text-base gap-slds-x-small',
      large: 'px-slds-large py-slds-small text-lg gap-slds-small'
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {icon && iconPosition === 'left' && <span>{icon}</span>}
        {children}
        {icon && iconPosition === 'right' && <span>{icon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
