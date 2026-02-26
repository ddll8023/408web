<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <CustomCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">图片资源管理</h2>
          <div class="flex gap-2">
            <CustomButton type="primary" @click="loadImages" :loading="loading">
              <font-awesome-icon :icon="['fas', 'rotate']" class="mr-1" />
              刷新
            </CustomButton>
            <CustomButton type="danger" @click="handleDeleteUnreferenced" :loading="cleanupLoading">
              <font-awesome-icon :icon="['fas', 'trash-can']" class="mr-1" />
              删除未引用
            </CustomButton>
          </div>
        </div>
      </template>

      <!-- 切换开关 -->
      <div class="mb-4 flex justify-end items-center gap-2">
        <span class="text-sm text-gray-600">仅显示未引用</span>
        <Switch v-model="onlyUnreferenced" @change="loadImages" />
      </div>

      <!-- 表格 -->
      <Table :data="images" :columns="tableColumns" :loading="loading">
        <!-- 预览列 -->
        <template #preview="{ row }">
          <img
            v-if="row.url"
            :src="getFullUrl(row.url)"
            class="w-[100px] h-[100px] object-cover rounded cursor-pointer hover:opacity-80 transition-opacity"
            @click="openPreview(row.url)"
          />
        </template>

        <!-- 大小列 -->
        <template #size="{ row }">
          {{ formatSize(row.size) }}
        </template>

        <!-- 时间列 -->
        <template #last_modified="{ row }">
          {{ formatTime(row.last_modified) }}
        </template>

        <!-- 引用题目列 -->
        <template #exams="{ row }">
          <div v-if="row.exams && row.exams.length" class="flex flex-wrap gap-1">
            <Tag v-for="exam in row.exams" :key="exam.id" type="info">
              {{ formatExamLabel(exam) }}
            </Tag>
          </div>
          <span v-else class="text-gray-400 text-sm">
            <font-awesome-icon :icon="['fas', 'link-slash']" class="mr-1" />
            未引用
          </span>
        </template>

        <!-- 操作列 -->
        <template #action="{ row }">
          <CustomButton
            type="text-danger"
            size="sm"
            :loading="row.deleteLoading"
            @click="handleDelete(row)"
          >
            <font-awesome-icon :icon="['fas', 'trash']" class="mr-1" />
            删除
          </CustomButton>
        </template>
      </Table>
    </CustomCard>

    <!-- 图片预览弹窗 -->
    <Teleport to="body">
      <div
        v-if="previewVisible"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80"
        @click="closePreview"
      >
        <img :src="previewUrl" class="max-w-[90%] max-h-[90%] object-contain" />
      </div>
    </Teleport>

    <!-- Confirm 组件 -->
    <Confirm ref="confirmRef" />
  </div>
</template>

<script setup>
/**
 * 图片资源管理页面
 * 功能描述：管理后台图片资源列表展示、删除未引用图片
 * 依赖组件：CustomButton, CustomCard, Switch, Table, Tag, Confirm
 */

import { ref, onMounted } from 'vue'
import { getImageList, deleteImage, deleteUnreferencedImages, getImageUrl } from '@/api/upload'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import Switch from '@/components/basic/Switch.vue'
import Table from '@/components/basic/Table.vue'
import Tag from '@/components/basic/Tag.vue'
import Confirm from '@/components/basic/Confirm.vue'

const images = ref([])
const loading = ref(false)
const onlyUnreferenced = ref(false)
const cleanupLoading = ref(false)

// Confirm 组件引用
const confirmRef = ref(null)

// 图片预览状态
const previewVisible = ref(false)
const previewUrl = ref('')

// 表格列配置
const tableColumns = [
  { prop: 'preview', label: '预览', width: '140px', align: 'center' },
  { prop: 'filename', label: '文件名', minWidth: '220px' },
  { prop: 'size', label: '大小', width: '120px', align: 'center' },
  { prop: 'last_modified', label: '最后修改时间', width: '200px', align: 'center' },
  { prop: 'exams', label: '引用题目', minWidth: '240px' },
  { prop: 'action', label: '操作', width: '120px', align: 'center' }
]

// Toast 提示函数（替代 ElMessage）
const showToast = (message, type = 'success') => {
  const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500'
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-opacity duration-300`
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    toast.classList.add('opacity-0')
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}

// 打开预览
const openPreview = (url) => {
  previewUrl.value = getFullUrl(url)
  previewVisible.value = true
}

// 关闭预览
const closePreview = () => {
  previewVisible.value = false
  previewUrl.value = ''
}

const loadImages = async () => {
  loading.value = true
  try {
    const res = await getImageList({ only_unreferenced: onlyUnreferenced.value })
    if (res.code === 200) {
      images.value = (res.data || []).map(item => ({ ...item, deleteLoading: false }))
    } else {
      showToast(res.message || '加载失败', 'error')
    }
  } catch (error) {
    showToast('加载图片列表失败', 'error')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const getFullUrl = (url) => {
  if (!url) return ''
  return getImageUrl(url)
}

const formatSize = (size) => {
  if (!size || size <= 0) return '-'
  const kb = size / 1024
  if (kb < 1024) return kb.toFixed(1) + ' KB'
  const mb = kb / 1024
  return mb.toFixed(2) + ' MB'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatExamLabel = (exam) => {
  if (!exam) return ''
  if (exam.year && exam.questionNumber) {
    return `${exam.year}年第${exam.questionNumber}题`
  }
  if (exam.title) {
    return exam.title
  }
  return `ID: ${exam.id}`
}

const handleDelete = async (row) => {
  confirmRef.value?.show(
    {
      title: '提示',
      message: `确定要删除图片「${row.filename}」吗？`,
      type: 'warning'
    },
    async () => {
      // 确认回调
      row.deleteLoading = true
      try {
        const res = await deleteImage(row.filename)
        if (res.code === 200) {
          showToast('删除成功', 'success')
          loadImages()
        } else {
          showToast(res.message || '删除失败', 'error')
        }
      } catch (error) {
        showToast('删除失败', 'error')
        console.error(error)
      } finally {
        row.deleteLoading = false
      }
    }
  )
}

const handleDeleteUnreferenced = async () => {
  confirmRef.value?.show(
    {
      title: '警告',
      message: '将删除所有当前未被任何题目（真题、模拟题）引用的图片，此操作不可恢复，是否继续？',
      type: 'danger'
    },
    async () => {
      // 确认回调
      cleanupLoading.value = true
      try {
        const res = await deleteUnreferencedImages()
        if (res.code === 200) {
          const count = typeof res.data === 'number' ? res.data : 0
          showToast(`已删除 ${count} 张未引用图片`, 'success')
          loadImages()
        } else {
          showToast(res.message || '删除未引用图片失败', 'error')
        }
      } catch (error) {
        showToast('删除未引用图片失败', 'error')
        console.error(error)
      } finally {
        cleanupLoading.value = false
      }
    }
  )
}

onMounted(() => {
  loadImages()
})
</script>

<style scoped>
/**
 * 图片资源管理页面样式
 * 已迁移至 Tailwind CSS
 */
</style>
