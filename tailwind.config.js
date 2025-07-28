// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        'space-blue': '#0a1a2f',
        'space-light': '#1a365d',
        'accent-blue': '#2b6cb0',
        'accent-light': '#4299e1',
      },
    },
  },
  plugins: [],
}