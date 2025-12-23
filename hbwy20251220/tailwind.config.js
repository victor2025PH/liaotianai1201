/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      colors: {
        game: {
          primary: '#FF6B00', // Orange from Send Packet
          secondary: '#8B5CF6', // Purple from Invite
          dark: '#0a0a0a', // Main BG
          card: '#1c1c1c', // Card BG
          surface: '#252525', // Lighter surface
          text: '#9CA3AF', // Muted text
        }
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #FF8F00 0%, #FF3D00 100%)',
        'gradient-purple': 'linear-gradient(135deg, #A855F7 0%, #6366F1 100%)',
        'gradient-dark': 'linear-gradient(180deg, #1c1c1c 0%, #111111 100%)',
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    }
  },
  plugins: [],
}
