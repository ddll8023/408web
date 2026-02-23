import { createApp, ref } from 'vue'
import Toast from '@/components/basic/Toast.vue'

// 创建 Toast 实例
const toastInstance = ref(null)
let app = null

const getToastInstance = () => {
  if (!toastInstance.value) {
    app = createApp(Toast)
    const container = document.createElement('div')
    document.body.appendChild(container)
    toastInstance.value = app.mount(container)
  }
  return toastInstance.value
}

export const toast = {
  success: (message, duration) => getToastInstance().show(message, 'success', duration),
  error: (message, duration) => getToastInstance().show(message, 'error', duration),
  warning: (message, duration) => getToastInstance().show(message, 'warning', duration),
  info: (message, duration) => getToastInstance().show(message, 'info', duration)
}

export default toast
