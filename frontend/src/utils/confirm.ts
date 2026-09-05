import { createApp } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Confirm from '@/components/basic/Confirm.vue'
import type { ConfirmOptions } from '@/components/basic/Confirm.vue'

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

type LegacyConfirmOptions = {
  confirmButtonText?: string
  cancelButtonText?: string
  type?: ConfirmOptions['type']
}
type ConfirmInput = ConfirmOptions | string

const normalizeOptions = (
  input: ConfirmInput,
  title?: string,
  options: LegacyConfirmOptions = {}
): ConfirmOptions => {
  if (typeof input !== 'string') return input

  return {
    message: input,
    title: title ?? '提示',
    confirmText: options.confirmButtonText ?? '确定',
    cancelText: options.cancelButtonText ?? '取消',
    type: options.type ?? 'warning'
  }
}

export function confirm(options: ConfirmOptions): Promise<boolean>
export function confirm(message: string, title?: string, options?: LegacyConfirmOptions): Promise<boolean>
export function confirm(
  input: ConfirmInput,
  title?: string,
  options: LegacyConfirmOptions = {}
): Promise<boolean> {
  return new Promise(resolve => {
    const instance = getConfirmInstance()

    instance.show(
      normalizeOptions(input, title, options),
      () => resolve(true),
      () => resolve(false)
    )
  })
}

export function alert(options: ConfirmOptions): Promise<void>
export function alert(message: string, title?: string, options?: LegacyConfirmOptions): Promise<void>
export function alert(
  input: ConfirmInput,
  title?: string,
  options: LegacyConfirmOptions = {}
): Promise<void> {
  return new Promise(resolve => {
    const instance = getConfirmInstance()
    instance.show(
      { ...normalizeOptions(input, title, options), mode: 'alert' },
      resolve,
      resolve
    )
  })
}

export default confirm
