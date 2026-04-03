/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        parchment: {
          50:  '#f5e6c8',
          100: '#ede0c4',
          200: '#e3d5b0',
          300: '#d4c49a',
          400: '#c4b080',
          500: '#b09060',
        },
        leather: {
          300: '#a07828',
          400: '#8b6914',
          500: '#7a5c10',
          600: '#6b4c11',
          700: '#5a3c0e',
          800: '#3d2808',
        },
        ink: {
          400: '#8a6040',
          600: '#5c3d1e',
          800: '#2c1a0e',
          900: '#1a0a00',
        },
        crimson: {
          400: '#c0392b',
          500: '#a93226',
          600: '#8b0000',
          700: '#6e0000',
          800: '#550000',
          900: '#3d0000',
        },
        gold: {
          300: '#f0d060',
          400: '#d4aa30',
          500: '#c9a227',
          600: '#a07818',
          700: '#8a6914',
        },
        azure: {
          300: '#7ab8e0',
          400: '#4a90c4',
          600: '#2a6090',
          800: '#1a3a5c',
        },
        arcane: {
          200: '#d4b8f0',
          400: '#9060c8',
          600: '#6b3fa8',
          700: '#5b2d8e',
          800: '#3d1a6e',
        },
        hp: {
          critical: '#7a1a0a',
          low:      '#8a4010',
          medium:   '#7a6200',
          good:     '#2a5a20',
        },
        hpbar: {
          critical: '#c0392b',
          low:      '#c87020',
          medium:   '#c0a000',
          good:     '#4a8a38',
        },
      },
      fontFamily: {
        display: ['"Cinzel"', 'Georgia', 'serif'],
        body:    ['"Crimson Text"', 'Georgia', 'serif'],
        sans:    ['"Crimson Text"', 'Georgia', 'serif'],
        mono:    ['"Courier Prime"', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
};
