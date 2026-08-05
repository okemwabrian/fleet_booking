/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    './**/*.py',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}