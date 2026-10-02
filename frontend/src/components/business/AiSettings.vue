<!-- 个人模型服务：按供应商管理凭据与目录，默认咨询选择独立保存，敏感状态仅存组件内存。 -->
<template>
  <section class="rounded-lg border border-line bg-white" aria-labelledby="ai-settings-title" :aria-busy="busy">
    <header class="border-b border-line p-4 sm:px-6">
      <h2 id="ai-settings-title" class="m-0 flex items-center gap-2 text-xl text-ink">
        <font-awesome-icon :icon="['fas', 'cog']" class="text-accent" aria-hidden="true" />模型服务
      </h2>
      <p class="mt-2 text-sm text-ink-soft">供应商凭据、模型目录和默认咨询选择分开管理。保存不自动检测，也不发送生成请求。</p>
    </header>
    <div class="p-4 sm:p-6">
      <p v-if="operation === 'load'" role="status" aria-live="polite" class="py-6 text-ink-soft">正在加载模型服务…</p>
      <Alert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}<CustomButton v-if="!loaded" size="sm" class="mt-2" :disabled="busy" @click="loadSettings">重新加载</CustomButton></Alert>
      <template v-if="loaded">
        <div class="mb-5 rounded-md border border-line bg-surface p-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-ink">默认咨询模型</p>
              <p v-if="savedSettings" class="mt-1 break-all text-sm text-ink-soft">{{ defaultProviderName }} / {{ savedSettings.modelId }} · {{ savedSettings.enabled ? '已启用' : '已暂停' }}</p>
              <p v-else class="mt-1 text-sm text-ink-soft">尚未选择。先保存一个供应商，再从目录选择型号。</p>
            </div>
            <CustomButton v-if="savedSettings" size="sm" :disabled="busy" :loading="operation === 'clear'" @click="clearDefault">清除默认选择</CustomButton>
          </div>
          <p class="mt-2 text-xs text-ink-soft">题目页聊天入口和图片处理仍未接入；完成配置不代表整项题目咨询已完成。</p>
        </div>
        <div class="grid gap-5 xl:grid-cols-[220px_minmax(0,1fr)]">
          <aside class="min-w-0">
            <CustomInput id="ai-provider-search" v-model="providerSearch" label="模型供应商" placeholder="搜索名称或 ID" :disabled="busy" />
            <nav aria-label="模型供应商" class="mt-3 max-h-[420px] space-y-1 overflow-y-auto pr-1">
              <button v-for="provider in filteredProviders" :key="provider.id" type="button" :disabled="busy"
                :aria-pressed="selectedProviderId === provider.id"
                class="w-full rounded-md border px-3 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50"
                :class="selectedProviderId === provider.id ? 'border-accent bg-accent/10' : 'border-transparent hover:bg-surface'"
                @click="selectProvider(provider.id)">
                <span class="block text-sm font-medium text-ink">{{ provider.name }}</span>
                <span class="mt-1 block text-xs text-ink-soft">{{ !provider.supported ? '需要额外配置 · 暂不接入' : provider.hasApiKey ? (provider.enabled ? '凭据已保存' : '已暂停') : '未配置' }}</span>
              </button>
              <p v-if="!filteredProviders.length" class="p-3 text-sm text-ink-soft">没有匹配的供应商。</p>
            </nav>
          </aside>
          <div class="min-w-0 space-y-5">
            <template v-if="selectedProvider">
              <AiProviderSettings :key="selectedProvider.id" :provider="selectedProvider" :model="selectedModel"
                :disabled="operation !== null || pickerBusy" @saved="providerSaved" @deleted="providerDeleted" @busy-change="providerBusy = $event" />
              <template v-if="selectedProvider.supported">
                <div class="border-t border-line pt-5">
                  <AiModelPicker :key="selectedProvider.id" :provider-id="selectedProvider.id" :model-value="selectedModel?.id ?? ''"
                    :disabled="operation !== null || providerBusy"
                    @select="selectedModel = $event" @busy-change="pickerBusy = $event" />
                </div>
                <div class="space-y-3 border-t border-line pt-5">
                  <p class="break-all text-sm text-ink">{{ selectedModel ? `所选型号：${selectedModel.name}（${selectedModel.id}）` : '尚未选择型号，不会自动替你选择。' }}</p>
                  <div class="flex items-center gap-2">
                    <Switch id="ai-consultation-enabled" v-model="defaultEnabled" :disabled="busy" aria-label="启用默认题目咨询配置" />
                    <FormLabel label="启用默认题目咨询配置" for-id="ai-consultation-enabled" />
                  </div>
                  <p class="text-xs text-ink-soft">当前默认输入为纯文本。模型图像能力由目录元数据标注，本站图片咨询链路尚未完成。</p>
                  <div class="flex flex-wrap gap-2">
                    <CustomButton type="primary" :disabled="!canSaveDefault" :loading="operation === 'save'" @click="saveDefault">保存为默认咨询模型</CustomButton>
                    <CustomButton :disabled="busy" @click="loadSettings">重新加载配置</CustomButton>
                  </div>
                  <p v-if="!selectedProvider.hasApiKey || !selectedProvider.enabled" class="text-xs text-ink-soft">请先保存并启用该供应商，再设置默认咨询模型。</p>
                </div>
              </template>
            </template>
            <p v-else class="rounded-md border border-line bg-surface p-6 text-sm text-ink-soft">请选择供应商。只接入服务端固定审核的供应商，不开放自定义端点或订阅 OAuth。</p>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { AiSettingsError, deleteAiSettings, queryAiProviders, queryAiSettings, saveAiSettings,
  type AiCatalogModelView, type AiProviderConfigView, type AiProviderView, type AiSettingsView } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import Switch from '@/components/basic/Switch.vue'
import AiModelPicker from '@/components/business/AiModelPicker.vue'
import AiProviderSettings from '@/components/business/AiProviderSettings.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { showConfirm } = useConfirm()
const { showToast } = useToast()
const providers = ref<AiProviderView[]>([])
const savedSettings = ref<AiSettingsView | null>(null)
const selectedProviderId = ref('')
const selectedModel = ref<AiCatalogModelView | null>(null)
const providerSearch = ref('')
const defaultEnabled = ref(true)
const loaded = ref(false)
const operation = ref<'load' | 'save' | 'clear' | null>(null)
const providerBusy = ref(false)
const pickerBusy = ref(false)
// 汇总父页与两类子操作状态，避免配置和检测互相覆盖。
const busy = computed(() => operation.value !== null || providerBusy.value || pickerBusy.value)
const errorMessage = ref('')
// 从目录映射当前供应商，不把导航状态写入浏览器持久化存储。
const selectedProvider = computed(() => providers.value.find(provider => provider.id === selectedProviderId.value) ?? null)
// 本地筛选供应商名称与 ID，不额外发起搜索请求。
const filteredProviders = computed(() => {
  const search = providerSearch.value.trim().toLowerCase()
  return providers.value.filter(provider => !search || `${provider.name} ${provider.id}`.toLowerCase().includes(search))
})
// 已保存的默认选择独立展示，不自动改成当前浏览型号。
const defaultProviderName = computed(() => providers.value.find(provider => provider.id === savedSettings.value?.providerId)?.name ?? savedSettings.value?.providerId)
// 只允许把已保存启用的供应商及明确所选型号设置为默认。
const canSaveDefault = computed(() => !busy.value && Boolean(selectedProvider.value?.supported && selectedProvider.value.hasApiKey &&
  selectedProvider.value.enabled && selectedModel.value?.provider === selectedProvider.value.id))
let sequence = 0
let controller: AbortController | null = null

/** 固定当前账号和请求序号，建立可取消的父页操作，不保存敏感请求内容。 */
function begin(action: 'load' | 'save' | 'clear') {
  const abort = new AbortController()
  controller = abort
  operation.value = action
  errorMessage.value = ''
  return { sequence: ++sequence, token: authStore.token, abort }
}
type Context = ReturnType<typeof begin>
/** 只接受仍属于当前账号、最新操作且未取消的结果。 */
function current(context: Context): boolean { return context.sequence === sequence && context.token === authStore.token && !context.abort.signal.aborted }
/** 仅原操作可解除父页忙状态，迟到清理不能覆盖后续操作。 */
function finish(context: Context): void {
  if (context.sequence === sequence) { controller = null; operation.value = null }
}
/** 忽略取消与失效结果，只展示 API 层已经脱敏的错误。 */
function fail(error: unknown, context: Context): void {
  if (current(context) && !(error instanceof AiSettingsError && error.cancelled)) {
    errorMessage.value = error instanceof AiSettingsError ? error.message : '模型服务操作失败，请稍后重试'
  }
}
/** 读取供应商状态和独立默认选择，恢复其供应商但不自动选择新的型号。 */
async function loadSettings(): Promise<void> {
  if (busy.value || !authStore.token) return
  const context = begin('load')
  loaded.value = false
  selectedModel.value = null
  try {
    const [catalog, settings] = await Promise.all([queryAiProviders(context.abort.signal), queryAiSettings(context.abort.signal)])
    if (!current(context)) return
    if (!catalog.data) throw new AiSettingsError('响应缺少供应商目录')
    providers.value = catalog.data.providers
    savedSettings.value = settings.data
    defaultEnabled.value = settings.data?.enabled ?? true
    selectedProviderId.value = settings.data?.providerId ?? (providers.value.some(provider => provider.id === selectedProviderId.value) ? selectedProviderId.value : '')
    loaded.value = true
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 主动切换供应商时清除临时型号，由子组件卸载回收旧 Key 和请求。 */
function selectProvider(id: string): void {
  if (busy.value || id === selectedProviderId.value) return
  selectedModel.value = null
  selectedProviderId.value = id
}
/** 合并该供应商的公开保存结果，不改动其他供应商或默认选择。 */
function providerSaved(config: AiProviderConfigView): void {
  providers.value = providers.value.map(provider => provider.id === config.providerId
    ? { ...provider, configured: true, enabled: config.enabled, hasApiKey: config.hasApiKey, revision: config.revision } : provider)
}
/** 清除对应供应商的本地保存状态，并同步移除服务端已连带删除的默认引用。 */
function providerDeleted(id: string): void {
  providers.value = providers.value.map(provider => provider.id === id
    ? { ...provider, configured: false, enabled: false, hasApiKey: false, revision: null } : provider)
  if (savedSettings.value?.providerId === id) { savedSettings.value = null; defaultEnabled.value = true }
}
/** 只保存用户明确所选的纯文本默认型号，不携带 Key 或自动发起检测。 */
async function saveDefault(): Promise<void> {
  const model = selectedModel.value
  if (!canSaveDefault.value || !model) return
  const context = begin('save')
  try {
    const response = await saveAiSettings({ providerId: model.provider, modelId: model.id, inputMode: 'text', enabled: defaultEnabled.value }, context.abort.signal)
    if (!current(context)) return
    if (!response.data) throw new AiSettingsError('保存响应缺少默认选择')
    savedSettings.value = response.data
    showToast('默认咨询模型已保存，保存不会检测调用权限', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 确认后清除默认选择并失效旧结果，保留全部供应商凭据。 */
async function clearDefault(): Promise<void> {
  if (busy.value || !savedSettings.value) return
  const context = begin('clear')
  try {
    const confirmed = await showConfirm({ title: '清除默认选择', message: '只清除默认咨询型号，保留各供应商的加密 Key。已有咨询会话将失效。',
      confirmText: '清除默认选择', cancelText: '取消', type: 'danger' })
    if (!confirmed || !current(context)) return
    await deleteAiSettings(context.abort.signal)
    if (!current(context)) return
    savedSettings.value = null
    defaultEnabled.value = true
    showToast('默认咨询选择已清除', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 离开菜单或切换账号时清除全部局部状态，子组件同步销毁其 Key 和请求。 */
function reset(): void {
  sequence += 1
  controller?.abort()
  controller = null
  loaded.value = false
  operation.value = null
  providerBusy.value = false
  pickerBusy.value = false
  providers.value = []
  savedSettings.value = null
  selectedProviderId.value = ''
  selectedModel.value = null
  providerSearch.value = ''
  defaultEnabled.value = true
  errorMessage.value = ''
}
// 账号变化先取消并清空旧局部状态，再为新账号发起一次加载。
watch(() => authStore.token, () => { reset(); if (authStore.token) void loadSettings() }, { immediate: true })
onBeforeUnmount(reset)
</script>
