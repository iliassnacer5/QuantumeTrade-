import type { Config } from 'tailwindcss';

/**
 * Design system Quantum Trade AI.
 * Dark mode par défaut · accent vert #1D9E75 (BUY) · rouge #E24B4A (SELL).
 * Phase F1 : tokens étendus (typo, ombres, gradients de marque, keyframes d'animation).
 */
const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0B0E11',
        surface: '#151A21',
        // Élévation intermédiaire (cartes survolées, popovers, topbar).
        elevated: '#1B222B',
        border: '#232A33',
        muted: '#8A94A6',
        sell: { DEFAULT: '#E24B4A', soft: '#E24B4A22' },
        buy: { DEFAULT: '#1D9E75', soft: '#1D9E7522' },
        accent: '#1D9E75',
        // Second pôle du gradient de marque (vert → cyan).
        cyan: '#22C7C7',
        warn: { DEFAULT: '#E0A63C', soft: '#E0A63C22' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        // Échelle typographique resserrée, tracking soigné.
        '2xs': ['0.6875rem', { lineHeight: '0.875rem' }],
        display: ['2.75rem', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '700' }],
        h1: ['1.75rem', { lineHeight: '1.15', letterSpacing: '-0.015em', fontWeight: '700' }],
        h2: ['1.25rem', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' }],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.125rem',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.25), 0 1px 3px rgba(0,0,0,0.15)',
        elevated: '0 8px 24px -8px rgba(0,0,0,0.55), 0 2px 6px rgba(0,0,0,0.3)',
        glow: '0 0 0 1px rgba(29,158,117,0.35), 0 8px 30px -8px rgba(29,158,117,0.35)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(120deg, #1D9E75 0%, #22C7C7 100%)',
        'brand-radial': 'radial-gradient(80% 120% at 20% 0%, rgba(29,158,117,0.16) 0%, rgba(11,14,17,0) 60%)',
        'glass': 'linear-gradient(160deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'pulse-dot': {
          '0%,100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.6s infinite',
        'fade-in-up': 'fade-in-up 0.35s ease-out both',
        'fade-in': 'fade-in 0.3s ease-out both',
        'pulse-dot': 'pulse-dot 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
