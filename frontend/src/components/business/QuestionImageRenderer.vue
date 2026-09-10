<template>
  <div
    v-if="question"
    ref="captureRoot"
    class="question-image-renderer"
    aria-hidden="true"
  >
    <header class="question-image-renderer__header">
      <h1 class="question-image-renderer__title">{{ questionTitle }}</h1>
      <div class="question-image-renderer__meta">
        <span>{{ questionTypeLabel }}</span>
        <span v-for="category in categories" :key="category">{{ category }}</span>
        <span v-if="difficultyLabel">{{ difficultyLabel }}</span>
      </div>
    </header>

    <section v-if="includeQuestion && hasQuestion" class="question-image-renderer__section">
      <h2>题目</h2>
      <MarkdownViewer
        :content="question.content"
        variant="plain"
        max-image-height=""
        @rendered="handleMarkdownRendered"
      />
    </section>

    <section v-if="includeOptions && hasOptions" class="question-image-renderer__section">
      <h2>选项</h2>
      <div class="question-image-renderer__options">
        <div
          v-for="([key, value]) in optionEntries"
          :key="key"
          class="question-image-renderer__option"
        >
          <span class="question-image-renderer__option-key">{{ key }}.</span>
          <MarkdownViewer
            :content="value"
            variant="plain"
            max-image-height=""
            @rendered="handleMarkdownRendered"
          />
        </div>
      </div>
    </section>

    <section v-if="includeAnswer && hasAnswer" class="question-image-renderer__section">
      <h2>答案</h2>
      <MarkdownViewer
        :content="question.answer || ''"
        variant="plain"
        max-image-height=""
        @rendered="handleMarkdownRendered"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { toBlob } from 'html-to-image'
import type { ExamQuestion, MockQuestion } from '@/types'
import { parseQuestionOptions } from '@/utils/questionOptions'
import { getDifficultyLabel } from '@/constants/exam'
import type { QuestionImageCopyScope } from '@/utils/questionCopy'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'

type Question = ExamQuestion | MockQuestion

interface Props {
  question: Question
  scope: QuestionImageCopyScope
}

const props = defineProps<Props>()
const captureRoot = ref<HTMLElement | null>(null)
const renderedCount = ref(0)

const questionTitle = computed(() => {
  const current = props.question
  const questionNumber = current.questionNumber == null ? '' : `第${current.questionNumber}题`

  if ('source' in current) {
    return [current.source, current.title || '', questionNumber]
      .filter(Boolean)
      .join(' · ') || '模拟题'
  }

  return [current.year != null ? `${current.year}年真题` : '真题', questionNumber]
    .filter(Boolean)
    .join(' ')
})

const questionTypeLabel = computed(() => {
  return props.question.questionType === 'CHOICE' ? '选择题' : '主观题'
})

const categories = computed(() => {
  return Array.isArray(props.question.category)
    ? props.question.category.filter(category => category.trim())
    : []
})

const difficultyLabel = computed(() => getDifficultyLabel(props.question.difficulty))
const hasQuestion = computed(() => Boolean(props.question.content?.trim()))
const hasAnswer = computed(() => Boolean(props.question.answer?.trim()))

const parsedOptions = computed(() => {
  if (props.question.questionType !== 'CHOICE') return null
  return parseQuestionOptions(props.question.options)
})

const optionEntries = computed(() => Object.entries(parsedOptions.value || {}))
const hasOptions = computed(() => optionEntries.value.length > 0)

const includeQuestion = computed(() => props.scope === 'question-options' || props.scope === 'all')
const includeOptions = computed(() => props.scope === 'question-options' || props.scope === 'all')
const includeAnswer = computed(() => props.scope === 'answer' || props.scope === 'all')
const hasRenderableContent = computed(() => {
  return (includeQuestion.value && hasQuestion.value) ||
    (includeOptions.value && hasOptions.value) ||
    (includeAnswer.value && hasAnswer.value)
})

const handleMarkdownRendered = () => {
  renderedCount.value += 1
}

const wait = (milliseconds: number) => {
  return new Promise<void>(resolve => window.setTimeout(resolve, milliseconds))
}

const waitForNextFrame = () => {
  return new Promise<void>(resolve => {
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => resolve())
    } else {
      window.setTimeout(resolve, 0)
    }
  })
}

const waitForMarkdown = async (root: HTMLElement) => {
  const expectedCount = root.querySelectorAll('.markdown-viewer').length
  if (expectedCount === 0) return

  const deadline = Date.now() + 2500
  while (renderedCount.value < expectedCount && Date.now() < deadline) {
    await wait(16)
  }

  if (renderedCount.value < expectedCount) {
    throw new Error('MARKDOWN_RENDER_TIMEOUT')
  }
}

const waitForImages = async (root: HTMLElement) => {
  const images = Array.from(root.querySelectorAll('img'))

  await Promise.all(images.map(async image => {
    // 截图节点位于视口外，避免 lazy 图片一直等待浏览器调度。
    image.loading = 'eager'

    if (!image.complete) {
      await new Promise<void>(resolve => {
        const timeout = window.setTimeout(resolve, 5000)
        const finish = () => {
          window.clearTimeout(timeout)
          image.removeEventListener('load', finish)
          image.removeEventListener('error', finish)
          resolve()
        }
        image.addEventListener('load', finish, { once: true })
        image.addEventListener('error', finish, { once: true })
      })
    }

    if (image.naturalWidth === 0) {
      throw new Error('IMAGE_LOAD_FAILED')
    }

    if (typeof image.decode === 'function') {
      try {
        await image.decode()
      } catch {
        // 已经有可用 naturalWidth 时，忽略浏览器解码 API 的偶发拒绝。
      }
    }
  }))
}

const capture = async (): Promise<Blob> => {
  if (!hasRenderableContent.value) {
    throw new Error('NO_COPY_CONTENT')
  }

  await nextTick()
  const root = captureRoot.value
  if (!root) {
    throw new Error('IMAGE_RENDERER_NOT_READY')
  }

  await waitForMarkdown(root)
  if (document.fonts) {
    await document.fonts.ready
  }
  await waitForImages(root)
  await waitForNextFrame()

  const blob = await toBlob(root, {
    backgroundColor: '#ffffff',
    cacheBust: true,
    pixelRatio: 2,
    // 原节点位于视口外，截图副本必须回到画布原点。
    style: {
      position: 'static',
      left: '0',
      top: '0',
      zIndex: 'auto'
    }
  })

  if (!blob) {
    throw new Error('IMAGE_BLOB_EMPTY')
  }

  return blob
}

defineExpose({ capture })
</script>

<style scoped>
.question-image-renderer {
  position: fixed;
  top: 0;
  left: -100000px;
  z-index: 0;
  box-sizing: border-box;
  width: 760px;
  padding: 32px;
  overflow: visible;
  background: #fff;
  color: #333;
  font-family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif;
  font-size: 16px;
  line-height: 1.6;
  pointer-events: none;
}

.question-image-renderer__header {
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.question-image-renderer__title {
  margin: 0;
  color: #374151;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}

.question-image-renderer__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: #8b6f47;
  font-size: 13px;
}

.question-image-renderer__meta span {
  padding: 2px 8px;
  border: 1px solid rgba(139, 111, 71, 0.25);
  border-radius: 999px;
}

.question-image-renderer__section {
  margin-top: 24px;
}

.question-image-renderer__section h2 {
  margin: 0 0 10px;
  color: #4b5563;
  font-size: 17px;
  font-weight: 700;
}

.question-image-renderer__options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.question-image-renderer__option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.question-image-renderer__option-key {
  flex: 0 0 auto;
  color: #8b6f47;
  font-weight: 700;
}

.question-image-renderer__option :deep(.markdown-viewer) {
  flex: 1;
  min-width: 0;
}

.question-image-renderer :deep(.markdown-viewer) {
  width: 100%;
  min-height: auto;
}

.question-image-renderer :deep(.v-md-editor-preview),
.question-image-renderer :deep(.github-markdown-body) {
  padding: 0;
  background: transparent;
}

.question-image-renderer :deep(img),
.question-image-renderer :deep(svg) {
  max-width: 100%;
  height: auto;
}

.question-image-renderer :deep(pre) {
  overflow: visible;
  white-space: pre-wrap;
}

.question-image-renderer :deep(table) {
  max-width: 100%;
}
</style>
