import { toast, type ToastType } from '@/utils/toast'

/**
 * useToast 组合式函数
 * 功能：封装 Toast 组件调用，提供简洁的 API
 * 使用方式：const { showToast } = useToast()
 */
export function useToast() {
  const showToast = (
    message: string,
    type: ToastType = 'success',
    duration = 3000
  ) => toast[type](message, duration)

  return {
    showToast
  }
}
