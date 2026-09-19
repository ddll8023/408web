<!-- 真题过程图片弹窗：独立展示图片，不参与题干和答案渲染。 -->
<template>
  <Dialog
    :visible="props.visible"
    :title="props.title"
    aria-label="真题过程图片"
    width="min(92vw, 1080px)"
    max-width="1080px"
    :loading="props.loading"
    @update:visible="emit('update:visible', $event)"
  >
    <div v-if="props.error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span>{{ props.error }}</span>
        <CustomButton size="sm" type="text-danger" @click="emit('retry')">重新加载</CustomButton>
      </div>
    </div>

    <div v-else-if="props.images.length === 0" class="flex min-h-[220px] flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-line bg-surface px-6 py-10 text-center text-sm text-gray-500">
      <font-awesome-icon :icon="['fas', 'eye']" class="text-2xl text-[#B79B75]" aria-hidden="true" />
      <p class="m-0">暂时没有过程图片</p>
      <span v-if="props.isAdmin" class="text-xs text-gray-400">可通过“过程 → 上传图片”添加讲解图片</span>
    </div>

    <div v-else class="flex flex-col gap-5">
      <div v-if="props.saving" class="text-xs text-gray-500" role="status" aria-live="polite">
        正在保存图片顺序...
      </div>

      <figure
        v-for="(image, index) in props.images"
        :key="image.id"
        class="overflow-hidden rounded-xl border border-line bg-surface"
      >
        <figcaption class="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
          <span class="text-sm font-medium text-[#6F5638]">第 {{ index + 1 }} / {{ props.images.length }} 张</span>

          <div v-if="props.isAdmin" class="flex items-center gap-1">
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-[#DCCBB5] bg-white text-accent transition-colors hover:bg-[#F5EFE6] focus:outline-none focus:ring-2 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="props.saving || props.deletingImageId !== null || index === 0"
              :aria-label="`过程图片第 ${index + 1} 张上移`"
              @click="moveImage(index, -1)"
            >
              <font-awesome-icon :icon="['fas', 'arrow-up']" aria-hidden="true" />
            </button>
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-[#DCCBB5] bg-white text-accent transition-colors hover:bg-[#F5EFE6] focus:outline-none focus:ring-2 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="props.saving || props.deletingImageId !== null || index === props.images.length - 1"
              :aria-label="`过程图片第 ${index + 1} 张下移`"
              @click="moveImage(index, 1)"
            >
              <font-awesome-icon :icon="['fas', 'arrow-down']" aria-hidden="true" />
            </button>
            <CustomButton
              type="text-danger"
              size="sm"
              :loading="props.deletingImageId === image.id"
              :disabled="props.saving || (props.deletingImageId !== null && props.deletingImageId !== image.id)"
              @click="emit('delete', image)"
            >
              删除
            </CustomButton>
          </div>
        </figcaption>

        <div class="flex min-h-[180px] items-center justify-center overflow-auto bg-white p-3 md:p-5">
          <img
            :src="getImageUrl(image.url)"
            :alt="`第 ${index + 1} 张过程图片`"
            class="max-h-[68vh] max-w-full object-contain"
          />
        </div>
      </figure>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * 真题过程图片弹窗。
 * 只负责图片展示和排序操作，不负责题目内容、答案或文件上传。
 */
import type { ExamProcessImage } from '@/types'
import Dialog from '@/components/basic/Dialog.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import { getImageUrl } from '@/api/upload'

interface Props {
  visible: boolean
  title: string
  images: ExamProcessImage[]
  loading?: boolean
  saving?: boolean
  deletingImageId?: number | null
  error?: string
  isAdmin?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  saving: false,
  deletingImageId: null,
  error: '',
  isAdmin: false,
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
  retry: []
  delete: [image: ExamProcessImage]
  reorder: [imageIds: number[]]
}>()

const moveImage = (index: number, offset: -1 | 1) => {
  if (props.saving || props.deletingImageId !== null) return

  const targetIndex = index + offset
  if (targetIndex < 0 || targetIndex >= props.images.length) return

  const nextImages = [...props.images]
  const [movedImage] = nextImages.splice(index, 1)
  if (!movedImage) return

  nextImages.splice(targetIndex, 0, movedImage)
  emit('reorder', nextImages.map(image => image.id))
}
</script>
