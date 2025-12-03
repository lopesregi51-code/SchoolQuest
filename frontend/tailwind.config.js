/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        secondary: "rgb(var(--color-secondary) / <alpha-value>)",
        success: "#48BB78",
        dark: "#0F172A",
        light: "#F8FAFC"
      }
    },
  },
  plugins: [
    require('@tailwindcss/line-clamp'),
  ],
}
