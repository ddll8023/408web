<!-- 新增自定义供应商：填写名称、接口地址、协议与 Key，保存成功后才加入供应商列表。 -->
<template>
  <ResponsiveDialog v-model:visible="visibleModel" title="新增自定义供应商" width="640px" max-width="calc(100vw - 24px)" @close="close">
    <form id="ai-custom-provider-form" class="space-y-4" :aria-busy="busy" @submit.prevent="submit">
      <Alert v-if="errorMessage" type="error">{{ errorMessage }}</Alert>
      <div>
        <FormLabel label="供应商名称" for-id="ai-custom-provider-name" required />
        <input id="ai-custom-provider-name" v-model="name" type="text" autocomplete="off" maxlength="200"
          :disabled="busy" required placeholder="例如 本机 Ollama、公司网关"
          class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
      </div>
      <div>
        <FormLabel label="接口地址" for-id="ai-custom-provider-base" required />
        <input id="ai-custom-provider-base" v-model="baseUrl" type="url" autocomplete="off" autocapitalize="none" :spellcheck="false"
          maxlength="2048" :disabled="busy" required placeholder="https://api.example.com/v1"
          aria-describedby="ai-custom-provider-base-help"
          class="h-[42px] w-full rounded-md border border-line bg-white px-4 font-mono text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        <p id="ai-custom-provider-base-help" class="mt-1 text-xs text-ink-soft">填写上游服务的基础地址，通常以 /v1 结尾；支持 http(s)，服务端不跟随重定向。题目内容会发送到该地址。</p>
      </div>
      <div>
        <FormLabel label="上游协议" for-id="ai-custom-provider-protocol" required />
        <Select id="ai-custom-provider-protocol" v-model="protocol" :options="PROTOCOLS" :disabled="busy" aria-label="上游协议" />
        <p class="mt-1 text-xs text-ink-soft">协议决定请求路径与参数形状；选错会在检测或咨询时暴露为调用失败。</p>
      </div>
      <div>
        <FormLabel label="API Key" for-id="ai-custom-provider-key" required />
        <input id="ai-custom-provider-key" v-model="apiKey" type="password" autocomplete="off" autocapitalize="none" :spellcheck="false"
          maxlength="4096" :disabled="busy" required placeholder="填写该供应商的 API Key"
          aria-describedby="ai-custom-provider-key-help"
          class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        <p id="ai-custom-provider-key-help" class="mt-1 text-xs text-ink-soft">服务端加密保存，不回显、不写浏览器持久化存储。保存不会发送模型请求。</p>
      </div>
      <div class="flex items-center gap-2">
        <Switch id="ai-custom-provider-enabled" v-model="enabled" :disabled="busy" aria-label="启用该供应商" />
        <FormLabel label="启用该供应商" for-id="ai-custom-provider-enabled" />
      </div>
    </form>
    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <CustomButton :disabled="busy" @click="close">取消</CustomButton>
        <CustomButton type="primary" :loading="busy" @click="submit">保存供应商</CustomButton>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { AiSettingsError, saveAiCustomProvider, type AiCustomProviderView, type AiProtocol } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import Select from '@/components/basic/Select.vue'
import Switch from '@/components/basic/Switch.vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const PROTOCOLS: { label: string; value: AiProtocol }[] = [
  { label: 'OpenAI Chat Completions', value: 'openai-completions' },
  { label: 'OpenAI Responses', value: 'openai-responses' },
  { label: 'Anthropic Messages', value: 'anthropic-messages' },
]

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ 'update:visible': [value: boolean]; created: [provider: AiCustomProviderView] }>()
const authStore = useAuthStore()
const { showToast } = useToast()
const name = ref('')
const baseUrl = ref('')
const protocol = ref<AiProtocol | ''>('openai-completions')
const apiKey = ref('')
const enabled = ref(true)
const busy = ref(false)
const errorMessage = ref('')
let sequence = 0
let controller: AbortController | null = null

// 由父组件控制显隐，关闭时由父组件负责销毁与清理。
const visibleModel = computed({ get: () => props.visible, set: (value: boolean) => emit('update:visible', value) })

/** 只接受三种已知协议，拒绝把空值或未知字符串当作可执行协议。 */
function isProtocol(value: string): value is AiProtocol {
  return value === 'openai-completions' || value === 'openai-responses' || value === 'anthropic-messages'
}

/** 校验自定义接口地址：只允许 http(s)，拒绝内嵌账号、查询串与片段，与服务端规则一致。 */
function validEndpoint(value: string): boolean {
  try {
    const url = new URL(value)
    return (url.protocol === 'http:' || url.protocol === 'https:') && Boolean(url.hostname) &&
      !url.username && !url.password && !url.search && !url.hash
  } catch {
    return false
  }
}

/** 新建供应商只提交一次，成功后交给父组件合并列表；失败只展示脱敏消息。 */
async function submit(): Promise<void> {
  if (busy.value || !authStore.token) return
  if (!name.value.trim()) { errorMessage.value = '请填写供应商名称'; return }
  if (!validEndpoint(baseUrl.value.trim())) { errorMessage.value = '接口地址格式无效，请填写 http(s) 地址'; return }
  if (!apiKey.value.trim()) { errorMessage.value = '请填写 API Key'; return }
  if (!isProtocol(protocol.value)) { errorMessage.value = '请选择上游协议'; return }
  const selectedProtocol = protocol.value
  const current = ++sequence
  const abort = new AbortController()
  controller = abort
  busy.value = true
  errorMessage.value = ''
  try {
    const response = await saveAiCustomProvider({
      name: name.value.trim(), baseUrl: baseUrl.value.trim(), protocol: selectedProtocol,
      enabled: enabled.value, apiKey: apiKey.value.trim(),
    }, abort.signal)
    if (current !== sequence || abort.signal.aborted) return
    if (!response.data) throw new AiSettingsError('保存响应缺少供应商状态')
    emit('created', response.data)
    showToast('自定义供应商已保存，尚未检测模型调用权限', 'success')
    close()
  } catch (error: unknown) {
    if (current === sequence && !(error instanceof AiSettingsError && error.cancelled)) {
      errorMessage.value = error instanceof AiSettingsError ? error.message : '保存自定义供应商失败，请稍后重试'
    }
  } finally {
    if (current === sequence) { controller = null; busy.value = false }
  }
}

/** 关闭并取消未完成的保存请求，清空局部表单纯文本。 */
function close(): void {
  sequence += 1
  controller?.abort()
  controller = null
  busy.value = false
  apiKey.value = ''
  errorMessage.value = ''
  emit('update:visible', false)
}

// 每次打开都从空白表单开始，避免上次输入残留。
watch(() => props.visible, (value) => {
  if (!value) return
  sequence += 1
  name.value = ''
  baseUrl.value = ''
  protocol.value = 'openai-completions'
  apiKey.value = ''
  enabled.value = true
  errorMessage.value = ''
})
onBeforeUnmount(() => { controller?.abort() })
</script>
