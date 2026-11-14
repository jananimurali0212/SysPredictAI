/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070b14',
          900: '#0b0f19', // main dark navy background
          850: '#0f172a',
          800: '#111827', // dashboard cards
          750: '#162032',
          700: '#1f2937', // lighter borders/hover
          600: '#374151',
        },
        status: {
          normal: '#10b981',   // Green
          warning: '#f59e0b',  // Yellow / Orange
          critical: '#ef4444', // Red
          info: '#3b82f6',     // Blue
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
