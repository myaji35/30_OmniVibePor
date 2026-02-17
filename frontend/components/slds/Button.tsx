/**
 * SLDS Button Component
 * Salesforce Lightning Design System 표준 버튼
 */

import React, { ReactNode, ButtonHTMLAttributes } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 버튼 텍스트 */
  children: ReactNode;

  /** 버튼 변형 */
  variant?: 'brand' | 'neutral' | 'destructive' | 'success' | 'outline-brand';

  /** 버튼 크기 */
  size?: 'small' | 'medium' | 'large';

  /** 아이콘 (좌측) */
  iconLeft?: ReactNode;

  /** 아이콘 (우측) */
  iconRight?: ReactNode;

  /** 전체 너비 */
  fullWidth?: boolean;

  /** 추가 CSS 클래스 */
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'neutral',
  size = 'medium',
  iconLeft,
  iconRight,
  fullWidth = false,
  className = '',
  disabled,
  ...props
}) => {
  // Base styles
  const baseStyles = `
    inline-flex items-center justify-center
    font-medium rounded-slds
    transition-all duration-150
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  // Variant styles
  const variantStyles = {
    brand: `
      bg-slds-brand text-white
      hover:bg-slds-brand-dark
      focus:ring-slds-brand
    `,
    neutral: `
      bg-white text-slds-text-default
      border border-slds
      hover:bg-gray-50
      focus:ring-gray-300
    `,
    destructive: `
      bg-slds-error text-white
      hover:bg-slds-error-dark
      focus:ring-slds-error
    `,
    success: `
      bg-slds-success text-white
      hover:bg-slds-success-dark
      focus:ring-slds-success
    `,
    'outline-brand': `
      bg-transparent text-slds-brand
      border-2 border-slds-brand
      hover:bg-slds-brand hover:text-white
      focus:ring-slds-brand
    `,
  };

  // Size styles
  const sizeStyles = {
    small: 'px-3 py-1.5 text-sm gap-1.5',
    medium: 'px-4 py-2 text-base gap-2',
    large: 'px-6 py-3 text-lg gap-2.5',
  };

  const widthStyle = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${widthStyle}
        ${className}
      `.replace(/\s+/g, ' ').trim()}
      disabled={disabled}
      {...props}
    >
      {iconLeft && <span className="flex-shrink-0">{iconLeft}</span>}
      <span>{children}</span>
      {iconRight && <span className="flex-shrink-0">{iconRight}</span>}
    </button>
  );
};

export default Button;
