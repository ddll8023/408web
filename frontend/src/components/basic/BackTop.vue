<template>
  <transition name="fade">
    <button
      v-show="visible"
      class="fixed z-50 w-10 h-10 rounded-full bg-[#8B6F47] flex items-center justify-center text-white shadow-[0_4px_12px_rgba(0,0,0,0.25)] transition-opacity hover:bg-[#7A5F3E] focus:outline-none"
      :style="{ right: right + 'px', bottom: bottom + 'px' }"
      @click="scrollToTop"
    >
      <font-awesome-icon :icon="['fas', 'arrow-up']" />
    </button>
  </transition>
</template>

<script setup>
/**
 * 回到顶部组件
 */
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
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

const handleScroll = () => {
  visible.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
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
