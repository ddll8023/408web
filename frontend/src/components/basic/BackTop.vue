<template>
  <transition name="fade">
    <button
      ref="buttonRef"
      v-show="visible"
      type="button"
      class="fixed z-50 w-10 h-10 rounded-full bg-[#8B6F47] flex items-center justify-center text-white shadow-[0_4px_12px_rgba(0,0,0,0.25)] transition-opacity hover:bg-[#7A5F3E] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47] focus-visible:ring-offset-2"
      :style="{ right: right + 'px', bottom: bottom + 'px' }"
      aria-label="回到顶部"
      @click="scrollToTop"
    >
      <slot>
        <font-awesome-icon :icon="['fas', 'arrow-up']" aria-hidden="true" />
      </slot>
    </button>
  </transition>
</template>

<script setup lang="ts">
/**
 * 回到顶部组件
 */
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  right: {
    type: Number,
    default: 32
  },
  bottom: {
    type: Number,
    default: 32
  },
  visibilityHeight: {
    type: Number,
    default: 300
  }
})

const visible = ref(false)
const buttonRef = ref<HTMLButtonElement | null>(null)
let scrollTarget: Window | HTMLElement = window

const findScrollTarget = (): Window | HTMLElement => {
  let parent = buttonRef.value?.parentElement || null
  while (parent) {
    const style = window.getComputedStyle(parent)
    if (/(auto|scroll|overlay)/.test(style.overflowY) || /(auto|scroll|overlay)/.test(style.overflow)) {
      return parent
    }
    parent = parent.parentElement
  }
  return window
}

const handleScroll = () => {
  const scrollTop = scrollTarget === window ? window.scrollY : scrollTarget.scrollTop
  visible.value = scrollTop > props.visibilityHeight
}

const scrollToTop = () => {
  scrollTarget.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  scrollTarget = findScrollTarget()
  scrollTarget.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
})

onUnmounted(() => {
  scrollTarget.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
