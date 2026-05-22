/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        counsel: '#a855f7',
        estate:  '#21d07a',
        capital: '#34a6ff',
        signal:  '#f5a623',
        risk:    '#f4495f',
        nexus:   '#4cc9ff',
        accent:  '#7c5cff',
        ink: {
          DEFAULT: '#f3f5fc',
          2: '#9aa6c8',
          3: '#6c7799',
          4: '#46506e',
        },
        bg: {
          0: '#04060f',
          1: '#070b1c',
          2: '#0b1228',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Sora', 'system-ui', 'sans-serif'],
        serif:   ['"Instrument Serif"', 'Georgia', 'serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      animation: {
        scan: 'scan 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        scan: {
          '0%':   { transform: 'translateY(0)',    opacity: '0' },
          '10%':  { opacity: '1' },
          '90%':  { opacity: '1' },
          '100%': { transform: 'translateY(400px)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};
