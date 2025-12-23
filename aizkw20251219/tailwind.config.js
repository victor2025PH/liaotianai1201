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
        sans: ['Inter', 'Noto Sans SC', 'sans-serif'],
        mono: ['JetBrains Mono', 'Noto Sans SC', 'monospace'],
      },
      colors: {
        // Override cyan to match the new brand Neon Blue (#00FFFF)
        cyan: {
          50: '#f0fdfd',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#00FFFF', // Brand Primary
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
          950: '#083344',
        },
        neon: {
          blue: '#00FFFF',
          purple: '#bc13fe',
          green: '#0aff0a',
        }
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2.5s infinite linear',
        'flow-slow': 'flow 20s linear infinite',
        'flow-medium': 'flow 15s linear infinite reverse',
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'slide-in-right': 'slideInRight 0.5s ease-out forwards',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 255, 255, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 255, 255, 0.6), 0 0 10px rgba(0, 255, 255, 0.4)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        },
        flow: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' }
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        }
      }
    }
  },
  plugins: [],
}
