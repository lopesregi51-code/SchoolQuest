/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2B6CB0",
        secondary: "#E53E3E",
        success: "#48BB78",
        dark: "#0F172A",
        light: "#F8FAFC"
      }
    },
  },
  plugins: [],
}
