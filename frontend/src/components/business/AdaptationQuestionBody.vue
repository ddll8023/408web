<!-- 改编题题目正文：展示题干、选项、来源标注与答案解析。 -->
<template>
  <div>
    <header class="flex flex-wrap items-center gap-2">
      <Tag :type="question.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
        {{ question.questionType === 'CHOICE' ? '选择题' : '主观题' }}
      </Tag>
      <span class="font-medium text-ink">{{ question.title || '（未命名）' }}</span>
      <Tag v-if="question.sourceSummary" type="info" size="sm">{{ question.sourceSummary }}</Tag>
      <Tag v-else type="warning" size="sm">未标注来源</Tag>
      <span v-if="unresolvedCount > 0" class="text-xs text-amber-600">
        含 {{ unresolvedCount }} 处未解析来源
      </span>
    </header>

    <div class="mt-3">
      <MarkdownViewer :content="question.content" content-role="body" />
    </div>

    <ul v-if="question.questionType === 'CHOICE' && question.options" class="mt-3 space-y-1.5">
      <li v-for="key in optionKeys" :key="key" class="flex gap-2 text-sm">
        <span class="shrink-0 font-semibold text-accent">{{ key }}.</span>
        <MarkdownViewer
          :content="question.options[key]"
          variant="plain"
          content-role="option"
        />
      </li>
    </ul>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <CustomButton size="sm" type="default" @click="expanded = !expanded">
        {{ expanded ? '收起解析' : '查看解析' }}
      </CustomButton>
      <span v-if="question.category?.length" class="flex flex-wrap gap-1">
        <Tag v-for="cat in question.category" :key="cat" type="info" size="sm">{{ cat }}</Tag>
      </span>
    </div>

    <div v-if="expanded" class="mt-3 rounded-lg bg-surface p-3">
      <MarkdownViewer v-if="question.answer" :content="question.answer" content-role="body" />
      <p v-else class="text-sm text-ink-soft">该题暂未提供答案解析</p>

      <div v-if="question.sources.length > 0" class="mt-3 border-t border-gray-100 pt-3">
        <p class="text-xs text-ink-soft">来源明细：</p>
        <ul class="mt-1 space-y-1">
          <li
            v-for="source in question.sources"
            :key="`${source.sourceYear}-${source.sourceQuestionNumber}`"
            class="text-xs"
            :class="source.sourceExists ? 'text-ink-soft' : 'text-amber-600'"
          >
            {{ source.sourceYear }} 年第 {{ source.sourceQuestionNumber }} 题
            <span v-if="source.examTitle"> —— {{ source.examTitle }}</span>
            <span v-else>（真题库未找到该题）</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdaptationQuestionBody 改编题正文组件
 * 功能：展示改编题题干、选项、来源标注与可展开的答案解析
 */
import type { AdaptationQuestion } from '@/types'
import type { PropType } from 'vue'
import { computed, ref, watch } from 'vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'
import Tag from '@/components/basic/Tag.vue'

const props = defineProps({
  question: {
    type: Object as PropType<AdaptationQuestion>,
    required: true
  },
  defaultExpanded: {
    type: Boolean,
    default: false
  }
})

const optionKeys = ['A', 'B', 'C', 'D'] as const
const expanded = ref(props.defaultExpanded)

watch(() => props.question.id, () => {
  expanded.value = props.defaultExpanded
})

const unresolvedCount = computed(
  () => (props.question.sources || []).filter(source => !source.sourceExists).length
)
</script>
