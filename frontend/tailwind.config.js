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
        primary: {
          DEFAULT: '#3b82f6', // Neon blue
          dark: '#1e40af',
          light: '#60a5fa',
        },
        danger: {
          DEFAULT: '#ef4444',
          dark: '#dc2626',
        },
        warning: {
          DEFAULT: '#f59e0b',
          dark: '#d97706',
        },
        success: {
          DEFAULT: '#10b981',
          dark: '#059669',
        },
        gray: {
          900: '#0f0f0f',
          850: '#151515',
          800: '#1a1a1a',
          750: '#1f1f1f',
          700: '#2a2a2a',
          600: '#404040',
          500: '#6b7280',
          400: '#9ca3af',
          300: '#d1d5db',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.3)',
        'glow-blue-lg': '0 0 40px rgba(59, 130, 246, 0.4)',
      },
    },
  },
  plugins: [],
}
