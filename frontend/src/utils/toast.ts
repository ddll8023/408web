import { createApp } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Toast from '@/components/basic/Toast.vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

// 创建 Toast 实例
let toastInstance: InstanceType<typeof Toast> | null = null

const getToastInstance = () => {
  if (!toastInstance) {
    const app = createApp(Toast)
    app.component('font-awesome-icon', FontAwesomeIcon)
    const container = document.createElement('div')
    document.body.appendChild(container)
    toastInstance = app.mount(container) as InstanceType<typeof Toast>
  }
  return toastInstance
}

export const toast = {
  success: (message: string, duration?: number) => getToastInstance().show(message, 'success', duration),
  error: (message: string, duration?: number) => getToastInstance().show(message, 'error', duration),
  warning: (message: string, duration?: number) => getToastInstance().show(message, 'warning', duration),
  info: (message: string, duration?: number) => getToastInstance().show(message, 'info', duration)
}

export default toast
