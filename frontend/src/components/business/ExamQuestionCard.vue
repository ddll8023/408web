<!-- 通用题目内容卡片：统一渲染真题、模拟题和改编题的题干、选项与答案。 -->
<template>
  <div class="exam-question-card" :data-density="density">
    <div v-if="exam" class="exam-question-card__question-card">
      <div class="exam-question-card__question-content w-full overflow-hidden">
        <MarkdownViewer
          :content="exam.content || ''"
          variant="plain"
          resizable
        />
      </div>

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
          :role="selectable && !showAnswer ? 'button' : undefined"
          :tabindex="selectable && !showAnswer ? 0 : -1"
          :aria-pressed="selectedOption === key"
          :aria-disabled="!selectable || showAnswer"
          :aria-label="optionStatusLabel(key) ? `选项 ${key}，${optionStatusLabel(key)}` : `选项 ${key}`"
          @click="handleOptionClick(key)"
          @keydown.enter.prevent="handleOptionClick(key)"
          @keydown.space.prevent="handleOptionClick(key)"
        >
          <span class="exam-question-card__option-letter">{{ key }}</span>
          <div class="exam-question-card__option-body min-w-0 overflow-hidden">
            <MarkdownViewer
              :content="String(value)"
              variant="plain"
              content-role="option"
            />
          </div>
          <span
            v-if="optionStatusLabel(key)"
            class="exam-question-card__option-status"
            :class="{ 'exam-question-card__option-status--correct': correctOptionKeys.includes(key) }"
          >
            <font-awesome-icon :icon="['fas', correctOptionKeys.includes(key) ? 'check' : 'times']" aria-hidden="true" />
            {{ optionStatusLabel(key) }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="exam?.answer" class="answer-card">
      <div class="answer-header">
        <font-awesome-icon :icon="['fas', showAnswer ? 'book' : 'lock']" class="answer-icon" aria-hidden="true" />
        <span class="answer-label">{{ exam.questionType === 'CHOICE' ? '答案与解析' : '参考答案与解析' }}</span>
        <CustomButton
          v-if="showToggle"
          size="sm"
          type="text"
          class="ml-auto"
          :aria-expanded="showAnswer"
          @click="$emit('toggle-answer')"
        >
          {{ showAnswer ? '收起解析' : '显示答案' }}
          <font-awesome-icon :icon="['fas', showAnswer ? 'chevron-up' : 'chevron-down']" class="ml-1" aria-hidden="true" />
        </CustomButton>
      </div>

      <div ref="answerTransitionContainer" class="answer-transition-container">
        <Transition name="answer-expand">
          <div v-if="showAnswer" key="content" class="answer-content overflow-hidden">
            <MarkdownViewer
              :content="exam.answer || ''"
              variant="plain"
            />
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { AdaptationQuestion, ExamQuestion, MockQuestion } from '@/types'
/**
 * 通用题目卡片组件（紧凑样式）
 * 用途：统一渲染真题、模拟题和改编题的题干、选项与答案区域
 * 设计：遵循 KISS/YAGNI/SOLID（单一职责：渲染题目与答案）
 * Source: @kangc/v-md-editor 官方文档
 */
import { parseOptions } from '@/composables/questionFormTypes'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import { useToast } from '@/composables/useToast'

/**
 * Props
 */
const props = defineProps({
  /** 题目对象 */
  exam: { type: Object as PropType<AdaptationQuestion | ExamQuestion | MockQuestion>, required: true },
  /** 是否显示答案 */
  showAnswer: { type: Boolean, default: false },
  /** 紧凑密度：compact | comfortable */
  density: { type: String, default: 'compact' },
  /** 是否显示切换答案按钮（父组件也可自行放按钮） */
  showToggle: { type: Boolean, default: true },
  /** 是否允许点击选项选择（默认允许） */
  selectable: { type: Boolean, default: true }
})

const emit = defineEmits<{ 'toggle-answer': []; answered: [payload: { optionKey: string; correct: boolean }] }>()
const { showToast } = useToast()

/**
 * 用户选择的选项（用于视觉反馈）
 */
const selectedOption = ref<string | null>(null)

/**
 * 外层容器统一承接答案区域的高度变化，避免旧内容和新占位各自从 0 过渡，
 * 导致收缩时先塌陷再补回一小段高度。
 */
const answerTransitionContainer = ref<HTMLElement | null>(null)
const answerTransitionDuration = 280
let answerTransitionSequence = 0
let answerTransitionFrame: number | null = null
let answerTransitionTimer: number | null = null
let answerTransitionEndHandler: ((event: TransitionEvent) => void) | null = null

const stopAnswerTransition = () => {
  const container = answerTransitionContainer.value

  if (answerTransitionFrame !== null) {
    cancelAnimationFrame(answerTransitionFrame)
    answerTransitionFrame = null
  }

  if (answerTransitionTimer !== null) {
    window.clearTimeout(answerTransitionTimer)
    answerTransitionTimer = null
  }

  if (container && answerTransitionEndHandler) {
    container.removeEventListener('transitionend', answerTransitionEndHandler)
  }
  answerTransitionEndHandler = null
}

const measureNaturalHeight = (container: HTMLElement): number => {
  const previousHeight = container.style.height
  container.style.height = 'auto'
  const naturalHeight = container.getBoundingClientRect().height
  container.style.height = previousHeight
  return naturalHeight
}

const animateAnswerContainer = async () => {
  const container = answerTransitionContainer.value
  if (!container) return

  const startHeight = container.getBoundingClientRect().height
  const sequence = ++answerTransitionSequence

  stopAnswerTransition()
  container.style.height = `${startHeight}px`

  await nextTick()

  if (sequence !== answerTransitionSequence || answerTransitionContainer.value !== container) {
    return
  }

  const targetHeight = measureNaturalHeight(container)
  // 确保浏览器先提交起始高度，再开始向目标高度过渡。
  void container.offsetHeight

  const finish = () => {
    if (sequence !== answerTransitionSequence) return

    stopAnswerTransition()
    container.style.removeProperty('height')
  }

  answerTransitionEndHandler = (event: TransitionEvent) => {
    if (event.target === container && event.propertyName === 'height') {
      finish()
    }
  }
  container.addEventListener('transitionend', answerTransitionEndHandler)

  answerTransitionFrame = requestAnimationFrame(() => {
    answerTransitionFrame = null
    if (sequence === answerTransitionSequence) {
      container.style.height = `${targetHeight}px`
    }
  })

  // 没有 transitionend 时也能恢复 auto，避免容器长期保持固定高度。
  answerTransitionTimer = window.setTimeout(finish, answerTransitionDuration + 80)
}

onBeforeUnmount(() => {
  answerTransitionSequence += 1
  stopAnswerTransition()
})

/**
 * 监听 showAnswer 变化，当答案隐藏时重置选中状态
 */
watch(() => props.showAnswer, (newVal) => {
  if (!newVal) {
    selectedOption.value = null
  }

  void animateAnswerContainer()
})

/**
 * 处理选项点击事件
 * 点击选项后，如果答案未显示，则自动显示答案
 */
const handleOptionClick = (optionKey: string) => {
  // 如果不可选择或答案已显示，则不处理
  if (!props.selectable || props.showAnswer) {
    return
  }
  
  // 记录用户选择的选项
  selectedOption.value = optionKey
  
  // 弹窗提示反馈
  if (correctOptionKeys.value.includes(optionKey)) {
    showToast('回答正确！', 'success')
  } else {
    showToast('回答错误！', 'error')
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
      return parseOptions(options)
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

/**
 * 选项在判题后的状态文案，可见文字与无障碍标签共用；
 * 未判题时返回空字符串，表示不展示状态。
 */
const optionStatusLabel = (key: string) => {
  if (!props.showAnswer) return ''
  if (correctOptionKeys.value.includes(key)) {
    return selectedOption.value === key ? '回答正确' : '正确答案'
  }
  return selectedOption.value === key ? '回答错误' : ''
}
</script>

<style scoped>
/* 答案高度过渡继续由原有容器承接，隐藏时不再保留大块占位。 */
.answer-expand-enter-active,
.answer-expand-leave-active {
  transition:
    opacity 0.18s ease-out,
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: opacity, transform;
}

.answer-transition-container {
  position: relative;
  overflow: hidden;
  transition: height 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.answer-expand-leave-active {
  position: absolute;
  inset: 0 0 auto;
  width: 100%;
  pointer-events: none;
}

.answer-expand-enter-from,
.answer-expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.answer-expand-enter-to,
.answer-expand-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.exam-question-card {
  color: var(--brand-ink);
}

.exam-question-card__question-content :deep(.v-md-editor-preview) {
  padding: 0;
  background-color: transparent;
}

.exam-question-card__question-content :deep(.github-markdown-body) {
  padding: 0;
}

.exam-question-card__question-content :deep(table),
.answer-content :deep(table) {
  margin: 0 auto;
}

.exam-question-card__option-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 14px;
}

.exam-question-card__option-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  column-gap: 10px;
  row-gap: 6px;
  min-height: 44px;
  padding: 8px 10px;
  border: 1px solid #dfe3e8;
  border-radius: 8px;
  background-color: #fff;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.exam-question-card__option-body {
  flex: 1 1 auto;
  min-width: 0;
}

.exam-question-card__option-row:focus-visible {
  outline: 2px solid var(--brand-accent);
  outline-offset: 2px;
}

.exam-question-card__option-letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid #dfe3e8;
  border-radius: 8px;
  color: #5b6674;
  background-color: #eef1f4;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  transition: color 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
}

/* 仅调整阅读选项的排版，保留 Markdown 的媒体尺寸变量和复制规则。 */
.exam-question-card__option-body :deep(.markdown-viewer.is-option) {
  font-size: 16px;
  line-height: 1.6;
}

.exam-question-card__option-row--clickable {
  cursor: pointer;
}

/* 已判题的选项不再响应悬停染色，避免覆盖正确或错误反馈。 */
.exam-question-card__option-row--clickable:hover {
  border-color: var(--brand-accent);
  background-color: color-mix(in srgb, var(--brand-accent) 8%, white);
}

.exam-question-card__option-row--clickable:hover .exam-question-card__option-letter {
  border-color: var(--brand-accent);
  color: var(--brand-accent);
}

.exam-question-card__option-row--clickable:active,
.exam-question-card__option-row--selected {
  border-color: var(--brand-accent);
  background-color: color-mix(in srgb, var(--brand-accent) 12%, white);
}

.exam-question-card__option-row--selected .exam-question-card__option-letter {
  border-color: var(--brand-accent);
  color: #fff;
  background-color: var(--brand-accent);
}

.exam-question-card__option-row--correct {
  border-color: #7cc39c;
  background-color: #eaf7f0;
}

.exam-question-card__option-row--correct .exam-question-card__option-letter {
  border-color: #7cc39c;
  color: #10613f;
  background-color: #d8efe3;
}

.exam-question-card__option-row--selected-correct .exam-question-card__option-letter {
  border-color: #10613f;
  color: #fff;
  background-color: #10613f;
}

.exam-question-card__option-row--wrong {
  border-color: #d99c93;
  background-color: #fdeeea;
}

.exam-question-card__option-row--wrong .exam-question-card__option-letter {
  border-color: #d99c93;
  color: #a63a2b;
  background-color: #f9dcd5;
}

.exam-question-card__option-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex: none;
  margin-top: 4px;
  margin-left: auto;
  /* 默认取错误色，正确状态由下方修饰类覆盖为绿色。 */
  color: #a63a2b;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.6;
  white-space: nowrap;
}

.exam-question-card__option-status--correct {
  color: #10613f;
}

.answer-card {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.answer-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.answer-icon {
  color: var(--brand-ink-soft);
  font-size: 13px;
}

.answer-label {
  color: var(--brand-ink-soft);
  font-size: 14px;
  font-weight: 500;
}

.answer-content {
  margin-top: 8px;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--brand-surface);
}

.exam-question-card[data-density='comfortable'] .exam-question-card__option-list {
  gap: 12px;
  margin-top: 18px;
}

.exam-question-card[data-density='comfortable'] .exam-question-card__option-row {
  padding: 12px;
}

.exam-question-card[data-density='comfortable'] .answer-content {
  padding: 16px;
}

@media (max-width: 767px) {
  .exam-question-card__option-row,
  .exam-question-card[data-density='comfortable'] .exam-question-card__option-row {
    column-gap: 8px;
    padding: 8px 10px;
  }

  /* 窄屏状态下状态文字独占一行，不再靠右挤压题干。 */
  .exam-question-card__option-status {
    margin-left: 0;
    margin-top: 0;
  }

  .exam-question-card__option-list {
    gap: 6px;
    margin-top: 12px;
  }

  .answer-card {
    margin-top: 14px;
  }

  .answer-content,
  .exam-question-card[data-density='comfortable'] .answer-content {
    padding: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .exam-question-card__option-row,
  .exam-question-card__option-letter {
    transition: none;
  }

  .answer-transition-container,
  .answer-expand-enter-active,
  .answer-expand-leave-active {
    transition-duration: 0.01s;
  }
}
</style>
