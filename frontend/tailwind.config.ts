import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  safelist: [
    // SLDS color classes
    'bg-slds-brand', 'bg-slds-brand-dark', 'bg-slds-brand-darker', 'bg-slds-success', 'bg-slds-warning', 'bg-slds-error', 'bg-slds-info',
    'bg-slds-background', 'bg-slds-background-alt', 'bg-slds-background-shade',
    'text-slds-brand', 'text-slds-brand-dark', 'text-slds-text-heading', 'text-slds-text-body', 'text-slds-text-weak', 'text-slds-text-disabled',
    'text-slds-success', 'text-slds-warning', 'text-slds-error', 'text-slds-info',
    'border-slds', 'border-slds-border-strong', 'border-slds-brand',
    // SLDS hover states
    'hover:bg-slds-brand-dark', 'hover:bg-slds-background-shade', 'hover:text-slds-brand',
    // SLDS spacing
    'p-slds-small', 'p-slds-medium', 'p-slds-large', 'p-slds-x-large',
    'px-slds-small', 'px-slds-medium', 'px-slds-large',
    'py-slds-small', 'py-slds-medium', 'py-slds-large',
    'm-slds-small', 'm-slds-medium', 'm-slds-large',
    'mb-slds-small', 'mb-slds-medium', 'mb-slds-large',
    'mt-slds-small', 'mt-slds-medium', 'mt-slds-large',
    'gap-slds-small', 'gap-slds-medium', 'gap-slds-large',
    // SLDS border radius
    'rounded-slds', 'rounded-slds-sm', 'rounded-slds-md',
    // SLDS shadows
    'shadow-slds-card', 'shadow-slds-modal', 'shadow-slds-dropdown',
  ],
  theme: {
    extend: {
      colors: {
        // Salesforce Lightning Design System
        'slds-brand': '#00A1E0',
        'slds-brand-dark': '#0070D2',
        'slds-brand-darker': '#005FB2',
        'slds-success': '#4BCA81',
        'slds-warning': '#FFB75D',
        'slds-error': '#EA001E',
        'slds-info': '#5867E8',

        'slds-background': '#F3F2F2',
        'slds-background-alt': '#FFFFFF',
        'slds-background-shade': '#E5E5E5',

        'slds-text-heading': '#16325C',
        'slds-text-body': '#3E3E3C',
        'slds-text-weak': '#706E6B',
        'slds-text-disabled': '#C9C7C5',

        'slds-border': '#DDDBDA',
        'slds-border-strong': '#C9C7C5',

        // Legacy brand colors (keep for compatibility)
        brand: {
          primary: {
            50: '#f5f3ff',
            100: '#ede9fe',
            400: '#c084fc',
            500: '#a855f7',
            600: '#9333ea',
            700: '#7e22ce',
            900: '#581c87',
          },
          secondary: {
            400: '#f472b6',
            500: '#ec4899',
            600: '#db2777',
          },
        },
        surface: {
          darkest: '#0a0a0a',
          dark: '#1a1a1a',
          medium: '#2a2a2a',
          light: '#3a3a3a',
        },
      },
      spacing: {
        'slds-xxx-small': '0.125rem',   // 2px
        'slds-xx-small': '0.25rem',     // 4px
        'slds-x-small': '0.5rem',       // 8px
        'slds-small': '0.75rem',        // 12px
        'slds-medium': '1rem',          // 16px
        'slds-large': '1.5rem',         // 24px
        'slds-x-large': '2rem',         // 32px
        'slds-xx-large': '3rem',        // 48px
      },
      borderRadius: {
        'slds': '0.25rem',        // 4px - DEFAULT
        'slds-sm': '0.125rem',    // 2px
        'slds-md': '0.5rem',      // 8px
      },
      boxShadow: {
        'slds-card': '0 2px 2px 0 rgba(0, 0, 0, 0.1)',
        'slds-modal': '0 0 3px 0 rgba(0, 0, 0, 0.16)',
        'slds-dropdown': '0 2px 3px 0 rgba(0, 0, 0, 0.16)',
      },
      fontSize: {
        'slds-heading-large': ['1.75rem', { lineHeight: '1.25', fontWeight: '700' }],
        'slds-heading-medium': ['1.25rem', { lineHeight: '1.25', fontWeight: '700' }],
        'slds-heading-small': ['1rem', { lineHeight: '1.25', fontWeight: '700' }],
        'slds-body-regular': ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
        'slds-body-small': ['0.75rem', { lineHeight: '1.5', fontWeight: '400' }],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
export default config
