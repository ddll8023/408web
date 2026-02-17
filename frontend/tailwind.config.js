import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 颜色系统
      colors: {
        primary: '#FBF7F2',
        accent: '#8B6F47',
        'accent-light': 'rgba(139, 111, 71, 0.1)',
        text: {
          primary: '#333',
          regular: '#666',
          secondary: '#999',
          white: '#fff',
        },
        bg: {
          white: '#fff',
          light: '#efefef',
        },
        border: {
          base: '#dcdfe6',
          light: '#dfe2e5',
        },
        success: '#67c23a',
        warning: '#e6a23c',
        danger: '#f56c6c',
        disabled: '#7f8c8d',
        'disabled-bg': '#f5f7fa',
      },
      // 字体大小
      fontSize: {
        small: '12px',
        base: '14px',
        medium: '16px',
        large: '18px',
        xl: '20px',
        xxl: '28px',
      },
      // 字重
      fontWeight: {
        medium: '500',
        bold: '600',
      },
      // 字体族
      fontFamily: {
        base: "'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif",
      },
      // 间距系统
      spacing: {
        xs: '8px',
        sm: '16px',
        md: '24px',
        lg: '32px',
        xl: '40px',
        gap: '12px',
      },
      // 容器宽度
      maxWidth: {
        'sm': '450px',
        'md': '900px',
        'lg': '1200px',
        'xl': '1400px',
      },
      // 边框圆角
      borderRadius: {
        base: '4px',
        small: '2px',
      },
      // 阴影
      boxShadow: {
        light: '0 2px 4px rgba(0, 0, 0, 0.08)',
        base: '0 2px 8px rgba(0, 0, 0, 0.1)',
      },
      // 高度
      height: {
        nav: '60px',
      },
      // Z轴层级
      zIndex: {
        nav: '1000',
      },
      // 过渡动画
      transition: {
        base: 'all 0.3s ease',
        fast: 'all 0.15s ease',
      },
      // 滚动条宽度
      scrollbar: {
        width: '8px',
      },
    },
  },
  plugins: [],
} satisfies Config
