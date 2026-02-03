import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
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
