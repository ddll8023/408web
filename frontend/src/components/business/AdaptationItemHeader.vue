<!-- 改编题头部：展示标题、题型、难度、分类、来源和复制操作。 -->
<template>
  <div class="adaptation-item-header flex items-center justify-between mb-6 pb-4 border-b border-black/[0.03]">
    <div class="min-w-0 flex-1">
      <h3 class="question-title m-0 text-lg font-semibold text-gray-800">
        改编题 #{{ adaptation.id }}
      </h3>
      <div class="mt-2 flex flex-wrap gap-2">
        <Tag :type="adaptation.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ adaptation.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </Tag>
        <Tag v-if="adaptation.difficulty" :type="getDifficultyType(adaptation.difficulty)">
          {{ getDifficultyLabel(adaptation.difficulty) }}
        </Tag>
        <Tag v-if="adaptation.subjectName" type="info">
          {{ adaptation.subjectName }}
        </Tag>
        <Tag
          v-for="category in categories"
          :key="category"
          type="info"
        >
          {{ category }}
        </Tag>
      </div>
      <p v-if="adaptation.sourceSummary" class="mt-2 mb-0 text-sm leading-6 text-ink-soft">
        {{ adaptation.sourceSummary }}
      </p>
    </div>

    <div class="question-actions ml-3 flex shrink-0 gap-1 opacity-80 transition-opacity duration-200 hover:opacity-100">
      <QuestionCopyMenu :question="adaptation" @copy="(command) => $emit('copy', command)" />
      <CustomButton
        size="sm"
        type="text"
        :disabled="adaptation.sources.length === 0"
        @click="$emit('show-sources', adaptation)"
      >
        来源
      </CustomButton>
      <template v-if="isAdmin">
        <CustomButton size="sm" type="text" @click="$emit('edit', adaptation)">编辑</CustomButton>
        <CustomButton
          size="sm"
          type="text-danger"
          :loading="deleteLoading"
          @click="$emit('delete', adaptation.id)"
        >
          删除
        </CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 改编题头部组件。
 * 只处理改编题特有的元信息，复制能力复用题库公共菜单。
 */
import { computed, type PropType } from 'vue'
import type { AdaptationQuestion } from '@/types'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'
import Tag from '@/components/basic/Tag.vue'

const props = defineProps({
  adaptation: {
    type: Object as PropType<AdaptationQuestion>,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  deleteLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits<{
  copy: [command: string]
  'show-sources': [question: AdaptationQuestion]
  edit: [question: AdaptationQuestion]
  delete: [id: number]
}>()

const categories = computed(() => props.adaptation.category?.filter(Boolean) || [])
</script>

<style scoped>
@media (max-width: 767px) {
  .adaptation-item-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .question-title {
    font-size: 14px;
  }

  .question-actions {
    width: 100%;
    justify-content: flex-start;
    margin-left: 0;
  }
}
</style>
