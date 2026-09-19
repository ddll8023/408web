/**
 * Tailwind 配置
 *
 * 语义色令牌定义在 `src/styles/tailwind.css` 的 :root（--brand-*），这里只做映射，
 * 保证组件类名（text-accent、bg-surface、text-ink…）与 scoped CSS 的 var() 同源；
 * 改色只需改 tailwind.css 一处。其余颜色一律使用 Tailwind 内置调色板。
 *
 * 注意：不要向 theme.extend.spacing 添加 xs/sm/md/lg/xl 等同名键。Tailwind v4 会把
 * theme.spacing 合并进 max-w-* 取值表末尾，同名键会把 max-w-sm/md/lg/xl 覆盖为
 * 16/24/32/40px（登录/注册卡片曾因此被压成 24px 竖条）；间距请直接用数字刻度（p-4 = 16px）。
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: 'var(--brand-accent)',
        'accent-hover': 'var(--brand-accent-hover)',
        'accent-deep': 'var(--brand-accent-deep)',
        surface: 'var(--brand-surface)',
        line: 'var(--brand-line)',
        ink: 'var(--brand-ink)',
        'ink-soft': 'var(--brand-ink-soft)',
        'ink-mute': 'var(--brand-ink-mute)',
        // 内容主题色（真题 / 模拟题），值定义在 tailwind.css 的 :root
        exam: {
          accent: 'var(--theme-exam-accent)',
          strong: 'var(--theme-exam-strong)',
          'icon-fg': 'var(--theme-exam-icon-fg)',
          'icon-bg': 'var(--theme-exam-icon-bg)',
          surface: 'var(--theme-exam-surface)',
          'surface-soft': 'var(--theme-exam-surface-soft)',
          'surface-badge': 'var(--theme-exam-surface-badge)',
          border: 'var(--theme-exam-border)',
          subtitle: 'var(--theme-exam-subtitle)',
          'soft-fg': 'var(--theme-exam-soft-fg)',
        },
        mock: {
          accent: 'var(--theme-mock-accent)',
          strong: 'var(--theme-mock-strong)',
          'icon-bg': 'var(--theme-mock-icon-bg)',
          surface: 'var(--theme-mock-surface)',
          'surface-soft': 'var(--theme-mock-surface-soft)',
          'surface-badge': 'var(--theme-mock-surface-badge)',
          border: 'var(--theme-mock-border)',
          subtitle: 'var(--theme-mock-subtitle)',
          'soft-fg': 'var(--theme-mock-soft-fg)',
        },
      },
    },
  },
  plugins: [],
}
