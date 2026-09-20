<!-- 改编来源编辑区：按行维护「年份 + 题号 + 小问」并即时解析真题命中情况。 -->
<template>
  <div class="space-y-3">
    <div
      v-for="(row, index) in rows"
      :key="row.key"
      class="rounded-lg border border-gray-200 bg-white/60 p-3"
    >
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-12">
        <div class="sm:col-span-3">
          <FormLabel :label="`来源年份 ${index + 1}`" :for-id="`source-year-${row.key}`" />
          <WheelPicker
            :id="`source-year-${row.key}`"
            :model-value="row.sourceYear"
            :options="yearOptions"
            placeholder="选择年份"
            aria-label="来源年份"
            clearable
            :disabled="disabled"
            class="w-full"
            @update:model-value="handleYearChange(index, $event)"
          />
        </div>
        <div class="sm:col-span-3">
          <FormLabel label="来源题号" :for-id="`source-number-${row.key}`" />
          <InputNumber
            :id="`source-number-${row.key}`"
            :model-value="row.sourceQuestionNumber ?? 0"
            :min="1"
            :max="1000"
            placeholder="题号"
            :disabled="disabled"
            @update:model-value="handleNumberChange(index, $event)"
          />
        </div>
        <div class="sm:col-span-4">
          <FormLabel label="小问或备注" hint="可选" :for-id="`source-part-${row.key}`" />
          <CustomInput
            :id="`source-part-${row.key}`"
            :model-value="row.sourcePart"
            placeholder="如 41(2)，整题留空"
            :maxlength="50"
            :disabled="disabled"
            @update:model-value="handlePartChange(index, $event)"
          />
        </div>
        <div class="flex items-end sm:col-span-2">
          <CustomButton
            type="text-danger"
            size="sm"
            :disabled="disabled || rows.length <= 1"
            @click="removeRow(index)"
          >
            <font-awesome-icon :icon="['fas', 'trash']" class="mr-1" />
            删除
          </CustomButton>
        </div>
      </div>
      <p class="mt-2 flex items-center gap-1 text-xs" :class="rowStatusClass(index)">
        <font-awesome-icon :icon="rowStatusIcon(index)" />
        {{ rowStatusText(index) }}
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <CustomButton
        size="sm"
        :disabled="disabled || rows.length >= MAX_SOURCE_REFS"
        @click="addRow"
      >
        <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
        添加来源
      </CustomButton>
      <span class="text-xs text-ink-soft">
        暂未确定来源可以先保存，之后再补录；同一改编题可引用多道真题。
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdaptationSourceEditor 改编来源编辑区
 * 功能：受控维护来源引用行，并为每行给出真题库命中提示
 * 依赖：WheelPicker、InputNumber、CustomInput、CustomButton、FormLabel 基础组件
 */
import type { AdaptationSourceLookupItem, AdaptationSourceRefInput } from '@/types'
import type { PropType } from 'vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { lookupAdaptationSources } from '@/api/adaptation'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import InputNumber from '@/components/basic/InputNumber.vue'
import WheelPicker from '@/components/basic/WheelPicker.vue'

interface SourceRow {
  key: number
  sourceYear: number | null
  sourceQuestionNumber: number | null
  sourcePart: string
}

/** 与后端 MAX_SOURCE_REFS 保持一致，避免提交被直接拒绝 */
const MAX_SOURCE_REFS = 20
const FIRST_EXAM_YEAR = 2009
const LOOKUP_DEBOUNCE_MS = 400

const props = defineProps({
  modelValue: {
    type: Array as PropType<AdaptationSourceRefInput[]>,
    default: () => []
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{ 'update:modelValue': [sources: AdaptationSourceRefInput[]] }>()

let rowKeySeed = 0
const rows = ref<SourceRow[]>([])
/** 记录最近一次由本组件发出的来源集合，避免父组件回写时覆盖正在输入的空行 */
let lastEmitted = ''
let lookupTimer: ReturnType<typeof setTimeout> | null = null
let lookupRequestVersion = 0
const lookupResults = ref<AdaptationSourceLookupItem[]>([])

const yearOptions = computed(() => {
  const lastYear = Math.max(new Date().getFullYear(), FIRST_EXAM_YEAR)
  const options: { label: string; value: number }[] = []
  for (let year = lastYear; year >= FIRST_EXAM_YEAR; year--) {
    options.push({ label: `${year} 年`, value: year })
  }
  return options
})

/** 把父组件传入的来源引用转换为编辑行 */
const createRow = (source?: AdaptationSourceRefInput): SourceRow => ({
  key: ++rowKeySeed,
  sourceYear: source?.sourceYear ?? null,
  sourceQuestionNumber: source?.sourceQuestionNumber ?? null,
  sourcePart: source?.sourcePart ?? ''
})

/** 仅保留年份与题号都完整的行，作为提交与解析的正式数据 */
const toSourceRefs = (): AdaptationSourceRefInput[] =>
  rows.value
    .filter(row => row.sourceYear !== null && row.sourceQuestionNumber !== null)
    .map(row => ({
      sourceYear: row.sourceYear as number,
      sourceQuestionNumber: row.sourceQuestionNumber as number,
      sourcePart: row.sourcePart.trim() || null
    }))

const emitSources = () => {
  const sources = toSourceRefs()
  lastEmitted = JSON.stringify(sources)
  emit('update:modelValue', sources)
  scheduleLookup()
}

const syncFromModelValue = (value: AdaptationSourceRefInput[]) => {
  if (JSON.stringify(value) === lastEmitted) return
  const sources = Array.isArray(value) ? value : []
  rows.value = sources.length > 0 ? sources.map(createRow) : [createRow()]
  lastEmitted = JSON.stringify(toSourceRefs())
  scheduleLookup()
}

const addRow = () => {
  if (rows.value.length >= MAX_SOURCE_REFS) return
  rows.value.push(createRow())
}

const removeRow = (index: number) => {
  rows.value.splice(index, 1)
  if (rows.value.length === 0) {
    rows.value.push(createRow())
  }
  emitSources()
}

const handleYearChange = (index: number, value: number | string | null) => {
  const row = rows.value[index]
  if (!row) return
  row.sourceYear = typeof value === 'number' ? value : null
  emitSources()
}

const handleNumberChange = (index: number, value: number | null) => {
  const row = rows.value[index]
  if (!row) return
  row.sourceQuestionNumber = typeof value === 'number' && value > 0 ? value : null
  emitSources()
}

const handlePartChange = (index: number, value: string) => {
  const row = rows.value[index]
  if (!row) return
  row.sourcePart = value
  emitSources()
}

/** 去抖后批量解析来源，避免逐行输入触发多次请求 */
const scheduleLookup = () => {
  if (lookupTimer) clearTimeout(lookupTimer)
  const requestVersion = ++lookupRequestVersion
  const pending = toSourceRefs()
  if (pending.length === 0) {
    lookupResults.value = []
    return
  }
  lookupTimer = setTimeout(() => {
    void runLookup(pending, requestVersion)
  }, LOOKUP_DEBOUNCE_MS)
}

const runLookup = async (
  pending: AdaptationSourceRefInput[],
  requestVersion: number,
) => {
  try {
    const response = await lookupAdaptationSources(pending)
    if (requestVersion !== lookupRequestVersion) return
    if (response.code === 200) {
      lookupResults.value = response.data || []
    }
  } catch (error) {
    if (requestVersion !== lookupRequestVersion) return
    lookupResults.value = []
    console.error('解析改编来源失败:', error)
  }
}

onBeforeUnmount(() => {
  if (lookupTimer) clearTimeout(lookupTimer)
})

watch(() => props.modelValue, syncFromModelValue, { immediate: true, deep: true })

/** 计算行在解析结果中的序号：只有完整行才参与解析请求 */
const rowResultIndex = (index: number) => {
  let cursor = 0
  for (let i = 0; i < index; i++) {
    const row = rows.value[i]
    if (row?.sourceYear !== null && row?.sourceQuestionNumber !== null) cursor++
  }
  return cursor
}

const rowStatusText = (index: number) => {
  const row = rows.value[index]
  if (!row) return ''
  if (row.sourceYear === null || row.sourceQuestionNumber === null) {
    return '请填写年份与题号'
  }
  const result = lookupResults.value[rowResultIndex(index)]
  if (!result) return '正在核对真题库…'
  return result.exists
    ? `命中真题：${result.examTitle || '（未命名题目）'}`
    : '真题库中未找到该题号，保存后标记为未解析，请核对年份与题号'
}

const rowStatusClass = (index: number) => {
  const row = rows.value[index]
  if (!row || row.sourceYear === null || row.sourceQuestionNumber === null) {
    return 'text-ink-soft'
  }
  const result = lookupResults.value[rowResultIndex(index)]
  if (!result) return 'text-ink-soft'
  return result.exists ? 'text-emerald-600' : 'text-amber-600'
}

const rowStatusIcon = (index: number) => {
  const row = rows.value[index]
  if (!row || row.sourceYear === null || row.sourceQuestionNumber === null) {
    return ['fas', 'circle-info']
  }
  const result = lookupResults.value[rowResultIndex(index)]
  if (!result) return ['fas', 'spinner']
  return result.exists ? ['fas', 'circle-check'] : ['fas', 'triangle-exclamation']
}
</script>
