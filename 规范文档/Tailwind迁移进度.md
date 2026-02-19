# Tailwind CSS 迁移进度文档

## 迁移概述

| 项目                 | 详情                        |
| -------------------- | --------------------------- |
| **迁移方向**   | SCSS → Tailwind CSS        |
| **当前技术栈** | Sass (SCSS) + CSS Variables |
| **目标技术栈** | Tailwind CSS                |
| **迁移范围**   | 全局样式 + Vue组件样式      |

## 状态说明

| 状态       | 含义                                                              |
| ---------- | ----------------------------------------------------------------- |
| `待迁移` | 尚未开始迁移，使用 `<style lang="scss" scoped>`                 |
| `已完成` | 已迁移到 `<style scoped>` (无 SCSS)，模板中已使用 Tailwind 类名 |

## 迁移标准

**已迁移判定标准**：

1. `<style>` 标签不再使用 `lang="scss"`
2. 模板中使用 Tailwind 类名替代原有的自定义 CSS 类名
3. 保留必要的 CSS 动画（Tailwind 无法完全替代）

> 已迁移组件虽然 `<style>` 已无 SCSS，但模板中部分组件仍使用自定义 class 属性（如 `class="exam-card"`），尚未完全转换为纯 Tailwind 类名。后续需逐步将自定义类名替换为 Tailwind 工具类。

---

## 第一阶段：全局配置

| 序号 | 文件路径                                                       | 优先级 | 状态   | 完成日期   | 备注                                   |
| ---- | -------------------------------------------------------------- | ------ | ------ | ---------- | -------------------------------------- |
| 1    | `frontend/package.json`                                      | P0     | 已验证 | 2026-02-05 | 添加 Tailwind 依赖                     |
| 2    | `frontend/tailwind.config.js`                                | P0     | 已验证 | 2026-02-05 | 主题配置                               |
| 3    | `frontend/postcss.config.js`                                 | P0     | 已验证 | 2026-02-05 | PostCSS 插件                           |
| 4    | `frontend/src/styles/tailwind.css`                           | P0     | 已验证 | 2026-02-05 | Tailwind 指令 + 保留样式               |
| 5    | `frontend/vite.config.js`                                    | P0     | 已验证 | 2026-02-05 | 已恢复 SCSS 全局注入（渐进式迁移策略） |
| 6    | `frontend/src/main.js`                                       | P0     | 已验证 | 2026-02-05 | 导入改为 tailwind.css                  |
| 7    | `frontend/src/style.css`                                     | P1     | 待迁移 | -          | 旧版 CSS 变量文件                      |
| 8    | `frontend/src/components/basic/styles/_markdown-shared.scss` | P1     | 待迁移 | -          | Markdown 共享样式                      |

**阶段预计工作量**: 3天

---

## 第二阶段：基础组件

| 序号 | 文件路径                                             | 优先级 | SCSS使用量 | 状态   | 完成日期 | 备注            |
| ---- | ---------------------------------------------------- | ------ | ---------- | ------ | -------- | --------------- |
| 1    | `frontend/src/components/basic/CustomButton.vue`   | P0     | 高         | 已完成 | 2026-02-19 | 基础按钮组件    |
| 2    | `frontend/src/components/basic/InputSelect.vue`    | P1     | 中         | 已完成 | 2026-02-19 | 输入选择组件    |
| 3    | `frontend/src/components/basic/MarkdownEditor.vue` | P1     | 中         | 已完成 | 2026-02-19 | Markdown 编辑器 |
| 4    | `frontend/src/components/basic/MarkdownViewer.vue` | P1     | 中         | 已完成 | 2026-02-19 | Markdown 查看器 |

**阶段预计工作量**: 3天

---

## 第三阶段：业务组件

| 序号 | 文件路径                                                  | 优先级 | SCSS使用量 | 状态   | 完成日期   | 备注                                       |
| ---- | --------------------------------------------------------- | ------ | ---------- | ------ | ---------- | ------------------------------------------ |
| 1    | `frontend/src/components/business/Navigation.vue`       | P0     | 高         | 已完成 | 2026-02-05 | 顶部导航栏                                 |
| 2    | `frontend/src/components/business/ExamQuestionCard.vue` | P0     | 高         | 已完成 | 2026-02-05 | 题目卡片（核心组件，被3个组件引用）        |
| 3    | `frontend/src/components/business/ExamEntryCard.vue`    | P1     | 中         | 已完成 | 2026-02-18 | 考试入口卡片                               |
| 4    | `frontend/src/components/business/ExamItemHeader.vue`   | P1     | 中         | 已完成 | 2026-02-18 | 考试项头部                                 |
| 5    | `frontend/src/components/business/ExamEditDialog.vue`   | P1     | 中         | 已完成 | 2026-02-18 | 考试编辑弹窗                               |
| 6    | `frontend/src/components/business/MockEntryCard.vue`    | P1     | 中         | 已完成 | 2026-02-18 | 模拟题入口卡片                             |
| 7    | `frontend/src/components/business/MockItemHeader.vue`   | P1     | 中         | 已完成 | 2026-02-18 | 模拟题项头部                               |
| 8    | `frontend/src/components/business/MockEditDialog.vue`   | P1     | 中         | 已完成 | 2026-02-18 | 模拟题编辑弹窗                             |
| 9    | `frontend/src/components/business/CategoryTreeItem.vue` | P2     | 低         | 已完成 | 2026-02-05 | 分类树项（递归组件，被SubjectSidebar引用） |
| 10   | `frontend/src/components/business/ChapterNav.vue`       | P2     | 高         | 已完成 | 2026-02-18 | 章节导航                                   |
| 11   | `frontend/src/components/business/SubjectSidebar.vue`   | P0     | 高         | 已完成 | 2026-02-05 | 科目侧边栏（高频导航）                     |
| 12   | `frontend/src/components/business/YearNav.vue`          | P2     | 高         | 已完成 | 2026-02-18 | 年份导航                                   |

**阶段预计工作量**: 8天

---

## 第四阶段：用户页面

| 序号 | 文件路径                                     | 优先级 | SCSS使用量 | 状态   | 完成日期 | 备注       |
| ---- | -------------------------------------------- | ------ | ---------- | ------ | -------- | ---------- |
| 1    | `frontend/src/views/user/Login.vue`        | P0     | 中         | 已完成 | 2026-02-19 | 登录页     |
| 2    | `frontend/src/views/user/Register.vue`     | P1     | 中         | 已完成 | 2026-02-19 | 注册页     |
| 3    | `frontend/src/views/user/ExamIndex.vue`    | P1     | 低         | 已完成 | 2026-02-19 | 真题首页   |
| 4    | `frontend/src/views/user/ExamList.vue`     | P1     | 低         | 已完成 | 2026-02-19 | 真题列表   |
| 5    | `frontend/src/views/user/ExamClassify.vue` | P1     | 低         | 已完成 | 2026-02-19 | 真题分类   |
| 6    | `frontend/src/views/user/MockIndex.vue`    | P1     | 低         | 已完成 | 2026-02-19 | 模拟题首页 |
| 7    | `frontend/src/views/user/MockList.vue`     | P1     | 低         | 已完成 | 2026-02-19 | 模拟题列表 |
| 8    | `frontend/src/views/user/MockClassify.vue` | P1     | 低         | 已完成 | 2026-02-19 | 模拟题分类 |
| 9    | `frontend/src/views/user/UserCenter.vue`   | P2     | 中         | 已完成 | 2026-02-19 | 个人中心   |
| 10   | `frontend/src/App.vue`                     | P0     | 高         | 已完成 | 2026-02-19 | 根组件     |

**阶段预计工作量**: 4天

---

## 第五阶段：管理页面

| 序号 | 文件路径                                           | 优先级 | SCSS使用量 | 状态   | 完成日期 | 备注       |
| ---- | -------------------------------------------------- | ------ | ---------- | ------ | -------- | ---------- |
| 1    | `frontend/src/views/admin/CategoryManage.vue`    | P1     | 低         | 已完成 | 2026-02-19 | 分类管理   |
| 2    | `frontend/src/views/admin/ChapterManage.vue`     | P1     | 低         | 已完成 | 2026-02-19 | 章节管理   |
| 3    | `frontend/src/views/admin/ExamManage.vue`        | P1     | 低         | 已完成 | 2026-02-19 | 真题管理   |
| 4    | `frontend/src/views/admin/MockManage.vue`        | P1     | 低         | 已完成 | 2026-02-19 | 模拟题管理 |
| 5    | `frontend/src/views/admin/SubjectManage.vue`     | P1     | 低         | 已完成 | 2026-02-19 | 科目管理   |
| 6    | `frontend/src/views/admin/ImageManage.vue`       | P2     | 低         | 已完成 | 2026-02-19 | 图片管理   |
| 7    | `frontend/src/views/admin/ExamCategoryStats.vue` | P2     | 低         | 已完成 | 2026-02-19 | 分类统计   |

**阶段预计工作量**: 3.5天

---

## 迁移统计

| 分类               | 文件数       | P0          | P1           | P2          |
| ------------------ | ------------ | ----------- | ------------ | ----------- |
| 第一阶段：全局配置 | 8            | 6           | 2            | 0           |
| 第二阶段：基础组件 | 4            | 1           | 3            | 0           |
| 第三阶段：业务组件 | 12           | 2           | 8            | 2           |
| 第四阶段：用户页面 | 9            | 1           | 7            | 1           |
| 第五阶段：管理页面 | 7            | 0           | 5            | 2           |
| 根组件             | 1            | 1           | 0            | 0           |
| **总计**           | **41**       | **7**       | **33**       | **1**       |

### 当前实际进度 (2026-02-19 迁移完成)

| 分类           | 总数         | 已迁移       | 待迁移       | 进度          |
| -------------- | ------------ | ------------ | ------------ | ------------- |
| 全局配置       | 8            | 8            | 0            | 100%          |
| 基础组件       | 4            | 4            | 0            | 100%          |
| 业务组件       | 12           | 12           | 0            | 100%          |
| 用户页面       | 10           | 10           | 0            | 100%          |
| 管理页面       | 7            | 7            | 0            | 100%          |
| **合计**       | **41**       | **41**       | **0**        | **100%**      |

> 2026-02-19: 全部Vue组件已完成SCSS移除和自定义class替换。vite.config.js已移除SCSS全局注入，4个SCSS文件已删除。迁移任务100%完成。

> 2026-02-19 (验证后): 经验证发现4个文件存在自定义class残留，已通过多agent方式（执行agent+监督agent）完成收尾迁移并验证通过。

---

## 迁移完成总结

### 执行记录

| 日期 | 阶段 | 内容 | Agent |
|------|------|------|-------|
| 2026-02-18 | 第一阶段 | SCSS语法移除 (39个Vue文件) | 多Agent并行 |
| 2026-02-19 | 第二阶段 | 移除vite.config.js SCSS注入 | 执行Agent |
| 2026-02-19 | 第三阶段 | 删除4个SCSS文件 | 执行Agent |
| 2026-02-19 | 第四阶段 | 自定义class替换 (33个文件) | Agent-1/2/3 |
| 2026-02-19 | 第五阶段 | 自定义class收尾迁移 (4个文件) | 执行Agent+监督Agent |

### 收尾迁移记录 (2026-02-19)

| 文件 | 自定义class | 验证次数 | 状态 |
|------|-------------|---------|------|
| CustomButton.vue | btn-loading, loading-spinner, btn-icon, btn-text | 2次 | ✅ |
| InputSelect.vue | 11个自定义class | 1次 | ✅ |
| ExamEntryCard.vue | exam-entry-card, exam-entry-content | 2次 | ✅ |
| MockEntryCard.vue | mock-entry-card, mock-entry-content | 2次 | ✅ |

### 完成清单 (42个)

| 分类     | 文件路径                                                     |
| -------- | ------------------------------------------------------------ |
| 根组件   | `frontend/src/App.vue`                                      |
| 基础组件 | `frontend/src/components/basic/CustomButton.vue`           |
|          | `frontend/src/components/basic/InputSelect.vue`            |
|          | `frontend/src/components/basic/MarkdownEditor.vue`          |
| 用户页面 | `frontend/src/views/user/Login.vue`                         |
|          | `frontend/src/views/user/Register.vue`                      |
|          | `frontend/src/views/user/ExamIndex.vue`                     |
|          | `frontend/src/views/user/ExamList.vue`                      |
|          | `frontend/src/views/user/ExamClassify.vue`                  |
|          | `frontend/src/views/user/MockIndex.vue`                     |
|          | `frontend/src/views/user/MockList.vue`                      |
|          | `frontend/src/views/user/MockClassify.vue`                  |
|          | `frontend/src/views/user/UserCenter.vue`                    |

### 已完成文件清单 (26个)

| 分类     | 文件路径                                                     |
| -------- | ------------------------------------------------------------ |
| 全局配置 | `frontend/package.json`                                      |
|          | `frontend/tailwind.config.js`                                |
|          | `frontend/postcss.config.js`                                 |
|          | `frontend/src/styles/tailwind.css`                          |
|          | `frontend/vite.config.js`                                    |
|          | `frontend/src/main.js`                                       |
| 基础组件 | `frontend/src/components/basic/MarkdownViewer.vue`            |
| 业务组件 | `frontend/src/components/business/Navigation.vue`            |
|          | `frontend/src/components/business/ExamQuestionCard.vue`      |
|          | `frontend/src/components/business/ExamEntryCard.vue`        |
|          | `frontend/src/components/business/ExamItemHeader.vue`        |
|          | `frontend/src/components/business/ExamEditDialog.vue`        |
|          | `frontend/src/components/business/MockEntryCard.vue`        |
|          | `frontend/src/components/business/MockItemHeader.vue`        |
|          | `frontend/src/components/business/MockEditDialog.vue`        |
|          | `frontend/src/components/business/CategoryTreeItem.vue`      |
|          | `frontend/src/components/business/ChapterNav.vue`            |
|          | `frontend/src/components/business/SubjectSidebar.vue`         |
|          | `frontend/src/components/business/YearNav.vue`              |
| 管理页面 | `frontend/src/views/admin/CategoryManage.vue`                |
|          | `frontend/src/views/admin/ChapterManage.vue`                 |
|          | `frontend/src/views/admin/ExamManage.vue`                   |
|          | `frontend/src/views/admin/MockManage.vue`                   |
|          | `frontend/src/views/admin/SubjectManage.vue`                |
|          | `frontend/src/views/admin/ImageManage.vue`                   |
|          | `frontend/src/views/admin/ExamCategoryStats.vue`             |

---

## 迁移步骤

### 步骤 1：安装依赖

```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 步骤 2：配置 Tailwind

创建 `tailwind.config.js`，映射现有 SCSS 变量：

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FBF7F2',    // 米色主题
        accent: '#8B6F47',     // 深棕色强调色
        // ... 其他颜色映射
      },
      fontSize: {
        // ... 字体大小映射
      },
      // ... 其他配置
    }
  },
  plugins: []
}
```

### 步骤 3：迁移全局样式

1. 创建 `src/styles/tailwind.css`，添加 Tailwind 基础指令
2. 迁移 `variables.scss` 到 `tailwind.config.js`
3. 迁移 `mixins.scss` 中的工具类到 Tailwind 类名
4. 迁移 `global.scss` 中的工具类

### 步骤 4：逐组件迁移

按照优先级顺序（P0 → P1 → P2）逐个迁移组件：

1. 移除 `<style lang="scss" scoped>`
2. 将 SCSS 类名替换为 Tailwind 类名
3. 使用 `@apply` 提取重复的类名组合（可选）

### 步骤 5：清理与验证

1. 删除不再需要的 SCSS 文件
2. 更新 `main.js` 导入样式
3. 全面测试各页面功能

---

## 颜色变量映射表

| SCSS 变量                 | 当前值                      | Tailwind 类名                         |
| ------------------------- | --------------------------- | ------------------------------------- |
| `$color-primary`        | `#FBF7F2`                 | `bg-[#FBF7F2]`                      |
| `$color-accent`         | `#8B6F47`                 | `text-[#8B6F47]` / `bg-[#8B6F47]` |
| `$color-accent-light`   | `rgba(139, 111, 71, 0.1)` | `bg-[rgba(139,111,71,0.1)]`         |
| `$color-text-primary`   | `#333`                    | `text-gray-900`                     |
| `$color-text-regular`   | `#666`                    | `text-gray-600`                     |
| `$color-text-secondary` | `#999`                    | `text-gray-400`                     |
| `$color-text-white`     | `#fff`                    | `text-white`                        |
| `$color-bg-white`       | `#fff`                    | `bg-white`                          |
| `$color-bg-light`       | `#efefef`                 | `bg-gray-100`                       |
| `$color-border`         | `#dcdfe6`                 | `border-gray-200`                   |
| `$color-success`        | `#67c23a`                 | `text-green-600`                    |
| `$color-warning`        | `#e6a23c`                 | `text-yellow-600`                   |
| `$color-danger`         | `#f56c6c`                 | `text-red-600`                      |
| `$color-disabled`       | `#7f8c8d`                 | `text-gray-500`                     |

---

## 字体变量映射表

| SCSS 变量             | 当前值   | Tailwind 类名                         |
| --------------------- | -------- | ------------------------------------- |
| `$font-size-small`  | `12px` | `text-xs` (12px)                    |
| `$font-size-base`   | `14px` | `text-sm` (14px)                    |
| `$font-size-medium` | `16px` | `text-base` (16px)                  |
| `$font-size-large`  | `18px` | `text-lg` (18px)                    |
| `$font-size-xl`     | `20px` | `text-xl` (20px)                    |
| `$font-size-xxl`    | `28px` | `text-2xl` (24px) / `text-[28px]` |

---

## 间距变量映射表

| SCSS 变量        | 当前值   | Tailwind 类名         |
| ---------------- | -------- | --------------------- |
| `$spacing-xs`  | `8px`  | `gap-2` / `p-2`   |
| `$spacing-sm`  | `16px` | `gap-4` / `p-4`   |
| `$spacing-md`  | `24px` | `gap-6` / `p-6`   |
| `$spacing-lg`  | `32px` | `gap-8` / `p-8`   |
| `$spacing-xl`  | `40px` | `gap-10` / `p-10` |
| `$spacing-gap` | `12px` | `gap-3` / `p-3`   |

---

## 布局变量映射表

| SCSS 变量                | 当前值                            | Tailwind 类名  |
| ------------------------ | --------------------------------- | -------------- |
| `$border-radius-base`  | `4px`                           | `rounded`    |
| `$border-radius-small` | `2px`                           | `rounded-sm` |
| `$box-shadow-light`    | `0 2px 4px rgba(0, 0, 0, 0.08)` | `shadow-sm`  |
| `$box-shadow-base`     | `0 2px 8px rgba(0, 0, 0, 0.1)`  | `shadow`     |
| `$nav-height`          | `60px`                          | `h-[60px]`   |
| `$z-index-nav`         | `1000`                          | `z-1000`     |

---

## Mixin 迁移参考

| Mixin                 | SCSS 用法                    | Tailwind 等价                         |
| --------------------- | ---------------------------- | ------------------------------------- |
| `flex-center`       | `@include flex-center;`    | `flex items-center justify-center`  |
| `flex-between`      | `@include flex-between;`   | `flex items-center justify-between` |
| `flex-column`       | `@include flex-column;`    | `flex flex-col`                     |
| `no-select`         | `@include no-select;`      | `select-none`                       |
| `mobile`            | `@include mobile { ... }`  | `@media (max-width: 768px) { ... }` |
| `scrollbar($width)` | `@include scrollbar(8px);` | 自定义滚动条样式                      |

---

## 注意事项

1. **Element Plus 样式覆盖**：使用 `:deep()` 选择器继续工作
2. **动态类名**：需要添加到 `safelist` 配置
3. **KaTeX 样式**：保持原有 CSS，不迁移
4. **响应式设计**：使用 Tailwind 断点前缀（`sm:`, `md:`, `lg:`）
5. **过渡动画**：使用 Tailwind `transition-*` 类
6. **SCSS 文件**：迁移期间保留，组件全部迁移完成后删除

---

## 渐进式迁移策略

### 背景说明

移除 `vite.config.js` 的 SCSS 全局注入后，所有使用 SCSS 变量的组件会报错。为避免一次性影响全部组件，采用渐进式迁移策略。

### 策略要点

| 阶段   | 操作               | 说明                   |
| ------ | ------------------ | ---------------------- |
| 当前   | 恢复 SCSS 全局注入 | 保持现有组件正常工作   |
| 迁移中 | 按组件逐个迁移     | 每完成一个组件即验证   |
| 完成后 | 移除 SCSS 全局注入 | 所有组件迁移完毕后执行 |

### 迁移检查清单

- [ ] 使用 `grep -r "lang=\"scss\"" frontend/src` 搜索所有使用 SCSS 的组件
- [ ] 迁移完成后移除 `<style lang="scss">` 中的 `lang` 属性
- [ ] 最终移除前再次确认无 SCSS 变量引用
- [ ] 删除 `variables.scss`、`mixins.scss`、`global.scss`

### 回退方案

若迁移过程中遇到问题：

1. 可继续使用 SCSS（仅修改的组件使用 Tailwind）
2. 全局注入在迁移期间持续生效
3. 无需一次性完成全部迁移
