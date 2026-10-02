<!-- 单供应商配置：Key 仅保留在局部表单，检测使用已保存凭据并单独确认额度。 -->
<template>
  <section class="space-y-4" :aria-busy="busy" aria-labelledby="ai-provider-title">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 id="ai-provider-title" class="text-lg font-medium text-ink">{{ provider.name }}</h3>
      <span class="text-sm text-ink-soft">{{ provider.hasApiKey ? '凭据已保存 · 调用权限未自动检测' : '尚未保存凭据' }}</span>
    </div>
    <div v-if="provider.baseUrls.length" class="rounded-md border border-line bg-surface p-3 text-xs text-ink-soft">
      <p>服务端固定的服务地址</p>
      <p v-for="url in provider.baseUrls" :key="url" class="mt-1 break-all font-mono">{{ url }}</p>
    </div>
    <Alert v-if="!provider.supported" type="warning">{{ provider.unsupportedReason }}</Alert>
    <Alert v-if="errorMessage" type="error">{{ errorMessage }}</Alert>
    <form v-if="provider.supported" class="space-y-4" @submit.prevent="save">
      <div>
        <FormLabel label="API Key" :for-id="keyInputId" :required="!provider.hasApiKey" class="mb-1" />
        <input :id="keyInputId" v-model="apiKey" type="password" autocomplete="off" autocapitalize="none" :spellcheck="false" maxlength="4096"
          :disabled="disabled || busy" :required="!provider.hasApiKey" :placeholder="provider.hasApiKey ? '已保存，留空保留；填写新值则替换' : '填写该供应商的 API Key'"
          :aria-describedby="`${keyInputId}-help`" class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        <p :id="`${keyInputId}-help`" class="mt-1 text-xs text-ink-soft">服务端加密保存，不回显、不写浏览器持久化存储。保存不会发送模型请求。</p>
      </div>
      <div class="flex items-center gap-2">
        <Switch :id="`${keyInputId}-enabled`" v-model="enabled" :disabled="disabled || busy" aria-label="启用该供应商" />
        <FormLabel label="启用该供应商" :for-id="`${keyInputId}-enabled`" />
      </div>
      <div class="flex flex-wrap gap-2">
        <CustomButton type="primary" :loading="operation === 'save'" :disabled="disabled || busy" @click="save">保存供应商</CustomButton>
        <CustomButton v-if="provider.configured" type="danger" :loading="operation === 'delete'" :disabled="disabled || busy" @click="remove">清除供应商</CustomButton>
      </div>
    </form>
    <div v-if="provider.supported" class="border-t border-line pt-4">
      <div class="flex flex-wrap items-center gap-3">
        <CustomButton :loading="operation === 'check'" :disabled="!canCheck" @click="check">检测所选模型</CustomButton>
        <CustomButton v-if="operation === 'check'" @click="cancelCheck">停止检测</CustomButton>
        <span v-if="checkedModel" role="status" class="text-sm text-ink">{{ checkedModel }} · 本次检测成功</span>
      </div>
      <p class="mt-2 text-xs text-ink-soft">先在目录中选择型号。检测会发一次短文本请求并可能消耗额度；不发送题目或聊天历史，不自动重试。</p>
      <p v-if="dirty" class="mt-1 text-xs text-ink-soft">有未保存的凭据设置，请先保存再检测。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { AiSettingsError, checkAiModel, deleteAiProvider, saveAiProvider,
  type AiCatalogModelView, type AiProviderConfigView, type AiProviderView } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import Switch from '@/components/basic/Switch.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ provider: AiProviderView; model: AiCatalogModelView | null; disabled?: boolean }>()
const emit = defineEmits<{ saved: [config: AiProviderConfigView]; deleted: [providerId: string]; busyChange: [busy: boolean] }>()
const authStore = useAuthStore()
const { showConfirm } = useConfirm()
const { showToast } = useToast()
const apiKey = ref('')
const enabled = ref(props.provider.enabled || !props.provider.configured)
const operation = ref<'save' | 'delete' | 'check' | null>(null)
// 单供应商操作互斥，等待确认也属于操作中。
const busy = computed(() => operation.value !== null)
// 为当前供应商的 Key、帮助和启用开关生成稳定的关联标识。
const keyInputId = computed(() => `ai-key-${props.provider.id}`)
// 空 Key 表示保留，启用状态变化或新 Key 才属于未保存修改。
const dirty = computed(() => Boolean(apiKey.value.trim()) || enabled.value !== props.provider.enabled)
// 检测只能使用已保存且未被局部修改的当前修订，不能偷偷检测未保存的 Key。
const canCheck = computed(() => !props.disabled && !busy.value && !dirty.value && props.provider.supported &&
  props.provider.hasApiKey && props.provider.enabled && props.provider.revision !== null && props.model?.provider === props.provider.id)
const errorMessage = ref('')
const checkedModel = ref('')
let sequence = 0
let controller: AbortController | null = null

/** 绑定账号、供应商和序号并建立取消控制，清除旧检测结论，不保存请求对象。 */
function begin(action: 'save' | 'delete' | 'check') {
  const abort = new AbortController()
  controller = abort
  operation.value = action
  checkedModel.value = ''
  errorMessage.value = ''
  emit('busyChange', true)
  return { sequence: ++sequence, token: authStore.token, providerId: props.provider.id, abort }
}
type Context = ReturnType<typeof begin>
/** 只接受当前账号和供应商最新操作的未取消结果。 */
function current(context: Context): boolean {
  return context.sequence === sequence && context.token === authStore.token &&
    context.providerId === props.provider.id && !context.abort.signal.aborted
}
/** 原操作结束才释放子组件忙状态，迟到请求不能解除新操作的锁定。 */
function finish(context: Context): void {
  if (context.sequence !== sequence) return
  controller = null
  operation.value = null
  emit('busyChange', false)
}
/** 取消和失效结果不报错，只展示经过 API 边界脱敏的安全消息。 */
function fail(error: unknown, context: Context): void {
  if (!current(context) || (error instanceof AiSettingsError && error.cancelled)) return
  errorMessage.value = error instanceof AiSettingsError ? error.message : '供应商操作失败，请稍后重试'
}
/** 首次保存要求 Key，空值保留旧值；成功后清空局部明文且不自动检测。 */
async function save(): Promise<void> {
  if (props.disabled || busy.value || !authStore.token || !props.provider.supported) return
  if (!props.provider.hasApiKey && !apiKey.value.trim()) { errorMessage.value = '首次保存请填写 API Key'; return }
  const context = begin('save')
  try {
    const response = await saveAiProvider({ providerId: props.provider.id, enabled: enabled.value,
      ...(apiKey.value.trim() ? { apiKey: apiKey.value.trim() } : {}) }, context.abort.signal)
    if (!current(context)) return
    if (!response.data) throw new AiSettingsError('保存响应缺少供应商状态')
    apiKey.value = ''
    emit('saved', response.data)
    showToast('供应商已保存，尚未检测模型调用权限', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 确认后清除本站供应商配置及必要默认引用，不撤销上游 Key。 */
async function remove(): Promise<void> {
  if (props.disabled || busy.value || !authStore.token || !props.provider.configured) return
  const context = begin('delete')
  try {
    const confirmed = await showConfirm({ title: '清除供应商', message: `删除本站保存的 ${props.provider.name} 加密密钥。若它是当前默认供应商，也会清除默认选择；不会撤销供应商账户中的 Key。`,
      confirmText: '清除供应商', cancelText: '取消', type: 'danger' })
    if (!confirmed || !current(context)) return
    await deleteAiProvider(context.providerId, context.abort.signal)
    if (!current(context)) return
    apiKey.value = ''
    emit('deleted', context.providerId)
    showToast('供应商配置已清除', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/**
 * 明确确认额度后仅检测已保存修订与所选型号，不发送题目或聊天。
 * 返回结果仍须匹配账号、修订、型号与未修改表单，不能把旧成功带到新配置。
 */
async function check(): Promise<void> {
  const model = props.model
  const revision = props.provider.revision
  if (!canCheck.value || !model || !revision) return
  const context = begin('check')
  try {
    const confirmed = await showConfirm({ title: '检测模型连接',
      message: `使用已保存的 ${props.provider.name} 凭据检测 ${model.name}（${model.id}），会发一次真实请求并可能消耗额度。确定继续吗？`,
      confirmText: '确认并检测', cancelText: '取消', type: 'warning' })
    if (!confirmed || !current(context)) return
    const response = await checkAiModel({ providerId: context.providerId, providerRevision: revision,
      modelId: model.id, requestId: crypto.randomUUID(), confirmUsage: true }, context.abort.signal)
    if (!current(context) || props.provider.revision !== revision || props.model?.id !== model.id || dirty.value) return
    if (!response.data) throw new AiSettingsError('检测响应缺少结果')
    checkedModel.value = `${model.name}（${model.id}）`
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 中止本地等待并关闭内部请求，不能把停止等待伪装成上游已停止。 */
function reset(): void {
  sequence += 1
  controller?.abort()
  controller = null
  operation.value = null
  apiKey.value = ''
  checkedModel.value = ''
  errorMessage.value = ''
  enabled.value = props.provider.enabled || !props.provider.configured
  emit('busyChange', false)
}
/** 取消本地检测等待并提示停止确认边界，不保证上游已停止或允许立即重发。 */
function cancelCheck(): void {
  reset()
  errorMessage.value = '已请求停止检测；上游未确认停止前，新的检测或咨询会被拒绝。'
}
// 账号、供应商或修订变化时取消旧请求，并清除局部明文和检测结论。
watch(() => [props.provider.id, props.provider.revision, authStore.token] as const, reset)
// 表单或型号一旦变化，本次成功结论立即失效。
watch(() => [apiKey.value, enabled.value, props.model?.id], () => { checkedModel.value = '' })
onBeforeUnmount(reset)
</script>
