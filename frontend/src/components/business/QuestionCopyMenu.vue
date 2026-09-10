<template>
  <!-- 复制下拉菜单 -->
  <Dropdown trigger="click" :disabled="isImageCopying" @command="handleCommand">
    <template #trigger>
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', 'copy']"
        :loading="isImageCopying"
      >
        {{ isImageCopying ? '生成中' : '复制' }}
      </CustomButton>
    </template>

    <template #dropdown>
      <!-- Markdown 格式 -->
      <DropdownItem disabled>
        <font-awesome-icon :icon="['fas', 'file-lines']" class="mr-1" />
        Markdown 格式
      </DropdownItem>
      <DropdownItem command="md-question">复制题目 (MD)</DropdownItem>
      <DropdownItem
        v-if="question.questionType === 'CHOICE' && question.options"
        command="md-options"
      >复制选项 (MD)</DropdownItem>
      <DropdownItem v-if="question.answer" command="md-answer">复制答案 (MD)</DropdownItem>
      <DropdownItem
        v-if="question.answer || (question.questionType === 'CHOICE' && question.options)"
        command="md-all"
      >复制完整内容 (MD)</DropdownItem>

      <!-- 纯文本格式 -->
      <DropdownItem disabled divided>
        <font-awesome-icon :icon="['fas', 'ticket']" class="mr-1" />
        纯文本格式
      </DropdownItem>
      <DropdownItem command="text-question">复制题目 (Text)</DropdownItem>
      <DropdownItem
        v-if="question.questionType === 'CHOICE' && question.options"
        command="text-options"
      >复制选项 (Text)</DropdownItem>
      <DropdownItem v-if="question.answer" command="text-answer">复制答案 (Text)</DropdownItem>
      <DropdownItem
        v-if="question.answer || (question.questionType === 'CHOICE' && question.options)"
        command="text-all"
      >复制完整内容 (Text)</DropdownItem>

      <!-- 图片格式 -->
      <DropdownItem disabled divided>
        <font-awesome-icon :icon="['fas', 'file']" class="mr-1" />
        图片格式
      </DropdownItem>
      <DropdownItem command="image-question-options" :disabled="isImageCopying">
        复制题目+选项 (图片)
      </DropdownItem>
      <DropdownItem v-if="question.answer" command="image-answer" :disabled="isImageCopying">
        复制答案 (图片)
      </DropdownItem>
      <DropdownItem
        v-if="question.answer || (question.questionType === 'CHOICE' && question.options)"
        command="image-all"
        :disabled="isImageCopying"
      >复制全部 (图片)</DropdownItem>
    </template>
  </Dropdown>

  <QuestionImageRenderer
    v-if="imageCopyScope"
    ref="imageRenderer"
    :question="question"
    :scope="imageCopyScope ?? 'all'"
  />
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import { nextTick, ref } from 'vue'
import type { ExamQuestion, MockQuestion } from '@/types'
import { copyImageBlob, getImageCopyScope, type QuestionImageCopyScope } from '@/utils/questionCopy'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import QuestionImageRenderer from '@/components/business/QuestionImageRenderer.vue'

/** 题目复制菜单，统一提供 Markdown、纯文本和图片复制入口。 */
const props = defineProps({
  question: {
    type: Object as PropType<ExamQuestion | MockQuestion>,
    required: true
  }
})

const emit = defineEmits<{ copy: [command: string] }>()
const { showToast } = useToast()

interface ImageRendererRef {
  capture: () => Promise<Blob>
}

const imageCopyScope = ref<QuestionImageCopyScope | null>(null)
const imageRenderer = ref<ImageRendererRef | null>(null)
const isImageCopying = ref(false)

const getImageFilename = (scope: QuestionImageCopyScope) => {
  const question = props.question
  const prefix = 'source' in question
    ? question.title || question.source || '模拟题'
    : `${question.year}年真题`
  const safePrefix = prefix.replace(/[\\/:*?"<>|]/g, '_').slice(0, 60)
  return `${safePrefix || '408题目'}-${scope}.png`
}

const handleImageCopy = async (scope: QuestionImageCopyScope) => {
  if (isImageCopying.value) return

  isImageCopying.value = true
  imageCopyScope.value = scope
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
  } catch (error) {
    console.error('图片复制失败:', error)
    if (error instanceof Error && error.message === 'NO_COPY_CONTENT') {
      showToast('没有可复制的内容', 'warning')
    } else {
      showToast('图片生成失败，可能包含跨域图片或内容过长', 'error')
    }
  } finally {
    imageCopyScope.value = null
    isImageCopying.value = false
  }
}

const handleCommand = (command: string) => {
  const scope = getImageCopyScope(command)
  if (scope) {
    void handleImageCopy(scope)
    return
  }

  emit('copy', command)
}
</script>
