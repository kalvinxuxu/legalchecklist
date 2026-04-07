/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        // Deep Navy - authority, trust, professionalism
        navy: {
          50: '#F0F4F8',
          100: '#D9E2EC',
          200: '#BCCCDC',
          300: '#9FB3C8',
          400: '#829AB1',
          500: '#627D98',
          600: '#486581',
          700: '#334E68',
          800: '#1A365D',
          900: '#0F2744',
        },
        // Warm Amber - accent, energy, premium
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#D97706',
          600: '#B45309',
          700: '#92400E',
        },
        // Ivory - warm backgrounds
        ivory: {
          50: '#FDFCFA',
          100: '#FAF8F5',
          200: '#F5F1EC',
          300: '#EDE8E0',
        },
        // Sky blue for info
        sky: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#0EA5E9',
          600: '#0284C7',
        },
        // Semantic colors
        success: {
          50: '#E8F5E9',
          500: '#2E7D32',
          600: '#1B5E20',
        },
        warning: {
          50: '#FFF3E0',
          500: '#E65100',
          600: '#BF360C',
        },
        danger: {
          50: '#FFEBEE',
          500: '#C62828',
          600: '#B71C1C',
        },
        // Primary = Deep Navy
        primary: {
          50: '#F0F4F8',
          100: '#D9E2EC',
          200: '#BCCCDC',
          300: '#9FB3C8',
          400: '#829AB1',
          500: '#627D98',
          600: '#486581',
          700: '#334E68',
          800: '#1A365D',
          900: '#0F2744',
        },
        border: '#E8E4DF',
        input: '#E8E4DF',
        ring: '#1A365D',
        background: '#FAF8F5',
        foreground: '#1A1A2E',
        card: '#FFFFFF',
        'card-foreground': '#1A1A2E',
        muted: '#F5F1EC',
        'muted-foreground': '#8B8178',
        accent: '#F5F1EC',
        'accent-foreground': '#1A1A2E',
        destructive: '#C62828',
        'destructive-foreground': '#FFFFFF',
        popover: '#FFFFFF',
        'popover-foreground': '#1A1A2E',
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'Noto Serif SC', 'serif'],
        sans: ['PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Arial', 'sans-serif'],
        display: ['Georgia', 'serif'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '10px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(26, 26, 46, 0.06), 0 1px 2px rgba(26, 26, 46, 0.04)',
        DEFAULT: '0 4px 12px rgba(26, 26, 46, 0.08), 0 2px 4px rgba(26, 26, 46, 0.04)',
        md: '0 8px 24px rgba(26, 26, 46, 0.10), 0 4px 8px rgba(26, 26, 46, 0.06)',
        lg: '0 16px 48px rgba(26, 26, 46, 0.12), 0 8px 16px rgba(26, 26, 46, 0.08)',
        glow: '0 0 40px rgba(26, 54, 93, 0.15)',
      },
      animation: {
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'float': 'float 6s ease-in-out infinite',
        'pulse-soft': 'pulseSoft 3s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',
        'slide-in-right': 'slideInRight 0.5s ease-out forwards',
        'stagger': 'stagger 0.6s ease-out forwards',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        stagger: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
