/**
 * SLDS Card Component
 * Salesforce Lightning Design System 표준 Card
 */

import React, { ReactNode } from 'react';

export interface CardProps {
  /** Card 제목 */
  title?: string;

  /** 제목 옆 아이콘 */
  icon?: ReactNode;

  /** Header 우측 Action 버튼/요소 */
  headerAction?: ReactNode;

  /** Card Body 내용 */
  children: ReactNode;

  /** Footer 영역 (선택) */
  footer?: ReactNode;

  /** 추가 CSS 클래스 */
  className?: string;

  /** Variant 스타일 */
  variant?: 'default' | 'bordered' | 'elevated';
}

export const Card: React.FC<CardProps> = ({
  title,
  icon,
  headerAction,
  children,
  footer,
  className = '',
  variant = 'default',
}) => {
  const baseStyles = 'bg-white rounded-slds overflow-hidden';

  const variantStyles = {
    default: 'border border-slds',
    bordered: 'border-2 border-slds',
    elevated: 'shadow-slds-card',
  };

  return (
    <article className={`${baseStyles} ${variantStyles[variant]} ${className}`}>
      {/* Card Header */}
      {(title || headerAction) && (
        <header className="flex items-center justify-between p-slds-medium border-b border-slds bg-gray-50">
          <div className="flex items-center gap-slds-small">
            {icon && (
              <div className="text-slds-brand flex-shrink-0">
                {icon}
              </div>
            )}
            {title && (
              <h2 className="slds-text-heading_small font-bold text-slds-text-default">
                {title}
              </h2>
            )}
          </div>

          {headerAction && (
            <div className="flex-shrink-0">
              {headerAction}
            </div>
          )}
        </header>
      )}

      {/* Card Body */}
      <div className="p-slds-medium">
        {children}
      </div>

      {/* Card Footer */}
      {footer && (
        <footer className="px-slds-medium py-slds-small border-t border-slds bg-gray-50">
          {footer}
        </footer>
      )}
    </article>
  );
};

export default Card;
