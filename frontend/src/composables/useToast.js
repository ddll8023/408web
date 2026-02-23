import { ref } from 'vue'

/**
 * useToast 组合式函数
 * 功能：封装 Toast 组件调用，提供简洁的 API
 * 使用方式：const { showToast } = useToast()
 */
export function useToast() {

  /**
   * 显示 Toast 消息
   * @param {string} message - 消息内容
   * @param {string} type - 消息类型：success, error, warning, info
   * @param {number} duration - 显示时长（毫秒）
   */
  const showToast = (message, type = 'success', duration = 3000) => {
    // 创建一个临时的 toast 元素
    const toast = document.createElement('div')
    toast.setAttribute('data-toast-component', 'true')
    document.body.appendChild(toast)

    // 动态导入 Toast 组件并挂载
    import('vue').then(({ createApp, ref }) => {
      const ToastComponent = {
        setup() {
          const visible = ref(true)
          const msg = ref(message)
          const msgType = ref(type)

          const typeClass = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            warning: 'bg-yellow-600',
            info: 'bg-blue-600'
          }[msgType.value] || 'bg-blue-600'

          const icon = {
            success: ['fas', 'check-circle'],
            error: ['fas', 'times-circle'],
            warning: ['fas', 'exclamation-circle'],
            info: ['fas', 'info-circle']
          }[msgType.value] || ['fas', 'info-circle']

          setTimeout(() => {
            visible.value = false
            setTimeout(() => toast.remove(), 300)
          }, duration)

          return { visible, msg, typeClass, icon }
        },
        template: `
          <transition name="toast">
            <div
              v-if="visible"
              class="fixed top-4 left-1/2 transform -translate-x-1/2 z-[9999] px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium"
              :class="typeClass"
            >
              <div class="flex items-center gap-2">
                <font-awesome-icon :icon="icon" />
                <span>{{ msg }}</span>
              </div>
            </div>
          </transition>
        `
      }

      const app = createApp(ToastComponent)

      // 注册 FontAwesome 图标
      import('@fortawesome/fontawesome-svg-core').then(({ library }) => {
        import('@fortawesome/free-solid-svg-icons').then(icons => {
          library.add(
            icons.faCheckCircle,
            icons.faTimesCircle,
            icons.faExclamationCircle,
            icons.faInfoCircle
          )
          import('@fortawesome/vue-fontawesome').then(({ FontAwesomeIcon }) => {
            app.component('font-awesome-icon', FontAwesomeIcon)
            app.mount(toast)
          })
        })
      })
    })
  }

  return {
    showToast
  }
}
