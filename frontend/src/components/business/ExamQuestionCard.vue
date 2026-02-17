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

<style scoped>
/**
 * 题目卡片样式 - 卡片分层式布局
 * 设计理念：题目与答案独立卡片，增强视觉层次感
 * 遵循项目设计规范：米色主题 + 深棕色强调色
 * Source: 基于 KISS/YAGNI/SOLID 原则重构
 * 已迁移至 Tailwind CSS
 */

/* 答题反馈动画 - CSS 动画无法用 Tailwind 完全替代 */
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
  max-height: 1000px;
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

/* 题目卡片（白色） */
.exam-question-card__question-card {
  position: relative;
  background-color: #fff;
  border: 1px solid #dfe2e5;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  padding: 24px;
  margin-bottom: 24px;
  transition: all 0.3s ease;
}

.exam-question-card__question-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.exam-question-card__question-content {
  width: 100%;
  overflow: hidden;
}

/* Markdown纯净模式，无额外padding */
.exam-question-card__question-content :deep(.v-md-editor-preview) {
  padding: 0;
  background-color: transparent;
}

.exam-question-card__question-content :deep(.github-markdown-body) {
  padding: 0;
}

/* SVG自适应约束 - 防止题目中的SVG溢出 */
.exam-question-card__question-content :deep(svg) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 16px auto;
}

/* 图片居中 */
.exam-question-card__question-content :deep(img) {
  display: block;
  margin-left: auto;
  margin-right: auto;
}

/* 表格居中 */
.exam-question-card__question-content :deep(table) {
  margin-left: auto;
  margin-right: auto;
}

/* 选项列表（紧凑） */
.exam-question-card__option-list {
  list-style: none;
  margin: 8px 0 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exam-question-card__option-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 8px;
  min-height: 44px;
  border: 1px solid #dfe2e5;
  border-left: 3px solid rgba(139, 111, 71, 0.1);
  border-radius: 4px;
  background-color: #fff;
  transition: all 0.15s ease;
}

.exam-question-card__option-row:hover {
  border-color: #dfe2e5;
  border-left-color: #8B6F47;
  background-color: rgba(139, 111, 71, 0.1);
}

/* 可点击状态（答案未显示时） */
.exam-question-card__option-row--clickable {
  cursor: pointer;
}

.exam-question-card__option-row--clickable:hover {
  border-left-color: #8B6F47;
  background-color: rgba(139, 111, 71, 0.1);
}

.exam-question-card__option-row--clickable:hover .exam-question-card__option-letter {
  background-color: #8B6F47;
  color: #fff;
  border-color: #8B6F47;
}

.exam-question-card__option-row--clickable:active {
  background-color: rgba(139, 111, 71, 0.15);
}

/* 用户选中的选项（答案未显示时的视觉反馈） */
.exam-question-card__option-row--selected {
  border-color: rgba(251, 247, 242, 0.3);
  border-left-color: #FBF7F2;
  background-color: rgba(64, 158, 255, 0.1);
}

.exam-question-card__option-row--selected .exam-question-card__option-letter {
  border-color: #FBF7F2;
  color: #FBF7F2;
  background-color: rgba(64, 158, 255, 0.1);
}

/* 用户选择的错误选项（显示答案时） */
.exam-question-card__option-row--wrong {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
  border-color: rgba(245, 108, 108, 0.3);
  border-left-color: #f56c6c;
  background-color: rgba(245, 108, 108, 0.1);
}

.exam-question-card__option-row--wrong .exam-question-card__option-letter {
  border-color: #f56c6c;
  color: #f56c6c;
  background-color: rgba(245, 108, 108, 0.1);
}

/* 正确答案（显示答案时） */
.exam-question-card__option-row--correct {
  border-color: rgba(103, 194, 58, 0.3);
  border-left-color: #67c23a;
  background-color: rgba(103, 194, 58, 0.08);
}

.exam-question-card__option-row--correct .exam-question-card__option-letter {
  border-color: #67c23a;
  color: #67c23a;
  background-color: rgba(103, 194, 58, 0.1);
}

/* 用户选中的正确选项（显示答案时的视觉反馈） */
.exam-question-card__option-row--selected-correct {
  animation: pulse-success 0.6s ease-out both;
  border-color: rgba(103, 194, 58, 0.3);
  border-left-color: #67c23a;
  background-color: rgba(103, 194, 58, 0.12);
}

.exam-question-card__option-row--selected-correct .exam-question-card__option-letter {
  background-color: #67c23a;
  color: #fff;
  border-color: #67c23a;
}

.exam-question-card__option-letter {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #8B6F47;
  color: #8B6F47;
  border-radius: 50%;
  font-weight: 600;
  font-size: 12px;
  line-height: 1;
  background-color: #fff;
  transition: all 0.15s ease;
}

.exam-question-card__option-body {
  flex: 1;
  min-width: 0;
  line-height: 1.4;
  overflow: hidden;
  display: flex;
  align-items: center;
}

/* 强制紧凑：移除 MarkdownViewer 内部所有额外间距 */
.exam-question-card__option-body :deep(.markdown-viewer) {
  width: 100%;
  min-height: auto !important;
}

.exam-question-card__option-body :deep(.v-md-editor-preview) {
  padding: 0 !important;
  min-height: auto !important;
}

.exam-question-card__option-body :deep(.github-markdown-body) {
  padding: 0 !important;
  font-size: 14px;
}

.exam-question-card__option-body :deep(p) {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.5;
}

.exam-question-card__option-body :deep(img) {
  max-height: 80px !important;
  margin: 2px 0 !important;
}

.exam-question-card__option-body :deep(svg) {
  max-width: 100% !important;
  height: auto !important;
  max-height: 60px !important;
  display: block;
  margin: 2px auto !important;
}

.exam-question-card__option-text {
  white-space: pre-line;
  color: #333;
  font-size: 14px;
  margin: 0;
}

/* 答案卡片（米色主题） */
.answer-card {
  background-color: rgba(251, 247, 242, 0.5);
  border: 1px solid rgba(139, 111, 71, 0.2);
  border-left: 4px solid #8B6F47;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.answer-card .answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.answer-card .answer-header .answer-icon {
  font-size: 18px;
  color: #8B6F47;
}

.answer-card .answer-header span {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.answer-card .answer-content {
  padding: 16px;
  background-color: #fff;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* SVG自适应约束 - 防止答案中的SVG溢出 */
.answer-card .answer-content :deep(svg) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 16px auto;
}

/* 图片居中 */
.answer-card .answer-content :deep(img) {
  display: block;
  margin-left: auto;
  margin-right: auto;
}

/* 表格居中 */
.answer-card .answer-content :deep(table) {
  margin-left: auto;
  margin-right: auto;
}

.answer-card .answer-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  border: 2px dashed #dcdfe6;
  color: #999;
  font-size: 14px;
}

.answer-card .answer-placeholder .el-icon {
  font-size: 18px;
}

/* 密度：comfortable（稍大） */
.exam-question-card[data-density='comfortable'] .question-card,
.exam-question-card[data-density='comfortable'] .exam-question-card__question-card {
  padding: 32px;
}

.exam-question-card[data-density='comfortable'] .option-row,
.exam-question-card[data-density='comfortable'] .exam-question-card__option-row {
  padding: 6px 10px;
}

.exam-question-card[data-density='comfortable'] .option-list,
.exam-question-card[data-density='comfortable'] .exam-question-card__option-list {
  gap: 16px;
  margin-top: 24px;
}

.exam-question-card[data-density='comfortable'] .option-letter,
.exam-question-card[data-density='comfortable'] .exam-question-card__option-letter {
  width: 22px;
  height: 22px;
  font-size: 12px;
}

.exam-question-card[data-density='comfortable'] .option-body,
.exam-question-card[data-density='comfortable'] .exam-question-card__option-body {
  line-height: 1.5;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .exam-question-card__question-card,
  .answer-card {
    padding: 16px;
  }

  .exam-question-card__question-card {
    margin-bottom: 16px;
  }

  .exam-question-card__option-row {
    padding: 2px 6px 2px 4px;
    gap: 4px;
  }

  .exam-question-card__option-letter {
    width: 20px;
    height: 20px;
    font-size: 11px;
  }

  .exam-question-card__option-body {
    line-height: 1.3;
  }

  .exam-question-card__option-list {
    gap: 3px;
  }
}
</style>


