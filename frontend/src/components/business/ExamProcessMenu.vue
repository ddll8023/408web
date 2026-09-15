<!-- 真题过程图片菜单：提供上传入口和独立的过程图片查看弹窗。 -->
<template>
  <Dropdown
    trigger="click"
    :disabled="isBusy"
    menu-class="exam-process-dropdown"
    @command="handleCommand"
  >
    <template #trigger>
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', 'pencil']"
        :loading="uploading"
      >
        过程
      </CustomButton>
    </template>

    <template #dropdown>
      <DropdownItem v-if="props.isAdmin" command="upload">
        <font-awesome-icon :icon="['fas', 'upload']" class="mr-2" aria-hidden="true" />
        上传图片
      </DropdownItem>
      <DropdownItem command="view">
        <font-awesome-icon :icon="['fas', 'eye']" class="mr-2" aria-hidden="true" />
        查看图片
      </DropdownItem>
    </template>
  </Dropdown>

  <input
    ref="fileInput"
    type="file"
    class="hidden"
    accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
    multiple
    @change="handleFileChange"
  />

  <ExamProcessDialog
    v-model:visible="dialogVisible"
    :title="dialogTitle"
    :images="images"
    :loading="loading"
    :saving="saving"
    :deleting-image-id="deletingImageId"
    :error="loadError"
    :is-admin="props.isAdmin"
    @retry="loadImages"
    @delete="handleDelete"
    @reorder="handleReorder"
  />
</template>

<script setup lang="ts">
/**
 * 真题过程图片菜单。
 * 负责局部请求状态和管理员操作，不改变真题主体内容及答案状态。
 */
import { computed, ref } from 'vue'
import type { ExamProcessImage, ExamQuestion } from '@/types'
import {
  deleteExamProcessImage,
  listExamProcessImages,
  reorderExamProcessImages,
  uploadExamProcessImage,
} from '@/api/examProcessImage'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import ExamProcessDialog from '@/components/business/ExamProcessDialog.vue'

interface Props {
  exam: ExamQuestion
  isAdmin?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isAdmin: false,
})

const { showConfirm } = useConfirm()
const { showToast } = useToast()

const fileInput = ref<HTMLInputElement | null>(null)
const dialogVisible = ref(false)
const images = ref<ExamProcessImage[]>([])
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const deletingImageId = ref<number | null>(null)
const loadError = ref('')
let requestVersion = 0

const dialogTitle = computed(() => {
  const questionNumber = props.exam.questionNumber == null ? '?' : props.exam.questionNumber
  return `${props.exam.year}年第${questionNumber}题 · 过程图片`
})

const isBusy = computed(() => {
  return uploading.value || loading.value || saving.value || deletingImageId.value !== null
})

const loadImages = async () => {
  const currentVersion = ++requestVersion
  loading.value = true
  loadError.value = ''

  try {
    const response = await listExamProcessImages(props.exam.id)
    if (currentVersion !== requestVersion) return

    if (response.code === 200) {
      images.value = response.data || []
      return
    }

    loadError.value = response.message || '加载过程图片失败'
  } catch (error) {
    if (currentVersion !== requestVersion) return
    loadError.value = '加载过程图片失败，请重试'
    console.error('加载过程图片失败:', error)
  } finally {
    if (currentVersion === requestVersion) loading.value = false
  }
}

const openViewer = () => {
  dialogVisible.value = true
  void loadImages()
}

const handleCommand = (command: string) => {
  if (command === 'upload') {
    fileInput.value?.click()
    return
  }

  if (command === 'view') {
    openViewer()
  }
}

const handleFileChange = async (event: Event) => {
  const input = event.target
  if (!(input instanceof HTMLInputElement)) return

  const files = Array.from(input.files || [])
  input.value = ''
  if (files.length === 0) return

  uploading.value = true
  let successCount = 0
  let failureCount = 0

  try {
    for (const file of files) {
      try {
        const response = await uploadExamProcessImage(props.exam.id, file)
        if (response.code === 200 && response.data) {
          images.value = [...images.value, response.data]
          successCount += 1
        } else {
          failureCount += 1
        }
      } catch (error) {
        failureCount += 1
        console.error('上传过程图片失败:', error)
      }
    }
  } finally {
    uploading.value = false
  }

  if (successCount > 0 && failureCount > 0) {
    showToast(`已上传 ${successCount} 张，${failureCount} 张失败`, 'warning')
  } else if (successCount > 0) {
    showToast(`过程图片上传成功，共 ${successCount} 张`, 'success')
  } else {
    showToast('过程图片上传失败', 'error')
  }
}

const handleDelete = async (image: ExamProcessImage) => {
  const confirmed = await showConfirm({
    title: '删除过程图片',
    message: '删除后图片将从该真题的过程展示中移除，是否继续？',
    type: 'warning',
  })
  if (!confirmed) return

  deletingImageId.value = image.id
  try {
    const response = await deleteExamProcessImage(props.exam.id, image.id)
    if (response.code === 200) {
      images.value = images.value.filter(item => item.id !== image.id)
      showToast('过程图片已删除', 'success')
    } else {
      showToast(response.message || '删除过程图片失败', 'error')
    }
  } catch (error) {
    showToast('删除过程图片失败', 'error')
    console.error('删除过程图片失败:', error)
  } finally {
    deletingImageId.value = null
  }
}

const handleReorder = async (imageIds: number[]) => {
  if (saving.value) return

  saving.value = true
  try {
    const response = await reorderExamProcessImages(props.exam.id, imageIds)
    if (response.code === 200 && response.data) {
      images.value = response.data
    } else {
      showToast(response.message || '保存图片顺序失败', 'error')
    }
  } catch (error) {
    showToast('保存图片顺序失败', 'error')
    console.error('保存过程图片顺序失败:', error)
  } finally {
    saving.value = false
  }
}
</script>
