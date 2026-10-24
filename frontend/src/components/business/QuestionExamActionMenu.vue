<!-- 出题操作菜单：复用复制菜单的分组面板，提供 Markdown、Word、图片复制与出题状态切换。 -->
<template>
  <QuestionCopyMenu
    :question="question"
    :disabled="statusLoading"
    menu-aria-label="出题操作"
    @copy="handleCopy"
    @word-copied="handleWordCopied"
  >
    <template #trigger="{ busy }">
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', 'ellipsis']"
        :loading="busy"
        :disabled="statusLoading"
        title="出题操作"
      >
        {{ busy ? '生成中' : '出题' }}
      </CustomButton>
    </template>

    <template #extra="{ busy }">
      <section class="question-copy-menu__section" aria-label="出题状态" role="group">
        <div class="question-copy-menu__heading">
          <span class="question-copy-menu__icon" aria-hidden="true">
            <font-awesome-icon :icon="['fas', 'rotate']" />
          </span>
          <span class="question-copy-menu__heading-copy">
            <span class="question-copy-menu__title">出题状态</span>
            <span class="question-copy-menu__description">标记本题是否已出题</span>
          </span>
        </div>

        <div class="question-copy-menu__items">
          <DropdownItem command="toggle-status" :disabled="busy || statusLoading">
            <font-awesome-icon :icon="['fas', 'rotate']" aria-hidden="true" />
            <span class="question-copy-menu__item-label">切换出题状态</span>
            <span class="question-exam-action-menu__current">
              当前：{{ question.isExamMarked ? '已出题' : '未出题' }}
            </span>
          </DropdownItem>
        </div>
      </section>
    </template>
  </QuestionCopyMenu>
</template>

<script setup lang="ts">
/**
 * 出题操作菜单。
 * 复制分组完全复用复制菜单，本组件只补充 Markdown 标题行与出题状态分组；
 * 具体标记接口和提示由宿主页面处理。
 */
import { computed } from 'vue'
import type { AdaptationQuestion, MockQuestion } from '@/types'
import type { QuestionRichCopyScope, RichCopyResult } from '@/utils/questionCopy'
import { buildMockTitleLine, copyFullMarkdown, resolveFullMarkdownLevel } from '@/utils/questionMarkdown'
import CustomButton from '@/components/basic/CustomButton.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'

/** 菜单题目类型：模拟题与改编题共用同一套复制与出题状态入口。 */
type ExamActionQuestion = (MockQuestion | AdaptationQuestion) & { examStatusLoading?: boolean }

interface Props {
  question: ExamActionQuestion
  statusLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  statusLoading: false,
})

const emit = defineEmits<{
  'content-copied': []
  'toggle-exam-status': []
}>()

/** Markdown 标题行：模拟题取标题与题号，改编题按编号，与改编题阅读页保持一致。 */
const markdownTitleLine = computed(() =>
  'source' in props.question
    ? buildMockTitleLine(props.question)
    : `改编题 #${props.question.id}`,
)

/** 只有完整内容复制才通知宿主标记出题，题目、选项、答案等局部复制不触发。 */
const handleWordCopied = (_result: RichCopyResult, scope: QuestionRichCopyScope) => {
  if (scope !== 'all') return
  emit('content-copied')
}

const handleCopy = async (command: string) => {
  if (command === 'toggle-status') {
    emit('toggle-exam-status')
    return
  }

  if (resolveFullMarkdownLevel(command) === null) return
  const copied = await copyFullMarkdown(command, props.question, markdownTitleLine.value)
  if (copied) emit('content-copied')
}
</script>

<style scoped>
.question-exam-action-menu__current {
  margin-left: auto;
  padding-left: 12px;
  color: #98a2b3;
  font-size: 12px;
}

:deep(.question-copy-menu__items .dropdown-item) {
  gap: 8px;
}
</style>
