export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          400: '#F0C040',
          500: '#D4A017',
          600: '#B8860B',
        },
        surface: {
          900: '#0A0A0A',
          800: '#141414',
          700: '#1E1E1E',
          600: '#2A2A2A',
        }
      }
    },
  },
  plugins: [],
}