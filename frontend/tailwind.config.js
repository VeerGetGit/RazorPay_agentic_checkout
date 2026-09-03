/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#e8f4ff',
          100: '#d1e9ff',
          500: '#2D5BE3',
          600: '#1E47D4',
          700: '#1535A8',
          900: '#0A1628',
        },
        accent: {
          400: '#00D09C',
          500: '#00B589',
        },
        surface: {
          800: '#0F1729',
          900: '#080E1A',
        }
      }
    },
  },
  plugins: [],
}