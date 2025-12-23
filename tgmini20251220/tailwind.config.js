/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        neon: {
          blue: '#00f3ff',
          purple: '#bc13fe',
          pink: '#ff00ff',
          green: '#0aff00',
        },
        dark: {
          bg: '#050505',
          card: '#0a0a0a',
          border: '#1f1f1f'
        }
      },
      backgroundImage: {
        'cyber-grid': "linear-gradient(to right, #1f1f1f 1px, transparent 1px), linear-gradient(to bottom, #1f1f1f 1px, transparent 1px)",
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      }
    }
  },
  plugins: [],
}
