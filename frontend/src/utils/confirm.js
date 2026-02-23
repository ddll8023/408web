import { createApp, ref } from 'vue'
import Confirm from '@/components/basic/Confirm.vue'

const confirmInstance = ref(null)
let app = null

const getConfirmInstance = () => {
  if (!confirmInstance.value) {
    app = createApp(Confirm)
    const container = document.createElement('div')
    document.body.appendChild(container)
    confirmInstance.value = app.mount(container)
  }
  return confirmInstance.value
}

export const confirm = (message, title = '提示', options = {}) => {
  return new Promise((resolve, reject) => {
    const instance = getConfirmInstance()

    // 调用 show 方法传递选项和回调
    instance.show(
      {
        message,
        title,
        confirmText: options.confirmButtonText || '确定',
        cancelText: options.cancelButtonText || '取消',
        type: options.type || 'warning'
      },
      // onConfirm
      () => {
        resolve('confirm')
      },
      // onCancel
      () => {
        reject('cancel')
      }
    )
  })
}

export default confirm
