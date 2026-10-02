<!-- 模型选择器：搜索分页与能力展示，不自动选择型号或调用模型。 -->
<template>
  <section aria-labelledby="ai-model-picker-title" :aria-busy="busy" class="space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 id="ai-model-picker-title" class="font-medium text-ink">模型目录</h3>
    </div>
    <p class="text-xs text-ink-soft">{{ page?.source === 'bundled' ? '随应用发布的目录' : '模型目录' }} · 目录收录不代表你的账号有调用权限，也不代表真实检测已经通过。</p>
    <div class="flex items-end gap-2">
      <CustomInput id="ai-model-search" v-model="search" label="搜索模型" placeholder="模型名称或实际 ID" :maxlength="200" :disabled="disabled || busy" class="flex-1" @keyup.enter="load(0)" />
      <CustomButton :disabled="disabled || busy" @click="load(0)">搜索</CustomButton>
    </div>
    <Alert v-if="errorMessage" type="error">{{ errorMessage }}<CustomButton size="sm" class="mt-2" :disabled="disabled || busy" @click="load(page?.offset ?? 0)">重新加载</CustomButton></Alert>
    <p v-if="busy" role="status" class="text-sm text-ink-soft">正在读取模型目录…</p>
    <div v-if="page?.models.length" class="max-h-[360px] space-y-2 overflow-y-auto pr-1">
      <button v-for="model in page.models" :key="`${model.provider}/${model.id}`" type="button" :disabled="disabled || busy"
        :aria-pressed="modelValue === model.id" class="w-full rounded-md border p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50"
        :class="modelValue === model.id ? 'border-accent bg-accent/10' : 'border-line bg-white hover:bg-surface'" @click="emit('select', model)">
        <span class="block font-medium text-ink">{{ model.name }}</span>
        <span class="mt-1 block break-all font-mono text-xs text-ink-soft">{{ model.id }}</span>
        <span class="mt-2 flex flex-wrap gap-2 text-xs text-ink-soft">
          <span>文本{{ model.supportsImages ? ' · 图像' : '' }}</span>
          <span v-if="model.reasoning">推理</span>
          <span v-if="model.contextWindow">上下文 {{ model.contextWindow.toLocaleString() }}</span>
        </span>
      </button>
    </div>
    <p v-else-if="page && !busy" class="rounded-md border border-line bg-surface p-4 text-sm text-ink-soft">{{ search ? '没有匹配的模型，请调整搜索词。' : '当前目录没有可用的文本型号。' }}</p>
    <div v-if="page" class="flex flex-wrap items-center justify-between gap-2 text-sm text-ink-soft">
      <span>共 {{ page.total }} 个型号</span>
      <div class="flex gap-2">
        <CustomButton size="sm" :disabled="disabled || busy || page.offset === 0" @click="load(Math.max(0, page.offset - page.limit))">上一页</CustomButton>
        <CustomButton size="sm" :disabled="disabled || busy || page.offset + page.limit >= page.total" @click="load(page.offset + page.limit)">下一页</CustomButton>
      </div>
    </div>
    <p class="text-xs text-ink-soft">模型支持图像不代表本站已完成图片咨询链路。未收录型号不会按猜测的协议接入。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { AiSettingsError, queryAiModels, type AiCatalogModelView, type AiModelsView } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ providerId: string; modelValue: string; disabled?: boolean }>()
const emit = defineEmits<{ select: [model: AiCatalogModelView]; busyChange: [busy: boolean] }>()
const authStore = useAuthStore()
const page = ref<AiModelsView | null>(null)
const search = ref('')
const action = ref<'query' | null>(null)
// 目录读取不与供应商保存或检测同时操作。
const busy = computed(() => action.value !== null)
const errorMessage = ref('')
let sequence = 0
let controller: AbortController | null = null

/** 目录响应同时绑定账号、供应商和序号，旧请求不能替换当前目录。 */
async function load(offset = 0): Promise<void> {
  if (props.disabled || busy.value || !authStore.token) return
  const current = ++sequence
  const token = authStore.token
  const providerId = props.providerId
  const abort = new AbortController()
  controller = abort
  action.value = 'query'
  emit('busyChange', true)
  errorMessage.value = ''
  try {
    const response = await queryAiModels({ providerId, search: search.value.trim(), offset, limit: 30 }, abort.signal)
    if (current !== sequence || token !== authStore.token || providerId !== props.providerId || abort.signal.aborted) return
    if (!response.data || response.data.providerId !== providerId) throw new AiSettingsError('目录供应商标识不一致')
    page.value = response.data
  } catch (error: unknown) {
    if (current === sequence && token === authStore.token && !(error instanceof AiSettingsError && error.cancelled)) {
      errorMessage.value = error instanceof AiSettingsError ? error.message : '模型目录读取失败'
    }
  } finally {
    if (current === sequence) { controller = null; action.value = null; emit('busyChange', false) }
  }
}
/** 取消旧请求并清空目录局部状态，后续迟到结果不得覆盖新供应商。 */
function reset(): void {
  sequence += 1
  controller?.abort()
  controller = null
  page.value = null
  search.value = ''
  errorMessage.value = ''
  action.value = null
  emit('busyChange', false)
}
// 供应商或账号变化后先回收旧请求，再读取新供应商的离线目录。
watch(() => [props.providerId, authStore.token] as const, () => { reset(); void load() }, { immediate: true })
onBeforeUnmount(reset)
</script>
