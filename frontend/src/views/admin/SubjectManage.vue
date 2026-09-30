<!-- 科目管理页面：表格与编辑弹窗支持窄屏访问。 -->
<template>
  <div class="mx-auto min-h-[var(--app-page-height)] max-w-[1400px] p-2 sm:p-4 md:p-6">
    <CustomCard shadow>
      <template #header>
        <div class="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-xl text-gray-800 font-semibold">科目管理</h2>
          <CustomButton type="primary" @click="handleAdd">
            <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
            新增科目
          </CustomButton>
        </div>
      </template>

      <!-- 科目列表表格 -->
      <div v-if="loadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ loadError }}
        <CustomButton size="sm" type="text" :disabled="loading" @click="loadSubjects">重试</CustomButton>
      </div>
      <Table :data="subjects" :columns="tableColumns" :loading="loading" stripe>
        <!-- 状态列自定义 -->
        <template #enabled="{ row }">
          <Tag :type="row.enabled ? 'success' : 'danger'" class="whitespace-nowrap">
            {{ row.enabled ? '启用' : '禁用' }}
          </Tag>
        </template>

        <!-- 操作列自定义 -->
        <template #action="{ row }">
          <div class="flex justify-center gap-1 whitespace-nowrap">
            <CustomButton type="text-primary" size="sm" @click="handleEdit(row)">编辑</CustomButton>
            <CustomButton
              type="text"
              size="sm"
              @click="handleToggleStatus(row)"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </CustomButton>
            <CustomButton type="text-danger" size="sm" @click="handleDelete(row)">删除</CustomButton>
          </div>
        </template>

        <!-- 窄屏卡片：避免在手机上强制横向滚动整张管理表格。 -->
        <template #mobile="{ row }">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="m-0 truncate text-base font-semibold text-gray-800">{{ row.name }}</h3>
              <p class="m-0 mt-1 truncate text-xs text-gray-500">{{ row.code }}</p>
            </div>
            <Tag :type="row.enabled ? 'success' : 'danger'" class="shrink-0 whitespace-nowrap">
              {{ row.enabled ? '启用' : '禁用' }}
            </Tag>
          </div>
          <p v-if="row.description" class="mb-0 mt-3 line-clamp-2 text-sm text-gray-600">
            {{ row.description }}
          </p>
          <div class="mt-3 flex flex-wrap justify-end gap-1 border-t border-gray-100 pt-2">
            <CustomButton type="text-primary" size="sm" @click="handleEdit(row)">编辑</CustomButton>
            <CustomButton type="text" size="sm" @click="handleToggleStatus(row)">
              {{ row.enabled ? '禁用' : '启用' }}
            </CustomButton>
            <CustomButton type="text-danger" size="sm" @click="handleDelete(row)">删除</CustomButton>
          </div>
        </template>

        <!-- 空状态插槽 -->
        <template #empty>
          <div class="flex flex-col items-center py-12">
            <font-awesome-icon :icon="['fas', 'folder-open']" class="text-4xl text-gray-300 mb-3" />
            <p class="text-gray-500 text-sm mb-4">暂无科目数据</p>
            <CustomButton type="primary" size="sm" @click="handleAdd">
              <font-awesome-icon :icon="['fas', 'plus']" class="mr-1" />
              添加第一个科目
            </CustomButton>
          </div>
        </template>
      </Table>
    </CustomCard>

    <!-- 编辑对话框 -->
    <ResponsiveDialog
      v-model:visible="dialogVisible"
      :title="dialogMode === 'add' ? '新增科目' : '编辑科目'"
      width="600px"
      @close="resetForm"
    >
      <form ref="formRef" @submit.prevent="handleSubmit" class="edit-form">
        <section class="edit-section">
          <div class="edit-section-heading"><h4 class="edit-section-title">科目信息</h4></div>
          <div class="edit-grid">
            <div>
              <FormLabel label="科目编码" required for-id="subject-code" />
              <CustomInput id="subject-code" v-model="form.code" placeholder="如：data-structure" :maxlength="50" clearable :error="errors.code" :disabled="dialogMode === 'edit'" />
              <p class="edit-hint">创建后不可修改，最多 50 字符</p>
            </div>
            <div>
              <FormLabel label="科目名称" required for-id="subject-name" />
              <CustomInput id="subject-name" v-model="form.name" placeholder="如：数据结构" :maxlength="100" clearable :error="errors.name" />
            </div>
            <div class="edit-span-full">
              <FormLabel label="科目描述" for-id="subject-description" />
              <textarea id="subject-description" v-model="form.description" class="edit-textarea" rows="3" maxlength="500" placeholder="请输入科目描述（可选）" aria-describedby="subject-description-hint"></textarea>
              <div class="edit-field-meta">
                <p id="subject-description-hint">简要描述科目内容和学习目标</p>
                <span class="edit-count">{{ form.description?.length || 0 }}/500</span>
              </div>
            </div>
          </div>
        </section>
        <section class="edit-section">
          <div class="edit-section-heading"><h4 class="edit-section-title">排序与状态</h4></div>
          <div class="edit-grid">
            <div>
              <FormLabel label="排序顺序" required for-id="subject-order-num" />
              <InputNumber id="subject-order-num" v-model="form.orderNum" :min="0" :max="9999" placeholder="数字越小越靠前" :error="Boolean(errors.orderNum)" />
              <p class="edit-hint">数字越小，科目在列表中越靠前</p>
              <p v-if="errors.orderNum" class="mt-1 text-xs text-red-500" role="alert">{{ errors.orderNum }}</p>
            </div>
            <div>
              <FormLabel label="是否启用" for-id="subject-enabled" />
              <div class="edit-state-row">
                <span class="text-sm text-ink-soft">{{ form.enabled ? '已启用' : '已禁用' }}</span>
                <Switch id="subject-enabled" v-model="form.enabled" />
              </div>
            </div>
          </div>
        </section>
      </form>

      <template #footer>
        <div class="edit-footer">
          <div class="edit-footer-actions">
            <CustomButton @click="dialogVisible = false">取消</CustomButton>
            <CustomButton type="primary" :loading="submitLoading" @click="handleSubmit">{{ dialogMode === 'add' ? '创建科目' : '保存修改' }}</CustomButton>
          </div>
        </div>
      </template>
    </ResponsiveDialog>
  </div>
</template>

<script setup lang="ts">
import type { Subject } from "@/types"
/**
 * 科目管理页面
 * 功能：科目的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+对话框实现
 */

// 1. Vue 官方 API
import { ref, reactive, onMounted } from 'vue'

// 2. Vue Router 相关（本页面未使用）

// 3. Pinia Store（本页面未使用）

// 4. 工具函数 / Composables
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

// 5. API 接口定义
import {
  getAllSubjects,
  createSubject,
  updateSubject,
  deleteSubject
} from '@/api/subject'

// 6. 子组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import Table from '@/components/basic/Table.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import InputNumber from '@/components/basic/InputNumber.vue'
import Switch from '@/components/basic/Switch.vue'
import Tag from '@/components/basic/Tag.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import '@/styles/edit-form.css'

// 消息提示和确认框
const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 加载状态
const loading = ref(false)
const loadError = ref('')

// 科目列表
const subjects = ref<Subject[]>([])

// 表格列定义
const tableColumns = [
  { prop: 'id', label: 'ID', width: '80' },
  { prop: 'code', label: '科目编码', width: '150' },
  { prop: 'name', label: '科目名称', width: '200' },
  { prop: 'description', label: '描述', minWidth: '200' },
  { prop: 'enabled', label: '状态', width: '120' },
  { prop: 'action', label: '操作', width: '260', fixed: 'right', slot: true }
]

// 对话框显示状态
const dialogVisible = ref(false)

// 对话框模式（add/edit）
const dialogMode = ref('add')

// 提交加载状态
const submitLoading = ref(false)

// 表单引用
const formRef = ref(null)

// 错误信息
const errors = reactive({
  code: '',
  name: '',
  orderNum: ''
})

// 表单数据
const form = reactive({
  id: null as number | null,
  code: '',
  name: '',
  description: '',
  orderNum: 0,
  enabled: true
})

// 表单验证方法
const validateForm = () => {
  let isValid = true

  // 重置错误
  errors.code = ''
  errors.name = ''
  errors.orderNum = ''

  // 验证科目编码
  if (!form.code.trim()) {
    errors.code = '请输入科目编码'
    isValid = false
  } else if (form.code.length > 50) {
    errors.code = '编码长度不能超过50字符'
    isValid = false
  }

  // 验证科目名称
  if (!form.name.trim()) {
    errors.name = '请输入科目名称'
    isValid = false
  } else if (form.name.length > 100) {
    errors.name = '名称长度不能超过100字符'
    isValid = false
  }

  // 验证排序顺序
  if (form.orderNum === null || form.orderNum === undefined) {
    errors.orderNum = '请输入排序顺序'
    isValid = false
  }

  return isValid
}

/**
 * 加载科目列表
 */
const loadSubjects = async () => {
  loadError.value = ''
  loading.value = true
  try {
    const response = await getAllSubjects()
    if (response.code === 200) {
      loadError.value = ''
      subjects.value = response.data || []
    } else {
      subjects.value = []
      loadError.value = response.message || '加载科目列表失败，请重试。'
      showToast(response.message || '加载科目列表失败', 'error')
    }
  } catch (error) {
    subjects.value = []
    loadError.value = '加载科目列表失败，请重试。'
    console.error('加载科目列表失败:', error)
    showToast('加载科目列表失败', 'error')
  } finally {
    loading.value = false
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
  form.orderNum = 0
  form.enabled = true
  // 重置错误信息
  errors.code = ''
  errors.name = ''
  errors.orderNum = ''
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
const handleEdit = (row: Subject) => {
  resetForm()
  form.id = row.id
  form.code = row.code
  form.name = row.name
  form.description = row.description || ''
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
  if (!validateForm()) {
    return
  }

  submitLoading.value = true
  try {
    let response
    const data = {
      code: form.code,
      name: form.name,
      description: form.description || null,
      orderNum: form.orderNum,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      // 创建科目
      response = await createSubject(data)
    } else {
      // 更新科目
      if (form.id === null) return
      response = await updateSubject(form.id, data)
    }

    if (response.code === 200) {
      showToast(dialogMode.value === 'add' ? '创建成功' : '更新成功', 'success')
      dialogVisible.value = false
      loadSubjects()
    } else {
      showToast(response.message || '操作失败', 'error')
    }
  } catch (error) {
    console.error('提交失败:', error)
    showToast(dialogMode.value === 'add' ? '创建失败' : '更新失败', 'error')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 切换启用/禁用状态
 */
const handleToggleStatus = async (row: Subject) => {
  const action = row.enabled ? '禁用' : '启用'
  try {
    const confirmed = await showConfirm({
      title: '确认操作',
      message: `确认${action}科目"${row.name}"吗？`,
      type: 'warning',
      confirmText: '确定',
      cancelText: '取消'
    })

    if (!confirmed) return
    const response = await updateSubject(row.id, {
      code: row.code,
      name: row.name,
      description: row.description,
      orderNum: row.orderNum,
      enabled: !row.enabled
    })

    if (response.code === 200) {
      showToast(`${action}成功`, 'success')
      loadSubjects()
    } else {
      showToast(response.message || `${action}失败`, 'error')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      showToast(`${action}失败`, 'error')
    }
  }
}

/**
 * 删除科目
 */
const handleDelete = async (row: Subject) => {
  try {
    const confirmed = await showConfirm({
      title: '删除确认',
      message: `确认删除科目"${row.name}"吗？删除后该科目下的所有章节也将无法访问。`,
      type: 'danger',
      confirmText: '确定',
      cancelText: '取消'
    })

    if (!confirmed) return
    const response = await deleteSubject(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      loadSubjects()
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      showToast('删除失败', 'error')
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
 * 使用 Tailwind 原子类为主，此处仅保留必要的自定义样式
 */

/* 骨架屏动画 */
@keyframes shimmer {
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
}

.skeleton-shimmer {
  animation-duration: 1.25s;
  animation-fill-mode: forwards;
  animation-iteration-count: infinite;
  animation-name: shimmer;
  animation-timing-function: linear;
  background: linear-gradient(to right, #f6f7f9 8%, #e9ebee 18%, #f6f7f9 33%);
  background-size: 800px 104px;
}

/* 错误提示抖动动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

.error-shake {
  animation: shake 0.5s ease-in-out;
}
</style>
