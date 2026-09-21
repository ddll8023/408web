<!-- 题目 JSON 导入面板：统一真题、模拟题和改编题编辑弹窗的导入交互。 -->
<template>
  <section class="mb-6">
    <button
      class="group flex w-full items-center justify-between rounded-r-lg border-l-4 border-accent bg-gradient-to-r from-surface/80 to-transparent px-5 py-3.5 transition-all duration-200 hover:from-surface hover:shadow-sm"
      type="button"
      :aria-expanded="visible"
      :aria-controls="panelId"
      @click="emit('update:visible', !visible)"
    >
      <span class="flex items-center gap-3">
        <font-awesome-icon :icon="['fas', 'code']" class="text-accent" aria-hidden="true" />
        <span class="font-semibold text-ink">从 JSON 格式导入</span>
        <span class="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent/60">批量录入</span>
      </span>
      <font-awesome-icon
        class="text-accent/60 transition-transform duration-300 group-hover:text-accent"
        :icon="visible ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']"
        aria-hidden="true"
      />
    </button>

    <Transition name="slide-fade">
      <div v-show="visible" :id="panelId" class="mt-3 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-start gap-3 rounded-lg border border-accent/10 bg-surface p-4">
          <font-awesome-icon :icon="['fas', 'info-circle']" class="mt-0.5 text-accent" aria-hidden="true" />
          <div class="text-sm text-ink-soft">
            粘贴单个题目的 JSON 数据，点击“解析并填充”后自动填充到下方表单。
            <a
              v-if="showExample"
              href="#"
              class="ml-2 text-accent underline underline-offset-2 hover:text-accent-hover"
              @click.prevent="emit('show-example')"
            >
              查看格式示例
            </a>
          </div>
        </div>

        <textarea
          :value="modelValue"
          class="w-full rounded-lg border border-gray-200 bg-gray-50/50 px-4 py-3 font-mono text-sm transition-all duration-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
          rows="5"
          placeholder="粘贴JSON数据..."
          @input="handleInput"
        />

        <div class="mt-4 flex flex-wrap gap-3">
          <CustomButton size="sm" @click="emit('paste')">
            <font-awesome-icon :icon="['fas', 'clipboard']" class="mr-1.5" aria-hidden="true" />
            粘贴
          </CustomButton>
          <CustomButton type="primary" size="sm" @click="emit('parse')">
            <font-awesome-icon :icon="['fas', 'check']" class="mr-1.5" aria-hidden="true" />
            解析并填充
          </CustomButton>
          <CustomButton
            v-if="showContentOnly"
            size="sm"
            title="仅更新题干、选项和答案解析，不修改基础信息"
            @click="emit('parse-content')"
          >
            <font-awesome-icon :icon="['fas', 'edit']" class="mr-1.5" aria-hidden="true" />
            仅更新题目内容
          </CustomButton>
          <CustomButton size="sm" @click="emit('clear')">
            <font-awesome-icon :icon="['fas', 'trash']" class="mr-1.5" aria-hidden="true" />
            清空
          </CustomButton>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
/**
 * 题目 JSON 导入面板。
 * 组件只负责公共展示和事件转发，JSON 解析及字段填充仍由业务弹窗处理。
 */
import { getCurrentInstance } from 'vue'
import CustomButton from '@/components/basic/CustomButton.vue'

interface Props {
  modelValue: string
  visible: boolean
  showContentOnly?: boolean
  showExample?: boolean
}

withDefaults(defineProps<Props>(), {
  showContentOnly: false,
  showExample: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:visible': [value: boolean]
  paste: []
  parse: []
  'parse-content': []
  clear: []
  'show-example': []
}>()

const panelId = `question-json-import-${getCurrentInstance()?.uid ?? Math.random().toString(36).slice(2)}`

const handleInput = (event: Event) => {
  if (event.target instanceof HTMLTextAreaElement) {
    emit('update:modelValue', event.target.value)
  }
}

</script>
