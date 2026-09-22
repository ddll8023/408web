<!-- 改编题来源弹窗：展示关联真题，并支持新标签页定位到原真题。 -->
<template>
  <ResponsiveDialog
    v-model:visible="dialogVisible"
    :title="dialogTitle"
    width="680px"
    max-width="calc(100vw - 24px)"
  >
    <Empty v-if="sources.length === 0" description="当前改编题暂无来源" />

    <div v-else class="flex flex-col gap-3">
      <article
        v-for="source in sources"
        :key="source.id ?? `${source.sourceYear}-${source.sourceQuestionNumber}`"
        class="rounded-lg border border-gray-200 bg-white p-4"
      >
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex min-w-0 items-center gap-2">
            <span class="font-medium text-ink">
              {{ source.sourceYear }} 年第 {{ source.sourceQuestionNumber }} 题
            </span>
            <Tag :type="source.sourceExists ? 'success' : 'warning'" size="sm">
              {{ source.sourceExists ? '已解析' : '未解析' }}
            </Tag>
          </div>

          <a
            v-if="getExamHref(source)"
            :href="getExamHref(source)"
            target="_blank"
            rel="noopener noreferrer"
            class="rounded-md px-2.5 py-1.5 text-sm font-medium text-accent transition-colors hover:bg-accent/10 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1"
          >
            查看真题
          </a>
        </div>

        <p v-if="source.examTitle" class="mt-2 mb-0 line-clamp-2 text-sm leading-6 text-ink-soft">
          {{ source.examTitle }}
        </p>
        <p v-else-if="!source.sourceExists" class="mt-2 mb-0 text-sm text-amber-700">
          真题库中暂未找到该年份和题号，来源事实仍已保留。
        </p>
      </article>
    </div>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
/**
 * 改编题来源弹窗。
 * 来源跳转复用真题年份页的题目 hash 定位，打开新标签页不影响当前改编题页面。
 */
import { computed, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import type { AdaptationQuestion, AdaptationSourceRef } from '@/types'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import Empty from '@/components/basic/Empty.vue'
import Tag from '@/components/basic/Tag.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  adaptation: {
    type: Object as PropType<AdaptationQuestion | null>,
    default: null
  }
})

const emit = defineEmits<{ 'update:visible': [visible: boolean] }>()
const router = useRouter()

const dialogVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
})

const sources = computed<AdaptationSourceRef[]>(() => props.adaptation?.sources || [])
const dialogTitle = computed(() => {
  const title = props.adaptation ? `改编题 #${props.adaptation.id}` : '改编题'
  return `${title} · 改编来源`
})

const getExamHref = (source: AdaptationSourceRef) => {
  if (!source.sourceExists || source.examQuestionId == null) return ''
  return router.resolve({
    path: `/exam/${source.sourceYear}`,
    hash: `#question-${source.examQuestionId}`
  }).href
}
</script>
