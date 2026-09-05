import { createApp } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Confirm from '@/components/basic/Confirm.vue'

let confirmInstance: InstanceType<typeof Confirm> | null = null

const getConfirmInstance = () => {
  if (!confirmInstance) {
    const app = createApp(Confirm)
    app.component('font-awesome-icon', FontAwesomeIcon)
    const container = document.createElement('div')
    document.body.appendChild(container)
    confirmInstance = app.mount(container) as InstanceType<typeof Confirm>
  }
  return confirmInstance
}

export const confirm = (message: string, title = '提示', options: { confirmButtonText?: string; cancelButtonText?: string; type?: string } = {}) => {
  return new Promise<string>((resolve, reject) => {
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
