/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './public/index.html',
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        soft: '0 4px 14px rgba(0,0,0,0.08)',
      },
      spacing: {
        18: '4.5rem',
      },
      colors: {
        card: {
          DEFAULT: 'hsl(0 0% 100%)',
          foreground: 'hsl(240 10% 3.9%)',
        },
        cardDark: {
          DEFAULT: 'hsl(240 3.7% 15.9%)',
          foreground: 'hsl(0 0% 98%)',
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

