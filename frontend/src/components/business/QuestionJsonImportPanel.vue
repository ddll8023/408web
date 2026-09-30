<!-- 题目 JSON 导入面板：统一真题、模拟题和改编题编辑弹窗的导入交互。 -->
<template>
  <section class="edit-import">
    <button
      class="edit-import-toggle"
      type="button"
      :aria-expanded="visible"
      :aria-controls="panelId"
      @click="emit('update:visible', !visible)"
    >
      <span class="flex flex-wrap items-center gap-x-2 gap-y-1">
        <font-awesome-icon :icon="['fas', 'code']" class="text-accent" aria-hidden="true" />
        <span class="text-sm font-medium">从 JSON 导入</span>
        <span class="text-xs text-ink-soft">辅助录入</span>
      </span>
      <font-awesome-icon
        class="shrink-0 text-ink-soft"
        :icon="visible ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']"
        aria-hidden="true"
      />
    </button>

    <Transition name="slide-fade">
      <div v-show="visible" :id="panelId" class="edit-import-body">
        <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <label :for="`${panelId}-input`" class="edit-label m-0">题目 JSON</label>
          <button v-if="showExample" type="button" class="text-xs text-accent underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-accent" @click="emit('show-example')">查看格式示例</button>
        </div>
        <textarea
          :id="`${panelId}-input`"
          :aria-describedby="`${panelId}-hint`"
          :value="modelValue"
          class="edit-textarea edit-json-input"
          spellcheck="false"
          rows="5"
          placeholder="粘贴JSON数据..."
          @input="handleInput"
        />

        <p :id="`${panelId}-hint`" class="edit-hint">粘贴单个题目的 JSON，解析后填充下方表单。<span v-if="showContentOnly">“仅更新题目内容”不会修改基础信息。</span></p>
        <div class="mt-3 flex flex-wrap gap-2">
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
import '@/styles/edit-form.css'

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
