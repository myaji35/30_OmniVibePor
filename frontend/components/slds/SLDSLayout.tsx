/**
 * SLDS Layout - 3-Column Structure
 * Salesforce Lightning Design System 표준 레이아웃
 */

import React, { ReactNode } from 'react';

interface SLDSLayoutProps {
  children: ReactNode;
}

interface LeftNavProps {
  children: ReactNode;
  collapsed?: boolean;
}

interface MainWorkspaceProps {
  children: ReactNode;
}

interface RightSidebarProps {
  children: ReactNode;
  visible?: boolean;
}

/**
 * 전체 SLDS 레이아웃 컨테이너
 */
export const SLDSLayout: React.FC<SLDSLayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-slds-background">
      {children}
    </div>
  );
};

/**
 * 좌측 네비게이션 영역
 */
export const LeftNav: React.FC<LeftNavProps> = ({ children, collapsed = false }) => {
  return (
    <aside
      className={`
        bg-white border-r border-slds
        transition-all duration-300
        flex-shrink-0
        overflow-y-auto
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      <nav className="p-slds-medium">
        {children}
      </nav>
    </aside>
  );
};

/**
 * 중앙 메인 워크스페이스
 */
export const MainWorkspace: React.FC<MainWorkspaceProps> = ({ children }) => {
  return (
    <main className="flex-1 overflow-y-auto bg-slds-background p-slds-large">
      <div className="max-w-7xl mx-auto">
        {children}
      </div>
    </main>
  );
};

/**
 * 우측 사이드바 (Activity, Context)
 */
export const RightSidebar: React.FC<RightSidebarProps> = ({ children, visible = true }) => {
  if (!visible) return null;

  return (
    <aside
      className="
        w-80 bg-white border-l border-slds
        flex-shrink-0 overflow-y-auto
      "
    >
      <div className="p-slds-medium">
        {children}
      </div>
    </aside>
  );
};

/**
 * 페이지 헤더 (제목 + 액션)
 */
interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  actions?: ReactNode;
  icon?: ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  actions,
  icon,
}) => {
  return (
    <header className="mb-slds-large">
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="mb-slds-small">
          <ol className="flex items-center gap-2 text-sm text-slds-text-weak">
            {breadcrumbs.map((crumb, idx) => (
              <li key={idx} className="flex items-center gap-2">
                {idx > 0 && <span>/</span>}
                {crumb.href ? (
                  <a href={crumb.href} className="hover:text-slds-brand">
                    {crumb.label}
                  </a>
                ) : (
                  <span>{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Title + Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-slds-medium">
          {icon && (
            <div className="text-slds-brand flex-shrink-0">
              {icon}
            </div>
          )}
          <div>
            <h1 className="slds-text-heading_large">{title}</h1>
            {subtitle && (
              <p className="slds-text-body_small mt-1">{subtitle}</p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-slds-small">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
};

/**
 * 네비게이션 아이템
 */
interface NavItemProps {
  children: ReactNode;
  icon?: ReactNode;
  active?: boolean;
  href?: string;
  onClick?: () => void;
  badge?: string | number;
}

export const NavItem: React.FC<NavItemProps> = ({
  children,
  icon,
  active = false,
  href,
  onClick,
  badge,
}) => {
  const baseStyles = `
    flex items-center justify-between
    w-full px-slds-medium py-slds-small
    rounded-slds text-left text-base
    transition-colors duration-150
  `;

  const activeStyles = active
    ? 'bg-slds-brand text-white hover:bg-slds-brand-dark'
    : 'text-slds-text-heading hover:bg-slds-background-shade font-semibold';

  const content = (
    <>
      <div className="flex items-center gap-slds-small flex-1">
        {icon && <span className="flex-shrink-0">{icon}</span>}
        <span className="font-medium">{children}</span>
      </div>
      {badge && (
        <span className={`
          px-2 py-0.5 rounded-full text-xs font-medium
          ${active ? 'bg-white text-slds-brand' : 'bg-gray-200 text-gray-700'}
        `}>
          {badge}
        </span>
      )}
    </>
  );

  if (href) {
    return (
      <a href={href} className={`${baseStyles} ${activeStyles}`}>
        {content}
      </a>
    );
  }

  return (
    <button onClick={onClick} className={`${baseStyles} ${activeStyles}`}>
      {content}
    </button>
  );
};

export default SLDSLayout;
