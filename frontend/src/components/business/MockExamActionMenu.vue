<template>
  <Dropdown
    trigger="click"
    :disabled="isBusy"
    menu-class="mock-exam-action-dropdown"
    @command="handleCommand"
  >
    <template #trigger>
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', 'file-word']"
        :loading="isBusy"
        title="出题操作"
      >
        出题
      </CustomButton>
    </template>

    <template #dropdown>
      <div class="mock-exam-action-menu" aria-label="出题操作">
        <DropdownItem command="copy-word" :disabled="isBusy">
          <font-awesome-icon :icon="['fas', 'file-word']" aria-hidden="true" />
          <span>复制到 Word</span>
        </DropdownItem>
        <DropdownItem command="copy-image" :disabled="isBusy">
          <font-awesome-icon :icon="['fas', 'file']" aria-hidden="true" />
          <span>导出题目图片</span>
        </DropdownItem>
        <DropdownItem command="toggle-status" :disabled="isBusy" divided>
          <font-awesome-icon :icon="['fas', 'rotate']" aria-hidden="true" />
          <span>切换出题状态</span>
          <span class="mock-exam-action-menu__current">
            当前：{{ question.isExamMarked ? '已出题' : '未出题' }}
          </span>
        </DropdownItem>
      </div>
    </template>
  </Dropdown>

  <!-- 复用现有 Word/题目图片导出实现，仅隐藏触发器。 -->
  <QuestionCopyMenu
    ref="copyMenu"
    :question="question"
    headless
    @word-copied="handleWordCopied"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MockQuestion } from '@/types'
import type {
  ImageCopyResult,
  QuestionImageCopyScope,
  QuestionRichCopyScope,
  RichCopyResult,
} from '@/utils/questionCopy'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'

interface Props {
  question: MockQuestion
  statusLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  statusLoading: false,
})

const emit = defineEmits<{
  'word-copied': [result: RichCopyResult]
  'toggle-exam-status': []
}>()

interface QuestionCopyMenuRef {
  copyWord: (scope?: QuestionRichCopyScope) => Promise<RichCopyResult | null>
  copyImage: (scope?: QuestionImageCopyScope) => Promise<ImageCopyResult | null>
}

const copyMenu = ref<QuestionCopyMenuRef | null>(null)
const isWordCopying = ref(false)
const isImageCopying = ref(false)
const isBusy = computed(() => isWordCopying.value || isImageCopying.value || props.statusLoading)

const handleWordCopied = (result: RichCopyResult) => {
  emit('word-copied', result)
}

const copyWord = async () => {
  if (isBusy.value) return

  const menu = copyMenu.value
  if (!menu) return

  isWordCopying.value = true
  try {
    await menu.copyWord('all')
  } finally {
    isWordCopying.value = false
  }
}

const copyImage = async () => {
  if (isBusy.value) return

  const menu = copyMenu.value
  if (!menu) return

  isImageCopying.value = true
  try {
    await menu.copyImage('question-options')
  } finally {
    isImageCopying.value = false
  }
}

const handleCommand = (command: string) => {
  if (command === 'copy-word') {
    void copyWord()
    return
  }

  if (command === 'copy-image') {
    void copyImage()
    return
  }

  if (command === 'toggle-status') {
    emit('toggle-exam-status')
  }
}
</script>

<style scoped>
.mock-exam-action-menu {
  min-width: 180px;
  padding: 4px;
}

.mock-exam-action-menu__current {
  margin-left: auto;
  color: #98a2b3;
  font-size: 12px;
}

.mock-exam-action-menu :deep(.dropdown-item) {
  gap: 8px;
}
</style>
