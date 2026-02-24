import { ref, reactive } from 'vue'

/**
 * useConfirm 组合式函数
 * 功能：封装 Confirm 对话框组件调用，提供简洁的 API
 * 使用方式：const { showConfirm } = useConfirm()
 */

// 单例模式，确保同时只有一个确认框
let confirmInstance = null
let resolvePromise = null

/**
 * 显示确认对话框
 * @param {Object} options - 配置选项
 * @param {string} options.title - 标题
 * @param {string} options.message - 消息内容
 * @param {string} options.confirmText - 确认按钮文字
 * @param {string} options.cancelText - 取消按钮文字
 * @param {string} options.type - 类型：success, warning, danger, info
 * @returns {Promise} 返回 Promise，用户确认时 resolve，取消时 reject
 */
export function useConfirm() {
  const showConfirm = (options = {}) => {
    const {
      title = '提示',
      message = '确定要执行此操作吗？',
      confirmText = '确定',
      cancelText = '取消',
      type = 'warning'
    } = options

    // 创建确认框容器
    const container = document.createElement('div')
    container.setAttribute('data-confirm-component', 'true')
    document.body.appendChild(container)

    // 动态创建并挂载组件
    return new Promise((resolve, reject) => {
      import('vue').then(({ createApp, ref: refVue, reactive: reactiveVue, onUnmounted }) => {
        const ConfirmComponent = {
          setup() {
            const visible = refVue(true)

            const iconMap = {
              success: { icon: ['fas', 'check'], bg: 'bg-green-100', iconColor: 'text-green-600', btnColor: 'bg-green-600 hover:bg-green-700' },
              warning: { icon: ['fas', 'exclamation-triangle'], bg: 'bg-yellow-100', iconColor: 'text-yellow-600', btnColor: 'bg-yellow-600 hover:bg-yellow-700' },
              danger: { icon: ['fas', 'trash'], bg: 'bg-red-100', iconColor: 'text-red-600', btnColor: 'bg-red-600 hover:bg-red-700' },
              info: { icon: ['fas', 'info'], bg: 'bg-blue-100', iconColor: 'text-blue-600', btnColor: 'bg-blue-600 hover:bg-blue-700' }
            }

            const currentIcon = iconMap[type] || iconMap.info

            const handleConfirm = () => {
              visible.value = false
              setTimeout(() => {
                container.remove()
                resolve(true)
              }, 300)
            }

            const handleCancel = () => {
              visible.value = false
              setTimeout(() => {
                container.remove()
                resolve(false)
              }, 300)
            }

            onUnmounted(() => {
              container.remove()
            })

            return {
              visible,
              title,
              message,
              confirmText,
              cancelText,
              currentIcon,
              handleConfirm,
              handleCancel
            }
          },
          template: `
            <teleport to="body">
              <transition name="modal">
                <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center">
                  <div class="absolute inset-0 bg-black/50" @click="handleCancel" />
                  <div class="relative bg-white rounded-lg shadow-xl w-[400px] max-w-[90%] p-6">
                    <div class="flex items-start gap-4">
                      <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center" :class="currentIcon.bg">
                        <font-awesome-icon :icon="currentIcon.icon" class="text-xl" :class="currentIcon.iconColor" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ title }}</h3>
                        <p class="text-gray-600 text-base">{{ message }}</p>
                      </div>
                    </div>
                    <div class="flex justify-end gap-3 mt-6">
                      <button
                        class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        @click="handleCancel"
                      >
                        {{ cancelText }}
                      </button>
                      <button
                        class="px-4 py-2 text-white rounded-lg transition-colors"
                        :class="currentIcon.btnColor"
                        @click="handleConfirm"
                      >
                        {{ confirmText }}
                      </button>
                    </div>
                  </div>
                </div>
              </transition>
            </teleport>
          `
        }

        const app = createApp(ConfirmComponent)

        // 注册 FontAwesome 图标
        import('@fortawesome/fontawesome-svg-core').then(({ library }) => {
          import('@fortawesome/free-solid-svg-icons').then(icons => {
            library.add(
              icons.faCheck,
              icons.faExclamationTriangle,
              icons.faTrash,
              icons.faInfo
            )
            import('@fortawesome/vue-fontawesome').then(({ FontAwesomeIcon }) => {
              app.component('font-awesome-icon', FontAwesomeIcon)
              app.mount(container)
            })
          })
        })
      })
    })
  }

  return {
    showConfirm
  }
}
