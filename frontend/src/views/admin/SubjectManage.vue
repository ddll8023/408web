<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <el-card class="shadow-sm">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">科目管理</h2>
          <CustomButton type="primary" @click="handleAdd">
            <el-icon style="margin-right: 6px"><Plus /></el-icon>
            新增科目
          </CustomButton>
        </div>
      </template>

      <!-- 科目列表表格 -->
      <el-table :data="subjects" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="科目编码" width="150" />
        <el-table-column prop="name" label="科目名称" width="200" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sortOrder" label="排序" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <CustomButton type="text-primary" size="small" @click="handleEdit(row)">编辑</CustomButton>
            <CustomButton 
              type="text"
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </CustomButton>
            <CustomButton type="text-danger" size="small" @click="handleDelete(row)">删除</CustomButton>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增科目' : '编辑科目'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="科目编码" prop="code">
          <el-input
            v-model="form.code"
            placeholder="请输入科目编码（如：data_structure）"
            maxlength="50"
            clearable
            :disabled="dialogMode === 'edit'"
          />
          <div class="text-xs text-[#999] mt-1">科目编码创建后不可修改</div>
        </el-form-item>

        <el-form-item label="科目名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入科目名称（如：数据结构）"
            maxlength="100"
            clearable
          />
        </el-form-item>

        <el-form-item label="科目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入科目描述（可选）"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="排序顺序" prop="sortOrder">
          <el-input-number
            v-model="form.sortOrder"
            :min="0"
            :max="9999"
            placeholder="数字越小越靠前"
          />
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
 * 科目管理页面
 * 功能：科目的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+对话框实现
 * 
 * Source: Element Plus Table & Dialog 组件
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { 
  getAllSubjects, 
  createSubject, 
  updateSubject, 
  deleteSubject 
} from '@/api/subject'
import CustomButton from '@/components/basic/CustomButton.vue'

// 科目列表
const subjects = ref([])

// 对话框显示状态
const dialogVisible = ref(false)

// 对话框模式（add/edit）
const dialogMode = ref('add')

// 提交加载状态
const submitLoading = ref(false)

// 表单引用
const formRef = ref(null)

// 表单数据
const form = reactive({
  id: null,
  code: '',
  name: '',
  description: '',
  sortOrder: 0,
  enabled: true
})

// 表单验证规则
const formRules = {
  code: [
    { required: true, message: '请输入科目编码', trigger: 'blur' },
    { max: 50, message: '编码长度不能超过50字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '编码只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入科目名称', trigger: 'blur' },
    { max: 100, message: '名称长度不能超过100字符', trigger: 'blur' }
  ],
  sortOrder: [
    { required: true, message: '请输入排序顺序', trigger: 'blur' }
  ]
}

/**
 * 加载科目列表
 */
const loadSubjects = async () => {
  try {
    const response = await getAllSubjects()
    if (response.code === 200) {
      subjects.value = response.data || []
    } else {
      ElMessage.error(response.message || '加载科目列表失败')
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
    ElMessage.error('加载科目列表失败')
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  form.id = null
  form.code = ''
  form.name = ''
  form.description = ''
  form.sortOrder = 0
  form.enabled = true
  formRef.value?.clearValidate()
}

/**
 * 新增科目
 */
const handleAdd = () => {
  resetForm()
  dialogMode.value = 'add'
  dialogVisible.value = true
}

/**
 * 编辑科目
 */
const handleEdit = (row) => {
  resetForm()
  form.id = row.id
  form.code = row.code
  form.name = row.name
  form.description = row.description || ''
  form.sortOrder = row.sortOrder
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
      code: form.code,
      name: form.name,
      description: form.description || null,
      sortOrder: form.sortOrder,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      // 创建科目
      response = await createSubject(data)
    } else {
      // 更新科目
      data.id = form.id
      response = await updateSubject(form.id, data)
    }

    if (response.code === 200) {
      ElMessage.success(dialogMode.value === 'add' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      loadSubjects()
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
      `确认${action}科目"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await updateSubject(row.id, {
      id: row.id,
      code: row.code,
      name: row.name,
      description: row.description,
      sortOrder: row.sortOrder,
      enabled: !row.enabled
    })

    if (response.code === 200) {
      ElMessage.success(`${action}成功`)
      loadSubjects()
    } else {
      ElMessage.error(response.message || `${action}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      ElMessage.error(`${action}失败`)
    }
  }
}

/**
 * 删除科目
 */
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除科目"${row.name}"吗？删除后该科目下的所有章节也将无法访问。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    const response = await deleteSubject(row.id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      loadSubjects()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSubjects()
})
</script>

<style scoped>
/**
 * 科目管理页面样式
 * 已迁移至 Tailwind CSS
 */
</style>

