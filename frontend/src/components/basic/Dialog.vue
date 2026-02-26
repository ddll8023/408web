<template>
  <teleport to="body">
    <transition name="dialog-fade">
      <dialog
        v-if="visible"
        class="fixed inset-0 z-50 flex items-start justify-center w-full h-full m-0 p-0 bg-transparent"
        :open="visible"
        @click.self="handleBackdropClick"
      >
        <!-- 遮罩层 -->
        <div
          class="fixed inset-0 bg-black/50 transition-opacity"
          @click="handleBackdropClick"
        />

        <!-- 弹窗主体 -->
        <div
          class="relative z-10 bg-white rounded-lg shadow-xl overflow-hidden"
          :class="containerClass"
          :style="containerStyle"
        >
          <!-- 头部 -->
          <div v-if="title || $slots.title" class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <slot name="title">
              <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
            </slot>
            <button
              class="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-gray-100"
              @click="handleClose"
              aria-label="关闭"
            >
                            <font-awesome-icon :icon="['fas', 'times']" class="text-lg" />
            </button>
          </div>

          <!-- 内容区 -->
          <div class="overflow-y-auto px-6 py-4" :style="contentStyle">
            <div v-if="loading" class="flex items-center justify-center p-8">
                            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-primary-600" />
              <span class="ml-3 text-gray-500">加载中...</span>
            </div>
            <slot v-else />
          </div>

          <!-- 底部 -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <slot name="footer" />
          </div>
        </div>
      </dialog>
    </transition>
  </teleport>
</template>

<script setup>
import { computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '86%'
  },
  maxWidth: {
    type: String,
    default: '1200px'
  },
  top: {
    type: String,
    default: 'calc(60px + 24px)'  // 导航栏60px + 额外边距24px
  },
  loading: {
    type: Boolean,
    default: false
  },
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  closeOnPressEscape: {
    type: Boolean,
    default: true
  },
  destroyOnClose: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:visible', 'close'])

// 容器样式
const containerClass = computed(() => {
  return {
    'w-full': true
  }
})

const containerStyle = computed(() => ({
  width: props.width,
  maxWidth: props.maxWidth,
  marginTop: props.top
}))

const contentStyle = computed(() => ({
  maxHeight: `calc(100vh - ${props.top} - 140px)`
}))

// 关闭弹窗
const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

// 点击遮罩层关闭
const handleBackdropClick = () => {
  if (props.closeOnClickModal) {
    handleClose()
  }
}

// 键盘事件
const handleKeydown = (e) => {
  if (e.key === 'Escape' && props.visible && props.closeOnPressEscape) {
    handleClose()
  }
}

// 监听 visible 变化，处理 body 滚动锁
watch(() => props.visible, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
dialog[open] {
  display: flex;
}

/* 过渡动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .bg-white,
.dialog-fade-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.dialog-fade-enter-from .bg-white,
.dialog-fade-leave-to .bg-white {
  transform: scale(0.95);
}
</style>
