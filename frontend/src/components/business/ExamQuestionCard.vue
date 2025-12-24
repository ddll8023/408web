<template>
  <div class="exam-question-card" :data-density="density">
    <!-- 题目卡片（白色卡片） -->
    <div class="exam-question-card__question-card" v-if="exam">
      <div class="exam-question-card__question-content">
        <MarkdownViewer 
          :content="exam.content || ''" 
          variant="plain" 
          :max-image-height="maxImageHeight"
        />
      </div>

      <!-- 选择题：紧凑行式选项容器（div 重构） -->
      <div v-if="exam.questionType === 'CHOICE' && Object.keys(parsedOptions).length" class="exam-question-card__option-list">
        <div
          v-for="(value, key) in parsedOptions"
          :key="key"
          class="exam-question-card__option-row"
          :class="{
            'exam-question-card__option-row--correct': showAnswer && correctOptionKeys.includes(key),
            'exam-question-card__option-row--selected-correct': showAnswer && selectedOption === key && correctOptionKeys.includes(key),
            'exam-question-card__option-row--selected': selectedOption === key && !showAnswer,
            'exam-question-card__option-row--wrong': showAnswer && selectedOption === key && !correctOptionKeys.includes(key),
            'exam-question-card__option-row--clickable': selectable && !showAnswer
          }"
          @click="handleOptionClick(key)"
        >
          <span class="exam-question-card__option-letter">{{ key }}</span>
          <div class="exam-question-card__option-body">
            <MarkdownViewer 
              :content="String(value)" 
              variant="plain" 
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 答案卡片（米色主题卡片） -->
    <div v-if="exam?.answer" class="answer-card">
      <div class="answer-header">
        <el-icon class="answer-icon"><Select /></el-icon>
        <span>{{ exam?.questionType === 'CHOICE' ? '正确答案' : '参考答案' }}</span>
        <CustomButton
          v-if="showToggle"
          size="small"
          :type="showAnswer ? 'warning' : 'primary'"
          @click="$emit('toggle-answer')"
          style="margin-left: auto"
        >
          {{ showAnswer ? '隐藏答案' : '显示答案' }}
        </CustomButton>
      </div>

      <Transition name="answer-expand" mode="out-in">
        <div v-if="showAnswer" key="content" class="answer-content">
          <MarkdownViewer 
            :content="exam?.answer || ''" 
            variant="plain" 
            :max-image-height="maxImageHeight"
          />
        </div>
        <div v-else key="placeholder" class="answer-placeholder">
          <el-icon><Lock /></el-icon>
          <span>答案已隐藏，点击上方按钮显示</span>
        </div>
      </Transition>
    </div>
  </div>
  
</template>

<script setup>
/**
 * 通用题目卡片组件（紧凑样式）
 * 用途：统一渲染题干、选项与答案区域，替换各页面重复模板
 * 设计：遵循 KISS/YAGNI/SOLID（单一职责：渲染题目与答案）
 * Source: Element Plus 官方文档；@kangc/v-md-editor 官方文档
 */
import { computed, ref, watch } from 'vue'
import { Select, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'
import CustomButton from '@/components/basic/CustomButton.vue'

/**
 * Props
 */
const props = defineProps({
  /** 题目对象 */
  exam: { type: Object, required: true },
  /** 是否显示答案 */
  showAnswer: { type: Boolean, default: false },
  /** 紧凑密度：compact | comfortable */
  density: { type: String, default: 'compact' },
  /** 是否显示切换答案按钮（父组件也可自行放按钮） */
  showToggle: { type: Boolean, default: true },
  /** 是否允许点击选项选择（默认允许） */
  selectable: { type: Boolean, default: true }
})

const emit = defineEmits(['toggle-answer', 'answered'])

/**
 * 计算图片最大高度
 */
const maxImageHeight = computed(() => {
  // return props.density === 'comfortable' ? '400px' : '300px'
  return '440px'
})

/**
 * 用户选择的选项（用于视觉反馈）
 */
const selectedOption = ref(null)

/**
 * 监听 showAnswer 变化，当答案隐藏时重置选中状态
 */
watch(() => props.showAnswer, (newVal) => {
  if (!newVal) {
    selectedOption.value = null
  }
})

/**
 * 处理选项点击事件
 * 点击选项后，如果答案未显示，则自动显示答案
 */
const handleOptionClick = (optionKey) => {
  // 如果不可选择或答案已显示，则不处理
  if (!props.selectable || props.showAnswer) {
    return
  }
  
  // 记录用户选择的选项
  selectedOption.value = optionKey
  
  // 弹窗提示反馈
  if (correctOptionKeys.value.includes(optionKey)) {
    ElMessage.success({
      message: '回答正确！',
      duration: 1500
    })
  } else {
    ElMessage.error({
      message: '回答错误！',
      duration: 1500
    })
  }

  // 通知父组件：本题已作答
  emit('answered', {
    optionKey,
    correct: correctOptionKeys.value.includes(optionKey)
  })

  // 触发显示答案事件
  emit('toggle-answer')
}

/**
 * 解析选择题选项：兼容字符串(JSON)或对象
 */
const parsedOptions = computed(() => {
  if (!props.exam) return {}
  const options = props.exam.options
  if (!options) return {}
  try {
    if (typeof options === 'string') {
      return JSON.parse(options)
    }
    if (typeof options === 'object') {
      return options
    }
  } catch (e) {
    console.error('解析选项失败:', e)
  }
  return {}
})

/**
 * 从 answer 文本中解析选择题的正确选项字母
 * 兼容：
 * - 仅字母："C"、"AB" 等
 * - 带前缀："正确答案：C"、"答案：AB" 等（支持中文冒号）
 */
const correctOptionKeys = computed(() => {
  if (!props.exam || props.exam.questionType !== 'CHOICE') {
    return []
  }

  const raw = (props.exam.answer || '').toString().trim()
  if (!raw) return []

  // 优先从 "正确答案：XXX" 或 "答案：XXX" 中提取
  const keywordMatch = raw.match(/(?:正确答案|答案)[：:]\s*([A-H]+)/i)
  let letters = ''

  if (keywordMatch && keywordMatch[1]) {
    letters = keywordMatch[1]
  } else {
    // 若整段文本基本上就是选项字母（兼容旧数据仅存 "A" 或 "AB"）
    const compact = raw.replace(/\s+/g, '')
    if (/^[A-H]+$/i.test(compact)) {
      letters = compact
    }
  }

  if (!letters) return []

  const upper = letters.toUpperCase()
  const result = Array.from(new Set(upper.split(''))).filter(ch => /[A-H]/.test(ch))
  return result
})
</script>

<style lang="scss" scoped>
/**
 * 题目卡片样式 - 卡片分层式布局
 * 设计理念：题目与答案独立卡片，增强视觉层次感
 * 遵循项目设计规范：米色主题 + 深棕色强调色
 * Source: 基于 KISS/YAGNI/SOLID 原则重构
 */

/* 答题反馈动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

@keyframes pulse-success {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); background-color: rgba(103, 194, 58, 0.15); }
  100% { transform: scale(1); }
}

.exam-question-card {
  /* 题目卡片（白色） */
  &__question-card {
    position: relative;                     // 相对定位，用于定位复制按钮
    background-color: $color-bg-white;     // 纯白色
    border: 1px solid $color-border-light; // #dfe2e5
    border-radius: $border-radius-base;    // 4px
    box-shadow: $box-shadow-light;         // 0 2px 4px rgba(0, 0, 0, 0.08)
    padding: $spacing-md;                  // 24px
    margin-bottom: $spacing-md;            // 24px（与答案卡片间距）
    transition: $transition-base;          // 0.3s
    
    &:hover {
      box-shadow: $box-shadow-base;        // 0 2px 8px rgba(0, 0, 0, 0.1) - hover增强阴影
    }
  }
  
  &__question-content {
    width: 100%;                           // 确保容器占满宽度
    overflow: hidden;                      // 防止内容溢出
    
    // Markdown纯净模式，无额外padding
    :deep(.v-md-editor-preview) {
      padding: 0;
      background-color: transparent;
    }

    :deep(.github-markdown-body) {
      padding: 0;                          // 收紧 GitHub Markdown 默认内边距
    }
    
    // SVG自适应约束 - 防止题目中的SVG溢出
    :deep(svg) {
      max-width: 100% !important;
      height: auto !important;
      display: block;
      margin: $spacing-sm auto;            // 居中显示，上下留间距
    }
    
    // 图片居中
    :deep(img) {
      display: block;
      margin-left: auto;
      margin-right: auto;
    }
    
    // 表格居中
    :deep(table) {
      margin-left: auto;
      margin-right: auto;
    }
  }

  /* 选项列表（紧凑） */
  &__option-list {
    list-style: none;
    margin: $spacing-xs 0 0 0;             // 8px顶部间距（紧凑）
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;                              // 8px行距
  }

  &__option-row {
    display: flex;
    align-items: center;                   // 垂直居中
    gap: 6px;                              // 6px字母与内容间距
    padding: 4px 10px 4px 8px;             // 内边距
    min-height: 44px;                      // 最小高度保持视觉一致
    border: 1px solid $color-border-light; // 浅灰边框增加区分度
    border-left: 3px solid $color-accent-light; // 左侧浅棕色指示条
    border-radius: $border-radius-base;    // 4px
    background-color: $color-bg-white;     // 白色背景
    transition: $transition-fast;          // 0.15s

    &:hover {
      border-color: $color-border-light;
      border-left-color: $color-accent;    // 左侧指示条高亮
      background-color: $color-accent-light; // rgba(139, 111, 71, 0.1)
    }

    // 可点击状态（答案未显示时）
    &--clickable {
      cursor: pointer;
      
      &:hover {
        border-left-color: $color-accent;
        background-color: $color-accent-light;
        
        .exam-question-card__option-letter {
          background-color: $color-accent;
          color: $color-bg-white;          // hover时字母反色
          border-color: $color-accent;
        }
      }
      
      &:active {
        background-color: rgba($color-accent, 0.15);
      }
    }

    // 用户选中的选项（答案未显示时的视觉反馈）
    &--selected {
      border-color: rgba($color-primary, 0.3);
      border-left-color: $color-primary;   // 左侧指示条蓝色
      background-color: rgba(64, 158, 255, 0.1);
      
      .exam-question-card__option-letter {
        border-color: $color-primary;
        color: $color-primary;
        background-color: rgba(64, 158, 255, 0.1);
      }
    }

    // 用户选择的错误选项（显示答案时）
    &--wrong {
      animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
      border-color: rgba($color-danger, 0.3);
      border-left-color: $color-danger;    // 左侧指示条红色
      background-color: rgba(245, 108, 108, 0.1);
      
      .exam-question-card__option-letter {
        border-color: $color-danger;
        color: $color-danger;
        background-color: rgba(245, 108, 108, 0.1);
      }
    }

    // 正确答案（显示答案时）
    &--correct {
      border-color: rgba($color-success, 0.3);
      border-left-color: $color-success;   // 左侧指示条绿色
      background-color: rgba(103, 194, 58, 0.08);
      
      .exam-question-card__option-letter {
        border-color: $color-success;
        color: $color-success;
        background-color: rgba(103, 194, 58, 0.1);
      }
    }

    // 用户选中的正确选项（显示答案时的视觉反馈）
    &--selected-correct {
      animation: pulse-success 0.6s ease-out both;
      border-color: rgba($color-success, 0.3);
      border-left-color: $color-success;
      background-color: rgba(103, 194, 58, 0.12);
      
      .exam-question-card__option-letter {
        background-color: $color-success;
        color: #fff;
        border-color: $color-success;
      }
    }
  }

  &__option-letter {
    flex-shrink: 0;
    width: 22px;                           // 22px（稍大提升可点击性）
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1.5px solid $color-accent;     // 深棕色圆圈
    color: $color-accent;
    border-radius: 50%;
    font-weight: $font-weight-bold;        // 600
    font-size: 12px;                       // 12px
    line-height: 1;
    background-color: $color-bg-white;     // 白色背景增强对比度
    transition: $transition-fast;
  }

  &__option-body {
    flex: 1;
    min-width: 0;
    line-height: 1.4;
    overflow: hidden;
    display: flex;
    align-items: center;
    
    // 强制紧凑：移除 MarkdownViewer 内部所有额外间距
    :deep(.markdown-viewer) {
      width: 100%;
      min-height: auto !important;         // 移除最小高度限制
    }
    
    :deep(.v-md-editor-preview) {
      padding: 0 !important;               // 移除内边距
      min-height: auto !important;
    }
    
    :deep(.github-markdown-body) {
      padding: 0 !important;
      font-size: $font-size-base;          // 14px
    }
    
    :deep(p) {
      margin: 0 !important;
      padding: 0 !important;
      line-height: 1.5;
    }
    
    :deep(img) {
      max-height: 80px !important;         // 选项图片极小
      margin: 2px 0 !important;
    }

    :deep(svg) {
      max-width: 100% !important;
      height: auto !important;
      max-height: 60px !important;         // SVG也限制高度
      display: block;
      margin: 2px auto !important;
    }
  }

  &__option-text {
    white-space: pre-line;                 // 保留原始换行
    color: $color-text-primary;
    font-size: $font-size-base;
    margin: 0;                             // 去除额外间距，保持高度紧凑
  }

  /* 答案卡片（米色主题） */
  .answer-card {
    background-color: rgba(251, 247, 242, 0.5); // 米色半透明 #FBF7F2
    border: 1px solid rgba(139, 111, 71, 0.2);  // 深棕色淡边框
    border-left: 4px solid $color-accent;       // 左侧强调条（深棕色）
    border-radius: $border-radius-base;         // 4px
    padding: $spacing-sm;                       // 16px
    box-shadow: $box-shadow-light;              // 0 2px 4px rgba(0, 0, 0, 0.08)
    transition: $transition-base;               // 0.3s

    .answer-header {
      display: flex;
      align-items: center;
      gap: $spacing-xs;                         // 8px
      margin-bottom: $spacing-sm;               // 16px

      .answer-icon {
        font-size: $font-size-large;            // 18px
        color: $color-accent;                   // 深棕色
      }
      
      span {
        font-size: $font-size-base;             // 14px
        font-weight: $font-weight-medium;       // 500
        color: $color-text-primary;             // #333
      }
    }

    .answer-content {
      padding: $spacing-sm;                     // 16px
      background-color: $color-bg-white;        // 白色内容区
      border-radius: $border-radius-small;      // 2px
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); // 轻微内阴影
      overflow: hidden;                         // 防止内容溢出
      
      // SVG自适应约束 - 防止答案中的SVG溢出
      :deep(svg) {
        max-width: 100% !important;
        height: auto !important;
        display: block;
        margin: $spacing-sm auto;              // 居中显示，上下留间距
      }
      
      // 图片居中
      :deep(img) {
        display: block;
        margin-left: auto;
        margin-right: auto;
      }
      
      // 表格居中
      :deep(table) {
        margin-left: auto;
        margin-right: auto;
      }
    }

    .answer-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: $spacing-xs;                         // 8px
      padding: $spacing-md;                     // 24px
      background-color: rgba(255, 255, 255, 0.8);
      border-radius: $border-radius-small;      // 2px
      border: 2px dashed $color-border-base;    // #dcdfe6
      color: $color-text-secondary;             // #999
      font-size: $font-size-base;               // 14px
      
      .el-icon {
        font-size: $font-size-large;            // 18px
      }
    }
  }

  /* 密度：comfortable（稍大） */
  &[data-density='comfortable'] {
    .question-card {
      padding: $spacing-lg;                     // 32px（更宽松）
    }
    
    .option-row {
      padding: 6px 10px;                        // 适度上下内边距
    }
    
    .option-list {
      gap: $spacing-sm;                         // 16px行距
      margin-top: $spacing-md;                  // 24px顶部间距
    }
    
    .option-letter {
      width: 22px;                              // 稍大
      height: 22px;
      font-size: $font-size-small;              // 12px
    }
    
    .option-body {
      line-height: 1.5;                         // 稍微放松行高
    }
  }

  /* 移动端优化 */
  @include mobile {
    .question-card,
    .answer-card {
      padding: $spacing-sm;                     // 16px（缩小内边距）
    }
    
    .question-card {
      margin-bottom: $spacing-sm;               // 16px（缩小卡片间距）
    }
    
    .exam-question-card__option-row {
      padding: 2px 6px 2px 4px;                 // 移动端极度紧凑
      gap: 4px;
    }
    
    .exam-question-card__option-letter {
      width: 20px;                              // 移动端稍小
      height: 20px;
      font-size: 11px;
    }
    
    .exam-question-card__option-body {
      line-height: 1.3;                         // 移动端更紧凑行高
    }
    
    .exam-question-card__option-list {
      gap: 3px;                                 // 移动端更紧凑间距
    }
  }
}

/* ==================== 答案展开/收起过渡动画 ==================== */
.answer-expand-enter-active,
.answer-expand-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.answer-expand-enter-from {
  opacity: 0;
  transform: translateY(-12px);
  max-height: 0;
}

.answer-expand-enter-to {
  opacity: 1;
  transform: translateY(0);
  max-height: 1000px; // 足够大的值覆盖大多数内容
}

.answer-expand-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 1000px;
}

.answer-expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}

</style>


