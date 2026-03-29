import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // PAI theme colors
        pai: {
          primary: '#3b82f6',    // Bright blue
          secondary: '#8b5cf6',  // Purple
          accent: '#ec4899',     // Pink
          dark: '#0f172a',       // Dark slate
          light: '#f8fafc',      // Light slate
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)'],
      },
    },
  },
  plugins: [],
} satisfies Config

export default config
