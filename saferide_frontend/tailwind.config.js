/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // <- this is important
  content: [
    "./src/**/*.{js,ts,jsx,tsx}", // adjust paths as per your project
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
