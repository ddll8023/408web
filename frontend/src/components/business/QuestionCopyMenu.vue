<!-- 题目复制菜单：按视口宽度调整菜单列数。 -->
<template>
  <Dropdown
    v-if="!props.headless"
    trigger="click"
    :disabled="isCopying"
    menu-class="question-copy-dropdown"
    @command="handleCommand"
  >
    <template #trigger>
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', 'copy']"
        :loading="isCopying"
      >
        {{ isCopying ? '生成中' : '复制' }}
      </CustomButton>
    </template>

    <template #dropdown>
      <div class="question-copy-menu" aria-label="复制内容">
        <section
          v-for="section in menuSections"
          :key="section.key"
          class="question-copy-menu__section"
          :aria-label="section.title"
          role="group"
        >
          <div class="question-copy-menu__heading">
            <span class="question-copy-menu__icon" aria-hidden="true">
              <font-awesome-icon :icon="section.icon" />
            </span>
            <span class="question-copy-menu__heading-copy">
              <span class="question-copy-menu__title">{{ section.title }}</span>
              <span class="question-copy-menu__description">{{ section.description }}</span>
            </span>
          </div>

          <div class="question-copy-menu__items">
            <DropdownItem
              v-for="item in section.items"
              :key="item.command"
              :command="item.command"
              :disabled="isCopying"
              :class="{ 'question-copy-menu__item--wide': item.wide }"
            >
              <span class="question-copy-menu__item-label">{{ item.label }}</span>
            </DropdownItem>
          </div>
        </section>
      </div>
    </template>
  </Dropdown>

  <QuestionImageRenderer
    v-if="renderScope"
    ref="imageRenderer"
    :question="question"
    :scope="renderScope ?? 'all'"
  />
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import { computed, nextTick, ref } from 'vue'
import type { AdaptationQuestion, ExamQuestion, MockQuestion } from '@/types'
import {
  copyImageBlob,
  copyRichContent,
  getImageCopyScope,
  getRichCopyScope,
  type ImageCopyResult,
  type QuestionContentScope,
  type QuestionImageCopyScope,
  type QuestionRichCopyScope,
  type RichCopyContent,
  type RichCopyResult,
} from '@/utils/questionCopy'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import QuestionImageRenderer from '@/components/business/QuestionImageRenderer.vue'

type CopyMenuSectionKey = 'markdown' | 'word' | 'image'
type CopyMenuIcon = ['fas', 'file-lines'] | ['fas', 'file-word'] | ['fas', 'file']

interface CopyMenuItem {
  command: string
  label: string
  wide?: boolean
}

interface CopyMenuSection {
  key: CopyMenuSectionKey
  title: string
  description: string
  icon: CopyMenuIcon
  items: CopyMenuItem[]
}

/** 题目复制菜单，统一提供 Markdown、Word 富文本和图片复制入口。 */
const props = defineProps({
  question: {
    type: Object as PropType<AdaptationQuestion | ExamQuestion | MockQuestion>,
    required: true
  },
  headless: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  copy: [command: string]
  'word-copied': [result: RichCopyResult]
}>()
const { showToast } = useToast()

interface QuestionRendererRef {
  capture: () => Promise<Blob>
  getClipboardContent: () => Promise<RichCopyContent>
}

const renderScope = ref<QuestionContentScope | null>(null)
const imageRenderer = ref<QuestionRendererRef | null>(null)
const isImageCopying = ref(false)
const isWordCopying = ref(false)
const isCopying = computed(() => isImageCopying.value || isWordCopying.value)

const hasOptions = computed(() => {
  return props.question.questionType === 'CHOICE' && Boolean(props.question.options)
})

const hasAnswer = computed(() => Boolean(props.question.answer?.trim()))

const menuSections = computed<CopyMenuSection[]>(() => [
  {
    key: 'markdown',
    title: 'Markdown 格式',
    description: '保留排版',
    icon: ['fas', 'file-lines'],
    items: [
      { command: 'md-question', label: '复制题目' },
      ...(hasOptions.value ? [{ command: 'md-options', label: '复制选项' }] : []),
      ...(hasAnswer.value ? [{ command: 'md-answer', label: '复制答案' }] : []),
      ...((hasAnswer.value || hasOptions.value)
        ? [{ command: 'md-all', label: '复制完整内容', wide: true }]
        : [])
    ]
  },
  {
    key: 'word',
    title: 'Word 格式',
    description: '可直接粘贴',
    icon: ['fas', 'file-word'],
    items: [
      { command: 'word-question', label: '复制题目' },
      ...(hasOptions.value ? [{ command: 'word-options', label: '复制选项' }] : []),
      ...(hasAnswer.value ? [{ command: 'word-answer', label: '复制答案' }] : []),
      ...((hasAnswer.value || hasOptions.value)
        ? [{ command: 'word-all', label: '复制完整内容', wide: true }]
        : [])
    ]
  },
  {
    key: 'image',
    title: '图片格式',
    description: '生成 PNG',
    icon: ['fas', 'file'],
    items: [
      { command: 'image-question-options', label: '复制题目 + 选项' },
      ...(hasAnswer.value ? [{ command: 'image-answer', label: '复制答案' }] : []),
      ...((hasAnswer.value || hasOptions.value)
        ? [{ command: 'image-all', label: '复制全部内容', wide: true }]
        : [])
    ]
  }
])

const getImageFilename = (scope: QuestionImageCopyScope) => {
  const question = props.question
  let prefix = '改编题'
  if ('source' in question) {
    prefix = question.title || question.source || '模拟题'
  } else if ('year' in question) {
    prefix = `${question.year}年真题`
  }
  const safePrefix = prefix.replace(/[\\/:*?"<>|]/g, '_').slice(0, 60)
  return `${safePrefix || '408题目'}-${scope}.png`
}

const handleImageCopy = async (scope: QuestionImageCopyScope): Promise<ImageCopyResult | null> => {
  if (isCopying.value) return null

  isImageCopying.value = true
  renderScope.value = scope
  await nextTick()

  try {
    const renderer = imageRenderer.value
    if (!renderer) throw new Error('IMAGE_RENDERER_NOT_READY')

    const blobPromise = renderer.capture()
    const result = await copyImageBlob(blobPromise, getImageFilename(scope))
    if (result === 'clipboard') {
      showToast('图片已复制', 'success')
    } else {
      showToast('当前浏览器不支持图片剪贴板，已下载 PNG', 'success')
    }
    return result
  } catch (error) {
    console.error('图片复制失败:', error)
    if (error instanceof Error && error.message === 'NO_COPY_CONTENT') {
      showToast('没有可复制的内容', 'warning')
    } else {
      showToast('图片生成失败，可能包含跨域图片或内容过长', 'error')
    }
    return null
  } finally {
    renderScope.value = null
    isImageCopying.value = false
  }
}

const handleWordCopy = async (scope: QuestionRichCopyScope): Promise<RichCopyResult | null> => {
  if (isCopying.value) return null

  isWordCopying.value = true
  renderScope.value = scope
  await nextTick()

  try {
    const renderer = imageRenderer.value
    if (!renderer) throw new Error('IMAGE_RENDERER_NOT_READY')

    const contentPromise = renderer.getClipboardContent()
    const result = await copyRichContent(contentPromise)
    if (result === 'rich') {
      showToast('内容已复制，可直接粘贴到 Word', 'success')
    } else {
      showToast('当前浏览器不支持富文本剪贴板，已按纯文本复制', 'warning')
    }
    return result
  } catch (error) {
    console.error('Word 内容复制失败:', error)
    if (error instanceof Error && error.message === 'NO_COPY_CONTENT') {
      showToast('没有可复制的内容', 'warning')
    } else {
      showToast('Word 内容生成失败，请重试', 'error')
    }
    return null
  } finally {
    renderScope.value = null
    isWordCopying.value = false
  }
}

const copyWord = async (scope: QuestionRichCopyScope = 'all') => {
  const result = await handleWordCopy(scope)
  if (result) emit('word-copied', result)
  return result
}

const copyImage = async (scope: QuestionImageCopyScope = 'all') => {
  return handleImageCopy(scope)
}

defineExpose({ copyWord, copyImage })

const handleCommand = (command: string) => {
  const wordScope = getRichCopyScope(command)
  if (wordScope) {
    void handleWordCopy(wordScope)
    return
  }

  const imageScope = getImageCopyScope(command)
  if (imageScope) {
    void handleImageCopy(imageScope)
    return
  }

  emit('copy', command)
}
</script>

<style>
/* 复制菜单采用分组、固定宽度和内部滚动，避免长菜单撑出视口。 */
.dropdown-menu.question-copy-dropdown {
  min-width: 0;
  padding: 6px;
  overflow: hidden;
  border: 1px solid var(--dropdown-border);
  border-radius: var(--dropdown-panel-radius);
  background: var(--dropdown-surface);
  box-shadow: var(--dropdown-shadow);
}

.question-copy-dropdown .question-copy-menu {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  width: 760px;
  max-width: calc(100vw - 24px);
  max-height: min(440px, calc(100vh - 24px));
  max-height: min(440px, calc(100dvh - 24px));
  padding: 2px;
  overflow-y: auto;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--brand-accent) 35%, transparent) transparent;
}

.question-copy-dropdown .question-copy-menu__section {
  min-width: 0;
  padding: 10px;
  border: 1px solid #f0ece7;
  border-radius: 10px;
  background: var(--dropdown-surface);
}

.question-copy-dropdown .question-copy-menu__section + .question-copy-menu__section {
  margin: 0;
}

.question-copy-dropdown .question-copy-menu__heading {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-height: 28px;
  padding: 2px 6px 7px;
  color: #667085;
  font-size: 12px;
  font-weight: 600;
}

.question-copy-dropdown .question-copy-menu__heading-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.question-copy-dropdown .question-copy-menu__icon {
  display: inline-flex;
  flex: 0 0 24px;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: var(--dropdown-accent-soft);
  color: var(--dropdown-accent);
  font-size: 12px;
}

.question-copy-dropdown .question-copy-menu__title {
  overflow: hidden;
  color: #344054;
  font-weight: 700;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-copy-dropdown .question-copy-menu__description {
  overflow: hidden;
  color: #98a2b3;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__items {
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px;
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__items .dropdown-item {
  display: flex;
  align-items: center;
  min-width: 0;
  min-height: 34px;
  margin: 0;
  padding: 7px 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #344054;
  font-size: 13px;
  line-height: 1.35;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__items .dropdown-item:hover:not(.is-disabled) {
  border-color: var(--dropdown-border-hover);
  background: var(--dropdown-option-hover);
  color: var(--dropdown-accent);
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__items .dropdown-item:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--brand-accent) 45%, transparent);
  outline-offset: -2px;
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__items .dropdown-item.is-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.dropdown-menu.question-copy-dropdown .question-copy-menu__item--wide {
  grid-column: auto;
}

.question-copy-dropdown .question-copy-menu__item-label {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1023px) {
  .question-copy-dropdown .question-copy-menu {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 620px;
  }
}

@media (max-width: 639px) {
  .question-copy-dropdown .question-copy-menu {
    grid-template-columns: 1fr;
    width: calc(100vw - 24px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dropdown-menu.question-copy-dropdown .question-copy-menu__items .dropdown-item {
    transition: none;
  }
}
</style>
