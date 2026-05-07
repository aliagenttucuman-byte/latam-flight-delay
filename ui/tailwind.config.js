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
        latam: {
          red: '#CC0000',
          dark: '#1A1A1A',
          white: '#FFFFFF',
          gray: '#F5F5F5',
        }
      }
    },
  },
  plugins: [],
}