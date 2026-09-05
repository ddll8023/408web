import confirm from '@/utils/confirm'

interface ConfirmOptions {
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: 'success' | 'warning' | 'danger' | 'info'
}

/**
 * useConfirm 组合式函数
 * 功能：封装 Confirm 对话框组件调用，提供简洁的 API
 * 使用方式：const { showConfirm } = useConfirm()
 */

export function useConfirm() {
  const showConfirm = async (options: ConfirmOptions = {}) => {
    const {
      title = '提示',
      message = '确定要执行此操作吗？',
      confirmText = '确定',
      cancelText = '取消',
      type = 'warning'
    } = options
    return confirm({
      message,
      title,
      confirmText,
      cancelText,
      type
    })
  }

  return {
    showConfirm
  }
}
