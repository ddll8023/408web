<!-- 响应式弹层：宽屏使用 Dialog，窄屏使用 BottomSheet，共用内容和底部操作插槽。 -->
<template>
  <Dialog
    v-if="isWide"
    :visible="visible"
    :title="title"
    :aria-label="ariaLabel"
    :width="width"
    :max-width="maxWidth"
    :top="top"
    :loading="loading"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :destroy-on-close="destroyOnClose"
    @update:visible="handleVisibleUpdate"
    @close="handleClose"
  >
    <template v-if="$slots.title" #title>
      <slot name="title" />
    </template>
    <slot v-if="!loading" />
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </Dialog>

  <BottomSheet
    v-else
    :visible="visible"
    :title="title"
    :aria-label="ariaLabel"
    :max-height="maxHeight"
    :close-on-backdrop="closeOnBackdrop"
    @update:visible="handleVisibleUpdate"
    @close="handleClose"
  >
    <template v-if="$slots.title" #header>
      <slot name="title" />
    </template>
    <div v-if="loading" class="flex items-center justify-center p-8" role="status" aria-live="polite">
      <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-accent" aria-hidden="true" />
      <span class="ml-3 text-gray-500">加载中...</span>
    </div>
    <slot v-else />
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </BottomSheet>
</template>

<script setup lang="ts">
/**
 * 响应式弹层包装。
 * 统一表单内容和操作插槽，避免业务页面分别维护桌面 Dialog 与窄屏 BottomSheet 两套结构。
 */
import Dialog from '@/components/basic/Dialog.vue'
import BottomSheet from '@/components/basic/BottomSheet.vue'
import { MEDIA_QUERIES } from '@/shared/responsive/breakpoints'
import { useMediaQuery } from '@/shared/responsive/useViewport'

interface Props {
  visible?: boolean
  title?: string
  ariaLabel?: string
  width?: string
  maxWidth?: string
  top?: string
  loading?: boolean
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  destroyOnClose?: boolean
  maxHeight?: string
  closeOnBackdrop?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  title: '',
  ariaLabel: '对话框',
  width: '86%',
  maxWidth: '1200px',
  top: 'calc(60px + 24px)',
  loading: false,
  closeOnClickModal: false,
  closeOnPressEscape: true,
  destroyOnClose: true,
  maxHeight: 'min(70dvh, 640px)',
  // 与现有 Dialog 默认行为保持一致，避免编辑表单误触遮罩后丢失内容。
  closeOnBackdrop: false,
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

const isWide = useMediaQuery(MEDIA_QUERIES.wide)

const handleVisibleUpdate = (value: boolean) => emit('update:visible', value)
const handleClose = () => emit('close')
</script>
