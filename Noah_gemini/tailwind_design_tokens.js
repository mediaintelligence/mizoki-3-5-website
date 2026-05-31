/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        mz: {
          bg: '#020204',
          surface: '#0a0a0c',
          border: '#1f1f22',
          accent: '#e4e4e7',
          muted: '#71717a',
          legal: '#3b82f6',
          estate: '#10b981',
          media: '#a855f7',
          risk: '#f43f5e',
        },
      },
    },
  },
  plugins: [],
}