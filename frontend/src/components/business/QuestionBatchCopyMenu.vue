<!-- 模拟题批量 Word 复制组件：复用单题渲染和剪贴板富文本能力。 -->
<template>
  <CustomButton
    type="primary"
    size="sm"
    :icon="['fas', 'file-word']"
    :loading="copying"
    :disabled="disabled || questions.length === 0"
    title="按已选顺序复制完整题目内容到 Word"
    @click="copyWord"
  >
    复制到 Word
  </CustomButton>

  <QuestionImageRenderer
    v-for="question in renderQuestions"
    :key="question.id"
    :question="question"
    scope="all"
    :ref="setRendererRef"
  />
</template>

<script setup lang="ts">
/**
 * 将多道模拟题合并为一次 Word 富文本复制。
 * 每道题继续使用 QuestionImageRenderer，确保公式、代码和图片处理规则一致。
 */
import { computed, nextTick, onBeforeUpdate, ref } from 'vue'
import type { MockQuestion } from '@/types'
import type { RichCopyContent, RichCopyResult } from '@/utils/questionCopy'
import { copyRichContent } from '@/utils/questionCopy'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionImageRenderer from '@/components/business/QuestionImageRenderer.vue'

interface Props {
  questions: MockQuestion[]
  disabled?: boolean
}

interface QuestionRendererRef {
  getClipboardContent: () => Promise<RichCopyContent>
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  'word-copied': [result: RichCopyResult, questionIds: number[]]
}>()

const { showToast } = useToast()
const copying = ref(false)
const copyingQuestions = ref<MockQuestion[]>([])
const rendererRefs = ref<QuestionRendererRef[]>([])
const renderQuestions = computed(() => copying.value ? copyingQuestions.value : [])

onBeforeUpdate(() => {
  rendererRefs.value = []
})

const setRendererRef = (instance: unknown) => {
  if (!instance || typeof instance !== 'object' || !('getClipboardContent' in instance)) return
  rendererRefs.value.push(instance as QuestionRendererRef)
}

const stripFragmentMarkers = (html: string) => {
  return html
    .replace('<!--StartFragment-->', '')
    .replace('<!--EndFragment-->', '')
}

const buildBatchContent = async (questions: MockQuestion[]): Promise<RichCopyContent> => {
  if (questions.length === 0) throw new Error('NO_COPY_CONTENT')
  if (rendererRefs.value.length !== questions.length) {
    throw new Error('IMAGE_RENDERER_NOT_READY')
  }

  const contents: RichCopyContent[] = []
  for (const renderer of rendererRefs.value) {
    contents.push(await renderer.getClipboardContent())
  }

  const separatorHtml = '<p style="height:12pt;margin:0;line-height:12pt;">&nbsp;</p>'
  return {
    html: `<!--StartFragment-->${contents
      .map(content => stripFragmentMarkers(content.html))
      .join(separatorHtml)}<!--EndFragment-->`,
    text: contents.map(content => content.text).join('\n\n'),
  }
}

const copyWord = async () => {
  if (copying.value || props.disabled || props.questions.length === 0) return

  const questionsToCopy = [...props.questions]
  copyingQuestions.value = questionsToCopy
  copying.value = true
  try {
    await nextTick()
    const result = await copyRichContent(buildBatchContent(questionsToCopy))
    if (result === 'rich') {
      showToast('已复制选中题目，可直接粘贴到 Word', 'success')
    } else {
      showToast('当前浏览器不支持富文本剪贴板，已按纯文本复制', 'warning')
    }
    emit('word-copied', result, questionsToCopy.map(question => question.id))
  } catch (error) {
    console.error('批量 Word 复制失败:', error)
    if (error instanceof Error && error.message === 'NO_COPY_CONTENT') {
      showToast('没有可复制的题目内容', 'warning')
    } else {
      showToast('批量 Word 内容生成失败，请减少题目数量后重试', 'error')
    }
  } finally {
    copying.value = false
    copyingQuestions.value = []
  }
}
</script>
