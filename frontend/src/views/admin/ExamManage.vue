<template>
  <div class="max-w-[1400px] mx-auto px-4 py-6 min-h-[calc(100vh-60px)]">
    <el-card class="shadow-sm">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">真题管理</h2>
          <div class="flex gap-2">
            <CustomButton type="primary" @click="handleAdd">
              <el-icon style="margin-right: 6px"><Plus /></el-icon>
              新增真题
            </CustomButton>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="mb-6 p-4 bg-[#efefef] rounded">
        <el-form inline>
          <el-form-item label="年份">
            <el-input-number
              v-model="filters.year"
              :min="2000"
              :max="2099"
              placeholder="请选择年份"
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="科目">
            <el-select
              v-model="filters.subjectId"
              placeholder="请选择科目"
              clearable
              style="width: 150px"
              @change="handleSubjectChange"
            >
              <el-option
                v-for="subject in subjectOptions"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <InputSelect
              v-model="filters.category"
              :options="categoryOptions"
              placeholder="请选择或输入分类"
              style="width: 180px"
              :disabled="!filters.subjectId"
            />
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索题目内容"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="filters.noCategory">仅显示无分类</el-checkbox>
          </el-form-item>
          <el-form-item>
            <CustomButton type="primary" @click="handleSearch">查询</CustomButton>
            <CustomButton style="margin-left: 16px" @click="handleReset">重置</CustomButton>
          </el-form-item>
        </el-form>
      </div>

      <!-- 真题列表表格 -->
      <el-table :data="exams" stripe style="width: 100%" v-loading="loading" @sort-change="handleSortChange">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="year" label="年份" width="100" sortable="custom" />
        <el-table-column prop="questionNumber" label="题号" width="80" sortable="custom" />
        <el-table-column label="题型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'">
              {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" show-overflow-tooltip min-width="250">
          <template #default="{ row }">
            <span class="cursor-pointer hover:!text-[#FBF7F2]">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="cat in (Array.isArray(row.category) ? row.category : [])"
              :key="cat"
              size="small"
              type="info"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ cat }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="难度" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.difficulty" :type="getDifficultyType(row.difficulty)">
              {{ getDifficultyLabel(row.difficulty) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="更新时间" width="160" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.updateTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <CustomButton type="text" size="sm" @click="handleView(row)">查看</CustomButton>
            <CustomButton type="text-primary" size="sm" @click="handleEdit(row)">编辑</CustomButton>
            <CustomButton
              type="text-danger"
              size="sm"
              :loading="row.deleteLoading"
              @click="handleDelete(row)"
            >
              删除
            </CustomButton>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-6">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadExamList"
          @Size-change="loadExamList"
        />
      </div>
    </el-card>

    <el-backtop
      :right="32"
      :bottom="32"
    >
      <div class="w-10 h-10 rounded-full bg-[#8B6F47] flex items-center justify-center text-white shadow-lg">
        <el-icon><ArrowUp /></el-icon>
      </div>
    </el-backtop>

    <!-- 编辑弹窗 -->
    <ExamEditDialog
      v-model:visible="editDialogVisible"
      :exam-id="editingExamId"
      @success="handleEditSuccess"
    />
  </div>
</template>

<script setup>
/**
 * 真题管理页面
 * 功能：真题的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+筛选实现
 * 使用 useAdminTable composable 复用公共逻辑
 */
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowUp } from '@element-plus/icons-vue'
import { getExamList, deleteExam, getExamCategoriesBySubject } from '@/api/exam'
import CustomButton from '@/components/basic/CustomButton.vue'
import InputSelect from '@/components/basic/InputSelect.vue'
import ExamEditDialog from '@/components/business/ExamEditDialog.vue'
import { useAdminTable } from '@/composables/useAdminTable'

const route = useRoute()

// 使用公共管理表格逻辑
const {
  loading,
  subjectOptions,
  categoryOptions,
  sorting,
  pagination,
  subjectMap,
  getDifficultyLabel,
  getDifficultyType,
  formatDateTime,
  loadSubjectOptions,
  loadSubjectCategoryOptions,
  handleSortChange: baseSortChange,
  clearUrlKeyword,
  getUrlKeyword
} = useAdminTable()

// 编辑弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref(null)

// 真题列表
const exams = ref([])

// 筛选条件
const filters = reactive({
  year: null,
  subjectId: null,
  category: '',
  keyword: '',
  noCategory: false
})

/**
 * 加载真题列表
 */
const loadExamList = async () => {
  loading.value = true
  try {
    const response = await getExamList({
      page: pagination.page,
      size: pagination.size,
      year: filters.year || undefined,
      subjectId: filters.subjectId || undefined,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      noCategory: filters.noCategory || undefined,
      sortField: sorting.sortField || undefined,
      sortOrder: sorting.sortOrder || undefined
    })
    
    if (response.code === 200) {
      exams.value = response.data.data || []
      pagination.total = response.data.total || 0
    } else {
      ElMessage.error(response.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载真题列表失败')
    console.error('加载真题列表失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 科目筛选变更
 */
const handleSubjectChange = async (subjectId) => {
  filters.subjectId = subjectId || null
  filters.category = ''
  await loadSubjectCategoryOptions(filters.subjectId, getExamCategoriesBySubject)
}

/**
 * 处理查询
 */
const handleSearch = () => {
  pagination.page = 1
  loadExamList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  filters.year = null
  filters.subjectId = null
  filters.category = ''
  filters.keyword = ''
  filters.noCategory = false
  categoryOptions.value = []
  sorting.sortField = null
  sorting.sortOrder = null
  pagination.page = 1
  clearUrlKeyword()
  loadExamList()
}

/**
 * 处理排序变化（使用公共逻辑）
 */
const handleSortChange = (sortInfo) => {
  baseSortChange(sortInfo, loadExamList)
}

/**
 * 处理新增（打开编辑弹窗，不传ID表示新建）
 */
const handleAdd = () => {
  editingExamId.value = null
  editDialogVisible.value = true
}

/**
 * 处理查看（在新标签页打开题目浏览页）
 * 构建URL: /exam/classify?subject=科目名称#exam-题目ID
 */
const handleView = (row) => {
  const subjectName = subjectMap.value[row.subjectId]
  if (!subjectName) {
    ElMessage.warning('无法获取题目所属科目信息')
    return
  }
  // 构建URL，使用hash定位到具体题目卡片
  const url = `/exam/classify?subject=${encodeURIComponent(subjectName)}#exam-${row.id}`
  window.open(url, '_blank')
}

/**
 * 处理编辑（打开编辑弹窗）
 */
const handleEdit = (row) => {
  editingExamId.value = row.id
  editDialogVisible.value = true
}

/**
 * 编辑成功回调
 */
const handleEditSuccess = () => {
  loadExamList()
}

/**
 * 处理删除
 */
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除真题"${row.title || row.year + '年 第' + row.questionNumber + '题'}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    row.deleteLoading = true
    const response = await deleteExam(row.id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      // 重新加载列表
      loadExamList()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除失败:', error)
    }
  } finally {
    if (row) row.deleteLoading = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSubjectOptions()
  // 从URL获取keyword参数
  const urlKeyword = getUrlKeyword()
  if (urlKeyword) {
    filters.keyword = urlKeyword
  }
  loadExamList()
})

// 监听路由变化，支持导航栏搜索跳转
watch(() => route.query.keyword, (newKeyword) => {
  if (newKeyword !== undefined) {
    filters.keyword = newKeyword || ''
    pagination.page = 1
    loadExamList()
  }
})
</script>

<style scoped>
/**
 * 真题管理页面样式
 * 大部分样式已迁移到Tailwind类
 */

/* 响应式布局 */
@media (max-width: 768px) {
  .max-w-\[1400px\] {
    padding: 16px 8px;
  }

  .flex.justify-end {
    overflow-x: auto;
  }
}
</style>

