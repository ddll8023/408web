<!-- 自定义型号管理：手工录入能力声明，支持新增、删除与选中，不向上游探测。 -->
<template>
  <section aria-labelledby="ai-custom-model-title" :aria-busy="busy" class="space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 id="ai-custom-model-title" class="font-medium text-ink">自定义型号</h3>
      <CustomButton size="sm" :disabled="disabled || busy" @click="showForm = !showForm">
        {{ showForm ? '收起录入' : '新增型号' }}
      </CustomButton>
    </div>
    <p class="text-xs text-ink-soft">型号与能力由你手工声明；服务端不探测上游，目录收录不代表你的账号有调用权限。</p>
    <Alert v-if="errorMessage" type="error">{{ errorMessage }}<CustomButton size="sm" class="mt-2" :disabled="disabled || busy" @click="load">重新加载</CustomButton></Alert>
    <p v-if="loading" role="status" class="text-sm text-ink-soft">正在读取自定义型号…</p>
    <form v-if="showForm" class="space-y-3 rounded-md border border-line bg-surface p-4" @submit.prevent="save">
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <FormLabel label="型号 ID" for-id="ai-custom-model-id" required />
          <input id="ai-custom-model-id" v-model="draft.modelId" type="text" autocomplete="off" autocapitalize="none"
            :spellcheck="false" maxlength="200" :disabled="disabled || busy" required placeholder="例如 qwen2.5:7b"
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 font-mono text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        </div>
        <div>
          <FormLabel label="显示名称" for-id="ai-custom-model-name" required />
          <input id="ai-custom-model-name" v-model="draft.name" type="text" autocomplete="off" maxlength="200"
            :disabled="disabled || busy" required placeholder="例如 Qwen2.5 7B"
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        </div>
        <div>
          <FormLabel label="上下文上限" for-id="ai-custom-model-context" />
          <input id="ai-custom-model-context" v-model.number="draft.contextWindow" type="number" min="0" max="10000000" step="1"
            :disabled="disabled || busy"
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        </div>
        <div>
          <FormLabel label="输出上限" for-id="ai-custom-model-tokens" required />
          <input id="ai-custom-model-tokens" v-model.number="draft.maxTokens" type="number" min="1" max="1000000" step="1"
            :disabled="disabled || busy" required
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Switch id="ai-custom-model-images" v-model="draft.supportsImages" :disabled="disabled || busy" aria-label="支持图像输入" />
        <FormLabel label="支持图像输入" for-id="ai-custom-model-images" />
      </div>
      <div class="flex flex-wrap justify-end gap-2">
        <CustomButton :disabled="disabled || busy" @click="resetDraft">清空</CustomButton>
        <CustomButton type="primary" :loading="operation === 'save'" :disabled="disabled || busy" @click="save">保存型号</CustomButton>
      </div>
    </form>
    <div v-if="models.length" class="max-h-[360px] space-y-2 overflow-y-auto pr-1">
      <div v-for="model in models" :key="model.id" class="flex items-stretch gap-2">
        <button type="button" :disabled="disabled || busy" :aria-pressed="modelValue === model.id"
          class="min-w-0 flex-1 rounded-md border p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50"
          :class="modelValue === model.id ? 'border-accent bg-accent/10' : 'border-line bg-white hover:bg-surface'"
          @click="emit('select', model)">
          <span class="block font-medium text-ink">{{ model.name }}</span>
          <span class="mt-1 block break-all font-mono text-xs text-ink-soft">{{ model.id }}</span>
          <span class="mt-2 flex flex-wrap gap-2 text-xs text-ink-soft">
            <span>文本{{ model.supportsImages ? ' · 图像' : '' }}</span>
            <span v-if="model.contextWindow">上下文 {{ model.contextWindow.toLocaleString() }}</span>
            <span>输出 {{ model.maxTokens.toLocaleString() }}</span>
          </span>
        </button>
        <CustomButton size="sm" :disabled="disabled || busy" :aria-label="`删除型号 ${model.name}`" @click="remove(model)">删除</CustomButton>
      </div>
    </div>
    <p v-else-if="!loading" class="rounded-md border border-line bg-surface p-4 text-sm text-ink-soft">还没有自定义型号，先新增一个再检测或设为默认。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { AiSettingsError, deleteAiCustomModel, queryAiModels, saveAiCustomModel,
  type AiCatalogModelView } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import Switch from '@/components/basic/Switch.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ providerId: string; modelValue: string; disabled?: boolean }>()
const emit = defineEmits<{ select: [model: AiCatalogModelView | null]; busyChange: [busy: boolean]; changed: [] }>()
const authStore = useAuthStore()
const { showConfirm } = useConfirm()
const { showToast } = useToast()
const models = ref<AiCatalogModelView[]>([])
const loading = ref(false)
const operation = ref<'save' | 'delete' | null>(null)
const busy = computed(() => loading.value || operation.value !== null)
const showForm = ref(false)
const errorMessage = ref('')
const draft = reactive({ modelId: '', name: '', supportsImages: false, contextWindow: 32768, maxTokens: 8192 })
let sequence = 0
let controller: AbortController | null = null
let unmounted = false

/** 读取当前供应商的全部自定义型号，迟到结果不能覆盖新供应商或新账号。 */
async function load(): Promise<void> {
  if (!authStore.token) return
  const current = ++sequence
  const token = authStore.token
  const providerId = props.providerId
  const abort = new AbortController()
  controller = abort
  loading.value = true
  errorMessage.value = ''
  emit('busyChange', true)
  try {
    const response = await queryAiModels({ providerId, offset: 0, limit: 100 }, abort.signal)
    if (current !== sequence || token !== authStore.token || providerId !== props.providerId || abort.signal.aborted) return
    if (!response.data || response.data.providerId !== providerId) throw new AiSettingsError('目录供应商标识不一致')
    models.value = response.data.models
  } catch (error: unknown) {
    if (current === sequence && token === authStore.token && !(error instanceof AiSettingsError && error.cancelled)) {
      errorMessage.value = error instanceof AiSettingsError ? error.message : '自定义型号读取失败'
    }
  } finally {
    if (current === sequence) { controller = null; loading.value = false; emit('busyChange', false) }
  }
}

/** 校验手工录入的型号字段，与服务端约束保持一致。 */
function validDraft(): boolean {
  const id = draft.modelId.trim()
  if (!id) { errorMessage.value = '请填写型号 ID'; return false }
  if (!draft.name.trim()) { errorMessage.value = '请填写显示名称'; return false }
  if (!Number.isInteger(draft.maxTokens) || draft.maxTokens < 1 || draft.maxTokens > 1_000_000) {
    errorMessage.value = '输出上限需为 1 到 1000000 之间的整数'; return false
  }
  if (!Number.isInteger(draft.contextWindow) || draft.contextWindow < 0 || draft.contextWindow > 10_000_000) {
    errorMessage.value = '上下文上限需为 0 到 10000000 之间的整数'; return false
  }
  return true
}

/** 保存型号后重新读取目录并选中新行，避免把旧列表当作最新状态。 */
async function save(): Promise<void> {
  if (props.disabled || busy.value || !authStore.token) return
  if (!validDraft()) return
  const current = ++sequence
  const abort = new AbortController()
  controller = abort
  operation.value = 'save'
  errorMessage.value = ''
  emit('busyChange', true)
  try {
    const response = await saveAiCustomModel({
      providerId: props.providerId, modelId: draft.modelId.trim(), name: draft.name.trim(),
      supportsImages: draft.supportsImages, contextWindow: draft.contextWindow, maxTokens: draft.maxTokens,
    }, abort.signal)
    if (current !== sequence || abort.signal.aborted) return
    if (!response.data) throw new AiSettingsError('保存响应缺少型号信息')
    emit('select', response.data)
    showToast('自定义型号已保存', 'success')
    resetDraft()
    showForm.value = false
    operation.value = null
    emit('busyChange', false)
    await load()
    if (!unmounted) emit('changed')
  } catch (error: unknown) {
    if (current === sequence && !(error instanceof AiSettingsError && error.cancelled)) {
      errorMessage.value = error instanceof AiSettingsError ? error.message : '自定义型号保存失败，请稍后重试'
    }
  } finally {
    if (current === sequence) { controller = null; operation.value = null; emit('busyChange', false) }
  }
}

/** 确认后删除型号；若它正被选中或设为默认，由服务端复选框一并清理并通知父组件。 */
async function remove(model: AiCatalogModelView): Promise<void> {
  if (props.disabled || busy.value || !authStore.token) return
  const providerId = props.providerId
  const current = ++sequence
  const abort = new AbortController()
  controller = abort
  operation.value = 'delete'
  errorMessage.value = ''
  emit('busyChange', true)
  try {
    const confirmed = await showConfirm({
      title: '删除自定义型号', message: `删除型号 ${model.name}（${model.id}）及其声明能力；若它正被设为默认咨询模型，也会清除默认选择。`,
      confirmText: '删除型号', cancelText: '取消', type: 'danger',
    })
    if (!confirmed || current !== sequence || abort.signal.aborted) return
    await deleteAiCustomModel(providerId, model.id, abort.signal)
    if (current !== sequence || abort.signal.aborted) return
    if (props.modelValue === model.id) emit('select', null)
    showToast('自定义型号已删除', 'success')
    operation.value = null
    emit('busyChange', false)
    await load()
    if (!unmounted) emit('changed')
  } catch (error: unknown) {
    if (current === sequence && !(error instanceof AiSettingsError && error.cancelled)) {
      errorMessage.value = error instanceof AiSettingsError ? error.message : '自定义型号删除失败，请稍后重试'
    }
  } finally {
    if (current === sequence) { controller = null; operation.value = null; emit('busyChange', false) }
  }
}

/** 清空录入表单，保留当前列表。 */
function resetDraft(): void {
  draft.modelId = ''
  draft.name = ''
  draft.supportsImages = false
  draft.contextWindow = 32768
  draft.maxTokens = 8192
}

/** 切换供应商或账号时取消旧请求并清空局部目录与草稿。 */
function reset(): void {
  sequence += 1
  controller?.abort()
  controller = null
  models.value = []
  showForm.value = false
  resetDraft()
  errorMessage.value = ''
  loading.value = false
  operation.value = null
  emit('busyChange', false)
}

watch(() => [props.providerId, authStore.token] as const, () => { reset(); void load() }, { immediate: true })
onBeforeUnmount(() => { unmounted = true; reset() })
</script>
