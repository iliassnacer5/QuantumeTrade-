import type { Config } from 'tailwindcss';

/**
 * Design system Quantum Trade AI.
 * Dark mode par défaut · accent rouge #E24B4A (SELL) · vert #1D9E75 (BUY).
 */
const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0B0E11',
        surface: '#151A21',
        border: '#232A33',
        muted: '#8A94A6',
        sell: { DEFAULT: '#E24B4A', soft: '#E24B4A22' },
        buy: { DEFAULT: '#1D9E75', soft: '#1D9E7522' },
        accent: '#1D9E75',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
