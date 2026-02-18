<template>
  <div class="chapter-manage-container">
    <el-card class="manage-card">
      <template #header>
        <div class="card-header">
          <h2>章节管理</h2>
          <CustomButton type="primary" @click="handleAdd(null)">
            <el-icon style="margin-right: 6px"><Plus /></el-icon>
            新增一级章节
          </CustomButton>
        </div>
      </template>

      <!-- 科目选择 -->
      <div class="subject-selector">
        <el-select
          v-model="selectedSubjectId"
          placeholder="请选择科目"
          style="width: 300px"
          @change="handleSubjectChange"
        >
          <el-option
            v-for="subject in subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
      </div>

      <!-- 章节树形表格 -->
      <el-table
        v-if="selectedSubjectId"
        v-loading="loading"
        :data="chapters"
        row-key="id"
        stripe
        style="width: 100%; margin-top: 16px"
        default-expand-all
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column prop="name" label="章节名称" min-width="200" />
        <el-table-column prop="orderNum" label="排序序号" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <CustomButton 
              v-if="!row.parentId" 
              type="text"
              size="small"
              @click="handleAdd(row.id)"
            >
              添加子章节
            </CustomButton>
            <CustomButton type="text-primary" size="small" @click="handleEdit(row)">编辑</CustomButton>
            <CustomButton 
              type="text"
              size="small"
              :loading="row.statusLoading"
              @click="handleToggleStatus(row)"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </CustomButton>
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

      <el-empty v-else description="请先选择科目" />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="所属科目">
          <el-input :value="getSubjectName()" disabled />
        </el-form-item>

        <el-form-item v-if="form.parentId" label="父章节">
          <el-input :value="getParentChapterName()" disabled />
        </el-form-item>

        <el-form-item label="章节名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入章节名称（如：线性表、栈与队列等）"
            maxlength="200"
            clearable
          />
        </el-form-item>

        <el-form-item label="排序序号" prop="orderNum">
          <el-input-number
            v-model="form.orderNum"
            :min="0"
            :max="9999"
            placeholder="数字越小越靠前"
          />
          <div class="form-tip">排序序号决定章节显示顺序</div>
        </el-form-item>

        <el-form-item label="是否启用" prop="enabled">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <CustomButton @click="dialogVisible = false">取消</CustomButton>
        <CustomButton type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </CustomButton>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 章节管理页面
 * 功能：章节的CRUD操作，支持两级树形结构（仅ADMIN可访问）
 * 遵循KISS原则：树形表格+对话框实现
 * 
 * Source: Element Plus Table & Dialog 组件
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getAllSubjects } from '@/api/subject'
import { 
  getChapterTree, 
  createChapter, 
  updateChapter, 
  deleteChapter 
} from '@/api/chapter'
import CustomButton from '@/components/basic/CustomButton.vue'

// 科目列表
const subjects = ref([])

// 选中的科目ID
const selectedSubjectId = ref(null)

// 章节树形数据
const chapters = ref([])

// 对话框显示状态
const dialogVisible = ref(false)

// 对话框模式（add/edit）
const dialogMode = ref('add')

// 提交加载状态
const submitLoading = ref(false)

// 表格加载状态
const loading = ref(false)

// 表单引用
const formRef = ref(null)

// 表单数据
const form = reactive({
  id: null,
  subjectId: null,
  parentId: null,
  name: '',
  orderNum: 0,
  enabled: true
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入章节名称', trigger: 'blur' },
    { max: 200, message: '名称长度不能超过200字符', trigger: 'blur' }
  ],
  orderNum: [
    { required: true, message: '请输入排序序号', trigger: 'blur' }
  ]
}

// 对话框标题
const dialogTitle = computed(() => {
  if (dialogMode.value === 'add') {
    return form.parentId ? '新增子章节' : '新增一级章节'
  }
  return '编辑章节'
})

/**
 * 加载科目列表
 */
const loadSubjects = async () => {
  try {
    const response = await getAllSubjects()
    if (response.code === 200) {
      subjects.value = response.data || []
      // 默认选中第一个科目
      if (subjects.value.length > 0) {
        selectedSubjectId.value = subjects.value[0].id
        loadChapters()
      }
    } else {
      ElMessage.error(response.message || '加载科目列表失败')
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
    ElMessage.error('加载科目列表失败')
  }
}

/**
 * 加载章节树
 */
const loadChapters = async () => {
  if (!selectedSubjectId.value) {
    return
  }

  loading.value = true
  try {
    const response = await getChapterTree(selectedSubjectId.value)
    if (response.code === 200) {
      chapters.value = response.data || []
    } else {
      ElMessage.error(response.message || '加载章节列表失败')
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    ElMessage.error('加载章节列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 科目切换
 */
const handleSubjectChange = () => {
  loadChapters()
}

/**
 * 获取科目名称
 */
const getSubjectName = () => {
  const subject = subjects.value.find(s => s.id === form.subjectId)
  return subject ? subject.name : ''
}

/**
 * 获取父章节名称
 */
const getParentChapterName = () => {
  if (!form.parentId) {
    return ''
  }
  
  // 在章节列表中查找父章节
  const parent = chapters.value.find(c => c.id === form.parentId)
  return parent ? parent.name : ''
}

/**
 * 重置表单
 */
const resetForm = () => {
  form.id = null
  form.subjectId = selectedSubjectId.value
  form.parentId = null
  form.name = ''
  form.orderNum = 0
  form.enabled = true
  formRef.value?.clearValidate()
}

/**
 * 新增章节
 * @param {Number|null} parentId 父章节ID，null表示一级章节
 */
const handleAdd = (parentId) => {
  resetForm()
  form.parentId = parentId
  dialogMode.value = 'add'
  dialogVisible.value = true
}

/**
 * 编辑章节
 */
const handleEdit = (row) => {
  resetForm()
  form.id = row.id
  form.subjectId = row.subjectId
  form.parentId = row.parentId
  form.name = row.name
  form.orderNum = row.orderNum
  form.enabled = row.enabled
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  // 表单验证
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  submitLoading.value = true
  try {
    let response
    const data = {
      subjectId: form.subjectId,
      parentId: form.parentId,
      name: form.name,
      orderNum: form.orderNum,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      // 创建章节
      response = await createChapter(data)
    } else {
      // 更新章节
      data.id = form.id
      response = await updateChapter(form.id, data)
    }

    if (response.code === 200) {
      ElMessage.success(dialogMode.value === 'add' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      loadChapters()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(dialogMode.value === 'add' ? '创建失败' : '更新失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 切换启用/禁用状态
 */
const handleToggleStatus = async (row) => {
  const action = row.enabled ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确认${action}章节"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    row.statusLoading = true
    const response = await updateChapter(row.id, {
      id: row.id,
      subjectId: row.subjectId,
      parentId: row.parentId,
      name: row.name,
      orderNum: row.orderNum,
      enabled: !row.enabled
    })

    if (response.code === 200) {
      ElMessage.success(`${action}成功`)
      loadChapters()
    } else {
      ElMessage.error(response.message || `${action}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      ElMessage.error(`${action}失败`)
    }
  } finally {
    if (row) row.statusLoading = false
  }
}

/**
 * 删除章节
 */
const handleDelete = async (row) => {
  const hasChildren = row.children && row.children.length > 0
  const warningMsg = hasChildren
    ? `章节"${row.name}"包含子章节，删除后所有子章节也将被删除。确认删除吗？`
    : `确认删除章节"${row.name}"吗？`

  try {
    await ElMessageBox.confirm(warningMsg, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })

    row.deleteLoading = true
    const response = await deleteChapter(row.id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      loadChapters()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  } finally {
    if (row) row.deleteLoading = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSubjects()
})
</script>

<style scoped>
/**
 * 章节管理页面样式
 * 移除 SCSS，使用普通 CSS
 */
.chapter-manage-container {
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

.subject-selector {
  margin-bottom: 24px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .chapter-manage-container {
    padding: 16px 8px;
  }

  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .subject-selector :deep(.el-select) {
    width: 100% !important;
  }
}
</style>

