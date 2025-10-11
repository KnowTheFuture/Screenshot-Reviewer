/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f6ff",
          100: "#dcebff",
          200: "#bad7fe",
          300: "#8cbafd",
          400: "#5a96fb",
          500: "#3a78f5",
          600: "#245de8",
          700: "#1b47c4",
          800: "#1d3d9d",
          900: "#1c357d"
        }
      }
    }
  },
  plugins: []
};