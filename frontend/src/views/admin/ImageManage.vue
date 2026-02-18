<template>
  <div class="image-manage-container">
    <el-card class="manage-card">
      <template #header>
        <div class="card-header">
          <h2>图片资源管理</h2>
          <div class="header-actions">
            <CustomButton type="primary" @click="loadImages" :loading="loading">刷新</CustomButton>
            <CustomButton type="danger" @click="handleDeleteUnreferenced" :loading="cleanupLoading">
              删除未引用
            </CustomButton>
          </div>
        </div>
      </template>

      <div class="filter-actions">
        <el-switch
          v-model="onlyUnreferenced"
          active-text="仅显示未引用"
          @change="loadImages"
        />
      </div>

      <el-table :data="images" stripe style="width: 100%" v-loading="loading">
        <el-table-column label="预览" width="140">
          <template #default="{ row }">
            <el-image
              v-if="row.url"
              :src="getFullUrl(row.url)"
              :preview-src-list="[getFullUrl(row.url)]"
              fit="cover"
              style="width: 100px; height: 100px"
            />
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column label="最后修改时间" width="200">
          <template #default="{ row }">
            {{ formatTime(row.lastModified) }}
          </template>
        </el-table-column>
        <!-- 引用题目列：仅显示信息，不提供跳转 -->
        <el-table-column label="引用题目" min-width="240">
          <template #default="{ row }">
            <template v-if="row.exams && row.exams.length">
              <el-space wrap>
                <el-tag
                  v-for="exam in row.exams"
                  :key="exam.id"
                  type="info"
                  size="small"
                >
                  {{ formatExamLabel(exam) }}
                </el-tag>
              </el-space>
            </template>
            <span v-else class="text-muted">未引用</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <CustomButton
              type="text-danger"
              size="small"
              :loading="row.deleteLoading"
              @click="handleDelete(row)"
            >
              删除
            </CustomButton>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getImageList, deleteImage, deleteUnreferencedImages, getImageUrl } from '@/api/upload'
import CustomButton from '@/components/basic/CustomButton.vue'

const images = ref([])
const loading = ref(false)
const onlyUnreferenced = ref(false)
const cleanupLoading = ref(false)

const loadImages = async () => {
  loading.value = true
  try {
    const res = await getImageList({ onlyUnreferenced: onlyUnreferenced.value })
    if (res.code === 200) {
      images.value = (res.data || []).map(item => ({ ...item, deleteLoading: false }))
    } else {
      ElMessage.error(res.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载图片列表失败')
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
  try {
    await ElMessageBox.confirm(`确定要删除图片「${row.filename}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    row.deleteLoading = true
    const res = await deleteImage(row.filename)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadImages()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  } finally {
    row.deleteLoading = false
  }
}

const handleDeleteUnreferenced = async () => {
  try {
    await ElMessageBox.confirm(
      '将删除所有当前未被任何题目（真题、模拟题）引用的图片，此操作不可恢复，是否继续？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleanupLoading.value = true
    const res = await deleteUnreferencedImages()
    if (res.code === 200) {
      const count = typeof res.data === 'number' ? res.data : 0
      ElMessage.success(`已删除 ${count} 张未引用图片`)
      loadImages()
    } else {
      ElMessage.error(res.message || '删除未引用图片失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除未引用图片失败')
      console.error(error)
    }
  } finally {
    cleanupLoading.value = false
  }
}

onMounted(() => {
  loadImages()
})
</script>

<style scoped>
/**
 * 图片资源管理页面样式
 * 移除 SCSS，使用普通 CSS
 */
.image-manage-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 16px;
  min-height: calc(100vh - 60px);
}

.manage-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h2 {
  margin: 0;
  font-size: 22px;
  color: #333;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-actions {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
