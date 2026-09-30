<!-- 改编题头部：展示标题、题型、难度、分类、来源和复制操作。 -->
<template>
  <div class="adaptation-item-header flex items-start justify-between gap-4 mb-3 pb-3 border-b border-gray-100">
    <div class="min-w-0 flex-1">
      <h3 class="question-title m-0 font-semibold">
        {{ adaptation.sourceSummary || '改编题（未标注来源）' }}
      </h3>
      <div class="question-metadata mt-2 flex flex-wrap gap-1.5">
        <Tag class="question-tag" size="sm" :type="adaptation.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ adaptation.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </Tag>
        <Tag v-if="adaptation.difficulty" class="question-tag" size="sm" :type="getDifficultyType(adaptation.difficulty)">
          {{ getDifficultyLabel(adaptation.difficulty) }}
        </Tag>
        <Tag v-if="adaptation.subjectName" class="question-tag" size="sm" type="info">
          {{ adaptation.subjectName }}
        </Tag>
        <Tag
          v-for="category in categories"
          :key="category"
          class="question-tag"
          size="sm"
          type="info"
        >
          {{ category }}
        </Tag>
      </div>
    </div>

    <div class="question-actions flex shrink-0 flex-wrap items-center gap-1">
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', fullscreenActive ? 'compress' : 'expand']"
        :title="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        :aria-label="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        @click="$emit('toggle-fullscreen')"
      />
      <template v-if="!fullscreenActive">
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
  },
  /** 当前卡片是否处于全屏或沉浸模式 */
  fullscreenActive: {
    type: Boolean,
    default: false
  }
})

defineEmits<{
  copy: [command: string]
  'show-sources': [question: AdaptationQuestion]
  edit: [question: AdaptationQuestion]
  delete: [id: number]
  'toggle-fullscreen': []
}>()

const categories = computed(() => props.adaptation.category?.filter(Boolean) || [])
</script>

<style scoped>
.question-title {
  font-size: 18px;
  line-height: 1.5;
  /* 标题取品牌棕色，与分类标题和卡片色条共同区分三个题库。 */
  color: var(--brand-accent);
  overflow-wrap: anywhere;
}

/* 元信息使用中性底色，让改编来源和题干成为阅读重点。 */
.question-metadata :deep(.question-tag) {
  color: var(--brand-ink-soft);
  background-color: #f4f5f6;
}

.question-actions {
  max-width: 100%;
}

@media (max-width: 767px) {
  .adaptation-item-header {
    flex-direction: column;
    gap: 12px;
  }

  .question-title {
    font-size: 16px;
  }

  .question-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
