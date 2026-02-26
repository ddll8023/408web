<template>
  <div class="max-w-[1400px] mx-auto px-6 py-8 h-[calc(100vh-60px)] overflow-hidden">
    <!-- 页面标题栏 -->
    <div class="flex items-center justify-between mb-8 pb-6 border-b-2 border-[rgba(139,111,71,0.1)]">
      <div class="flex flex-col gap-1">
        <h1 class="m-0 text-[1.75rem] font-semibold text-[#8B6F47] flex items-center">
          <span class="inline-block w-1.5 h-7 bg-gradient-to-b from-[#8B6F47] to-[#a88a5f] mr-4 rounded-sm"></span>
          分类标签管理
        </h1>
        <span class="text-xs text-[#999] ml-[calc(5px+16px)]">管理各科目的题目分类层级结构</span>
      </div>
      <div class="flex items-center gap-6">
        <!-- 题目类型切换 -->
        <CustomRadioGroup v-model="questionType" :options="[
          { label: '真题', value: 'exam' },
          { label: '模拟题', value: 'mock' }
        ]" @change="handleQuestionTypeChange" />
        <CustomButton v-if="questionType === 'exam'" type="primary" @click="handleAdd">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
          新增分类
        </CustomButton>
        <CustomTooltip v-else content="模拟题分类从题目中动态提取，暂不支持手动管理" placement="top">
          <CustomButton type="primary" disabled>
            <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
            新增分类
          </CustomButton>
        </CustomTooltip>
      </div>
    </div>

    <!-- 左右分栏布局 -->
    <div class="flex gap-8 items-start">
      <!-- 左侧筛选栏 -->
      <aside class="w-64 flex-shrink-0 sticky top-[calc(60px+24px)]">
        <!-- 科目筛选列表 -->
        <div class="bg-white rounded-xl p-6 shadow-sm border border-[rgba(139,111,71,0.08)] mb-6">
          <h3 class="m-0 mb-4 text-sm font-semibold text-[#8B6F47] flex items-center gap-2 pb-3 border-b border-[rgba(139,111,71,0.1)]">
            <font-awesome-icon :icon="['fas', 'folder']" class="text-base" />
            科目筛选
          </h3>
          <div class="flex flex-col gap-1">
            <!-- 各科目选项 -->
            <div
              v-for="stat in subjectStats"
              :key="stat.id"
              class="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200"
              :class="filterSubjectId === stat.id ? 'bg-gradient-to-r from-[rgba(139,111,71,0.12)] to-[rgba(139,111,71,0.06)]' : 'hover:bg-[rgba(139,111,71,0.06)]'"
              @click="handleStatClick(stat.id)"
            >
              <div class="flex items-center gap-2.5 min-w-0">
                <div class="w-7 h-7 flex items-center justify-center rounded-md bg-[rgba(139,111,71,0.08)] text-[#999] text-sm transition-all duration-200 flex-shrink-0" :class="{ '!bg-[rgba(139,111,71,0.15)] !text-[#8B6F47]': filterSubjectId === stat.id }">
                  <font-awesome-icon :icon="['fas', 'folder']" />
                </div>
                <span class="text-sm text-[#333] whitespace-nowrap overflow-hidden text-ellipsis transition-all duration-200" :class="{ '!text-[#8B6F47] !font-semibold': filterSubjectId === stat.id }">{{ stat.name }}</span>
                <CustomTooltip v-if="stat.enabledCount < stat.count" :content="`${stat.count - stat.enabledCount} 个分类已禁用`" placement="top">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="text-[#e6a23c] text-sm ml-1" />
                </CustomTooltip>
              </div>
              <!-- 显示题目引用数量 -->
              <span class="min-w-[36px] px-2 py-0.5 text-xs font-semibold text-center rounded-[10px] bg-[rgba(139,111,71,0.1)] text-[#8B6F47]" :class="{ '!bg-[#8B6F47] !text-white': filterSubjectId === stat.id }">
                {{ stat.questionCount }}
              </span>
            </div>
          </div>
        </div>

      </aside>

      <!-- 右侧主内容区 -->
      <main class="flex-1 min-w-0 relative h-[calc(100vh-60px-128px)] overflow-y-auto">
        <!-- 背景层次增强 -->
        <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <!-- 右上角暖色光晕 -->
          <div class="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-[rgba(139,111,71,0.08)] to-transparent rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3"></div>
          <!-- 左下角冷色光晕 -->
          <div class="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-[rgba(64,158,255,0.05)] to-transparent rounded-full blur-3xl transform -translate-x-1/3 translate-y-1/3"></div>
          <!-- 几何网格纹理 -->
          <div class="absolute inset-0 opacity-[0.03]" style="background-image: radial-gradient(#8B6F47 1px, transparent 1px); background-size: 24px 24px;"></div>
        </div>

        <!-- 骨架屏 - 档案柜风格 -->
        <div v-if="loading" class="
          relative
          bg-gradient-to-br from-white/90 to-[rgba(139,111,71,0.02)]/30
          backdrop-blur-sm
          rounded-2xl p-6
          border border-white/50
          shadow-[0_2px_16px_rgba(139,111,71,0.06),inset_0_1px_0_rgba(255,255,255,0.8)]
          before:absolute before:inset-0 before:rounded-2xl before:p-px
          before:bg-gradient-to-br before:from-white/40 before:to-transparent before:-z-10
        ">
          <div class="skeleton-container">
          <div v-for="i in 3" :key="i" class="
            bg-white rounded-xl overflow-hidden
            border border-[rgba(139,111,71,0.08)]
            shadow-sm skeleton-card
          ">
            <div class="h-1.5 skeleton-shimmer"></div>
            <div class="p-5 space-y-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 skeleton-shimmer rounded-lg"></div>
                <div class="space-y-2">
                  <div class="w-32 h-4 skeleton-shimmer rounded"></div>
                  <div class="w-20 h-3 skeleton-shimmer rounded"></div>
                </div>
              </div>
              <div class="flex gap-4">
                <div class="w-16 h-3 skeleton-shimmer rounded"></div>
                <div class="w-16 h-3 skeleton-shimmer rounded"></div>
                <div class="w-16 h-3 skeleton-shimmer rounded"></div>
              </div>
              <div class="grid grid-cols-2 gap-2 pt-4 border-t border-dashed border-[rgba(139,111,71,0.08)]">
                <div class="h-16 skeleton-shimmer rounded-lg"></div>
                <div class="h-16 skeleton-shimmer rounded-lg"></div>
              </div>
            </div>
          </div>
          </div>
        </div>

        <!-- 树形视图 -->
        <template v-if="treeCategories.length > 0">
          <Transition name="tree-fade">
            <!-- 统一的背景容器 -->
            <div class="
              relative
              bg-gradient-to-br from-white/90 to-[rgba(139,111,71,0.02)]/30
              backdrop-blur-sm
              rounded-2xl p-6
              border border-white/50
              shadow-[0_2px_16px_rgba(139,111,71,0.06),inset_0_1px_0_rgba(255,255,255,0.8)]
              before:absolute before:inset-0 before:rounded-2xl before:p-px
              before:bg-gradient-to-br before:from-white/40 before:to-transparent before:-z-10
            ">
              <!-- 树形视图工具栏 -->
              <div class="flex gap-2 pb-3 mb-3 border-b border-[rgba(139,111,71,0.1)]">
                <CustomButton type="text" size="sm" @click="expandAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-down']" class="mr-1" />
                  全部展开
                </CustomButton>
                <CustomButton type="text" size="sm" @click="collapseAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="mr-1" />
                  全部收起
                </CustomButton>
              </div>
              <CustomTree
              ref="treeRef"
              :data="treeCategories"
              :node-key="'id'"
              :label="'name'"
              :children-key="'children'"
              v-model:expanded-keys="treeExpandedKeys"
              @node-expand="handleTreeNodeExpand"
              @node-collapse="handleTreeNodeCollapse"
            >
              <template #default="{ node: data, level }">
                <div class="
                  flex-1 flex items-center justify-between px-3 py-2 rounded-xl
                  hover:bg-white/60 hover:backdrop-blur-sm
                  border border-transparent hover:border-[rgba(139,111,71,0.08)]
                  shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]
                  transition-all duration-200
                " :class="{ 'opacity-60': !data.enabled }">
                  <div class="flex items-center gap-2.5">
                    <div class="
                      w-8 h-8 flex items-center justify-center
                      bg-gradient-to-br from-[rgba(139,111,71,0.12)] to-[rgba(139,111,71,0.05)]
                      text-[#8B6F47] rounded-lg
                      shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]
                      transition-all duration-200
                    ">
                      <font-awesome-icon v-if="data.children && data.children.length > 0" :icon="['fas', 'folder-open']" />
                      <font-awesome-icon v-else :icon="['fas', 'file']" />
                    </div>
                    <span class="text-sm font-medium text-[#333]">{{ data.name }}</span>
                    <span v-if="questionType === 'exam'" class="text-xs text-[#999] font-mono bg-[rgba(139,111,71,0.08)] px-1.5 py-0.5 rounded">{{ data.code }}</span>
                    <CustomTag v-if="level === 0" variant="info" class="ml-1">
                      {{ data.subjectName }}
                    </CustomTag>
                    <span class="text-xs text-[#999] bg-[rgba(139,111,71,0.08)] px-2 py-0.5 rounded-[10px]">{{ getChildrenQuestionCount(data) }}题</span>
                  </div>
                  <!-- 操作按钮：仅真题模式显示 -->
                  <div v-if="questionType === 'exam'" class="flex items-center gap-2 opacity-0 transition-opacity duration-200" :class="{ '!opacity-100': true }">
                    <CustomTooltip content="添加子分类" placement="top" v-if="level < 2 && !data.isSubjectGroup">
                      <div class="w-7 h-7 flex items-center justify-center rounded-md cursor-pointer text-[#999] hover:bg-[rgba(139,111,71,0.1)] hover:text-[#8B6F47]" @click.stop="handleAddChild(data)">
                        <font-awesome-icon :icon="['fas', 'plus']" />
                      </div>
                    </CustomTooltip>
                    <CustomTooltip content="编辑" placement="top">
                      <div class="w-7 h-7 flex items-center justify-center rounded-md cursor-pointer text-[#999] hover:bg-[rgba(139,111,71,0.1)] hover:text-[#8B6F47]" @click.stop="handleEdit(data)">
                        <font-awesome-icon :icon="['fas', 'edit']" />
                      </div>
                    </CustomTooltip>
                    <CustomButton type="text-danger" size="sm" class="!p-1" @click="handleDelete(data)">
                      <font-awesome-icon :icon="['fas', 'trash']" />
                    </CustomButton>
                  </div>
                </div>
              </template>
            </CustomTree>
            </div>
          </Transition>
        </template>

        <!-- 空状态 -->
        <div v-if="!loading && treeCategories.length === 0" class="
          relative flex flex-col items-center justify-center py-20
          bg-white/40 backdrop-blur-sm
          rounded-2xl border border-dashed border-[rgba(139,111,71,0.15)]
        ">
          <CustomEmpty description="暂无分类数据" />
        </div>
      </main>
    </div>

    <!-- 编辑对话框 -->
    <CustomDialog
      v-model:visible="dialogVisible"
      :title="dialogMode === 'add' ? '新增分类' : '编辑分类'"
      width="680px"
    >
      <!-- 表单区域 - 分组布局 -->
      <div class="space-y-6">
        <!-- 基本信息组 -->
        <div class="
          relative p-5
          bg-gradient-to-br from-white/80 to-[rgba(139,111,71,0.02)]
          backdrop-blur-sm
          rounded-xl
          border border-white/50
          shadow-[0_2px_16px_rgba(139,111,71,0.06)]
          before:absolute before:inset-0 before:rounded-xl before:p-px
          before:bg-gradient-to-br before:from-white/60 before:to-transparent before:-z-10
        ">
          <!-- 分组标题 -->
          <div class="flex items-center gap-2 mb-5 pb-4 border-b border-dashed border-[rgba(139,111,71,0.12)]">
            <div class="w-7 h-7 flex items-center justify-center bg-gradient-to-br from-[#8B6F47] to-[#968657] text-white rounded-lg shadow-md">
              <font-awesome-icon :icon="['fas', 'folder-plus']" class="text-sm" />
            </div>
            <span class="text-base font-semibold text-[#8B6F47]">基本信息</span>
          </div>

          <!-- 第一行：所属科目 + 父分类 -->
          <div class="grid grid-cols-2 gap-5 mb-5">
            <div>
              <label class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                所属科目
                <span class="text-red-500">*</span>
              </label>
              <CustomSelect
                v-model="form.subjectId"
                :options="subjectOptions.map(s => ({ label: s.name, value: s.id }))"
                placeholder="请选择科目"
                :disabled="dialogMode === 'edit'"
                @change="handleSubjectChange"
              />
              <p class="text-xs text-[#999] mt-1.5" v-if="dialogMode === 'edit'">所属科目创建后不可修改</p>
            </div>
            <div>
              <label class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                父分类
              </label>
              <CustomSelect
                v-model="form.parentId"
                :options="parentOptions"
                placeholder="无（顶级分类）"
                clearable
                :disabled="!form.subjectId || (dialogMode === 'edit' && hasChildren)"
              />
              <p class="text-xs text-[#999] mt-1.5">
                <span v-if="hasChildren">该分类已有子分类</span>
                <span v-else>留空表示顶级分类</span>
              </p>
            </div>
          </div>

          <!-- 第二行：分类编码 + 分类名称 -->
          <div class="grid grid-cols-2 gap-5">
            <CustomInput
              v-model="form.code"
              label="分类编码"
              placeholder="如：stack-queue"
              :maxlength="50"
              required
            >
              <template #tip>
                <p class="text-xs text-[#999] mt-1">建议使用英文小写字母和连字符</p>
              </template>
            </CustomInput>
            <CustomInput
              v-model="form.name"
              label="分类名称"
              placeholder="如：栈和队列"
              :maxlength="50"
              required
            />
          </div>
        </div>

        <!-- 详细信息组 -->
        <div class="
          relative p-5
          bg-gradient-to-br from-white/80 to-[rgba(139,111,71,0.02)]
          backdrop-blur-sm
          rounded-xl
          border border-white/50
          shadow-[0_2px_16px_rgba(139,111,71,0.06)]
          before:absolute before:inset-0 before:rounded-xl before:p-px
          before:bg-gradient-to-br before:from-white/60 before:to-transparent before:-z-10
        ">
          <!-- 分组标题 -->
          <div class="flex items-center gap-2 mb-4 pb-4 border-b border-dashed border-[rgba(139,111,71,0.12)]">
            <div class="w-7 h-7 flex items-center justify-center bg-gradient-to-br from-[#40a9ff] to-[#1890ff] text-white rounded-lg shadow-md">
              <font-awesome-icon :icon="['fas', 'align-left']" class="text-sm" />
            </div>
            <span class="text-base font-semibold text-[#8B6F47]">详细信息</span>
          </div>

          <!-- 分类描述 -->
          <div>
            <label class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
              分类描述
            </label>
            <textarea
              v-model="form.description"
              class="
                w-full px-4 py-3
                border border-[rgba(139,111,71,0.15)] rounded-xl
                bg-white/80 backdrop-blur-sm
                focus:outline-none focus:border-[#8B6F47] focus:ring-2 focus:ring-[#8B6F47]/15
                transition-all duration-200
                resize-none
              "
              placeholder="请输入分类描述（可选）"
              :rows="3"
              :maxlength="255"
            ></textarea>
            <div class="flex justify-end mt-2">
              <span class="text-xs px-2 py-0.5 rounded-full bg-[rgba(139,111,71,0.08)] text-[#8B6F47]">
                {{ form.description?.length || 0 }} / 255
              </span>
            </div>
          </div>
        </div>

        <!-- 排序与状态组 -->
        <div class="
          relative p-5
          bg-gradient-to-br from-white/80 to-[rgba(139,111,71,0.02)]
          backdrop-blur-sm
          rounded-xl
          border border-white/50
          shadow-[0_2px_16px_rgba(139,111,71,0.06)]
          before:absolute before:inset-0 before:rounded-xl before:p-px
          before:bg-gradient-to-br before:from-white/60 before:to-transparent before:-z-10
        ">
          <!-- 分组标题 -->
          <div class="flex items-center gap-2 mb-5 pb-4 border-b border-dashed border-[rgba(139,111,71,0.12)]">
            <div class="w-7 h-7 flex items-center justify-center bg-gradient-to-br from-[#73d13d] to-[#52c41a] text-white rounded-lg shadow-md">
              <font-awesome-icon :icon="['fas', 'sliders-h']" class="text-sm" />
            </div>
            <span class="text-base font-semibold text-[#8B6F47]">排序与状态</span>
          </div>

          <!-- 排序 + 启用状态 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <label class="text-sm font-medium text-gray-700">排序顺序</label>
              <CustomInputNumber
                v-model="form.orderNum"
                :min="0"
                :max="9999"
              />
              <span class="text-xs text-[#999]">数字越小越靠前</span>
            </div>
            <div class="flex items-center gap-3 px-4 py-2.5 bg-[rgba(139,111,71,0.04)] rounded-xl">
              <CustomSwitch v-model="form.enabled" />
              <span class="text-sm font-medium" :class="form.enabled ? 'text-[#52c41a]' : 'text-[#999]'">
                {{ form.enabled ? '已启用' : '已禁用' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <CustomButton @click="dialogVisible = false">取消</CustomButton>
          <CustomButton type="primary" :loading="submitLoading" @click="handleSubmit">
            确定
          </CustomButton>
        </div>
      </template>
    </CustomDialog>
  </div>
</template>

<script setup>
/**
 * 分类标签管理页面
 * 功能：按科目管理分类标签的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+对话框实现
 */
import { ref, reactive, computed, onMounted } from 'vue'

// 工具函数 / 常量
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

// API 接口定义
import {
  getAllCategories,
  getCategoriesBySubject,
  createCategory,
  updateCategory,
  deleteCategory,
  checkCategoryUsage,
  getAvailableParentCategories,
  getCategoryStats
} from '@/api/category'
import { getAllSubjects } from '@/api/subject'
import { getMockCategoryStatsBySubject, getMockCategoriesBySubject, getMockSubjectStats } from '@/api/mock'

// 自定义组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomDialog from '@/components/basic/Dialog.vue'
import CustomSelect from '@/components/basic/Select.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import CustomTag from '@/components/basic/Tag.vue'
import CustomEmpty from '@/components/basic/Empty.vue'
import CustomSwitch from '@/components/basic/Switch.vue'
import CustomInputNumber from '@/components/basic/InputNumber.vue'
import CustomTooltip from '@/components/basic/Tooltip.vue'
import CustomRadioGroup from '@/components/basic/RadioGroup.vue'
import CustomTree from '@/components/basic/Tree.vue'

const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 所有分类列表（用于统计）
const allCategories = ref([])

// 当前显示的分类列表（筛选后）
const categories = ref([])

// 科目选项
const subjectOptions = ref([])

// 筛选科目ID
const filterSubjectId = ref(null)

// 题目类型筛选（exam=真题, mock=模拟题）
const questionType = ref('exam')

// 树形视图引用
const treeRef = ref(null)

// 树形视图展开的节点ID列表（响应式，用于保持展开状态）
const treeExpandedKeys = ref([])

/**
 * 树形视图：全部展开
 * 直接设置 treeExpandedKeys 数组
 */
const expandAllTree = () => {
  const allNodes = getAllTreeNodes(treeCategories.value)
  treeExpandedKeys.value = allNodes
}

/**
 * 树形视图：全部收起
 * 清空 treeExpandedKeys 数组
 */
const collapseAllTree = () => {
  treeExpandedKeys.value = []
}

/**
 * 处理树节点展开事件
 * 将展开的节点ID添加到 treeExpandedKeys 中
 */
const handleTreeNodeExpand = (data) => {
  if (!treeExpandedKeys.value.includes(data.id)) {
    treeExpandedKeys.value.push(data.id)
  }
}

/**
 * 处理树节点收起事件
 * 从 treeExpandedKeys 中移除收起的节点ID
 */
const handleTreeNodeCollapse = (data) => {
  const index = treeExpandedKeys.value.indexOf(data.id)
  if (index > -1) {
    treeExpandedKeys.value.splice(index, 1)
  }
}

/**
 * 获取树形视图当前展开的节点ID列表
 * 直接返回 treeExpandedKeys 的副本
 */
const getTreeExpandedKeys = () => {
  return [...treeExpandedKeys.value]
}

/**
 * 恢复树形视图的展开状态
 * 直接设置 treeExpandedKeys 数组
 * @param {Array} keys 需要展开的节点ID列表
 */
const restoreTreeExpandedKeys = (keys) => {
  if (!keys) return
  treeExpandedKeys.value = [...keys]
}

/**
 * 递归获取所有树节点ID
 */
const getAllTreeNodes = (nodes) => {
  const ids = []
  const traverse = (list) => {
    list.forEach(node => {
      ids.push(node.id)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(nodes)
  return ids
}

// 科目统计数据（用于科目筛选列表）
const categoryStats = ref({
  subjectStats: [],  // 各科目题目数
  totalQuestionCount: 0  // 全局题目总数
})

// 加载状态
const loading = ref(false)

// 对话框显示状态
const dialogVisible = ref(false)

// 对话框模式（add/edit）
const dialogMode = ref('add')

// 提交加载状态
const submitLoading = ref(false)

// 父分类选项
const parentOptions = ref([])

// 编辑时检查是否有子分类
const hasChildren = ref(false)

/**
 * 将分类数据转换为树形结构或分组结构
 * 模拟题模式：按科目分组显示（扁平结构）
 * 真题模式：构建树形结构（支持多层级）
 */
const treeCategories = computed(() => {
  const list = categories.value
  if (!list || list.length === 0) return []

  // 模拟题模式：扁平列表显示（所有分类平铺，不按科目分组）
  if (questionType.value === 'mock') {
    // 直接返回扁平列表，每个分类都是独立的卡片
    return list.map(item => ({
      ...item,
      children: []  // 模拟题没有子分类
    }))
  }

  // 真题模式：构建树形结构
  // 创建id到节点的映射
  const map = new Map()
  list.forEach(item => {
    map.set(item.id, { ...item, children: [] })
  })

  const tree = []
  list.forEach(item => {
    const node = map.get(item.id)
    if (item.parentId && map.has(item.parentId)) {
      map.get(item.parentId).children.push(node)
    } else {
      tree.push(node)
    }
  })

  // 对每层按orderNum排序
  const sortChildren = (nodes) => {
    nodes.sort((a, b) => (a.orderNum || 0) - (b.orderNum || 0))
    nodes.forEach(node => {
      if (node.children && node.children.length > 0) {
        sortChildren(node.children)
      }
    })
  }
  sortChildren(tree)
  
  return tree
})

/**
 * 计算各科目分类统计（用于科目筛选列表）
 * 使用 allCategories 获取分类数量，使用 categoryStats 获取题目数
 */
const subjectStats = computed(() => {
  return subjectOptions.value.map(subject => {
    const subjectCategories = allCategories.value.filter(c => c.subjectId === subject.id)
    // 从统计数据中获取该科目的题目数
    const statItem = categoryStats.value.subjectStats.find(s => s.subjectId === subject.id)
    const questionCount = statItem ? statItem.questionCount : 0
    return {
      id: subject.id,
      name: subject.name,
      count: subjectCategories.length,  // 分类数量
      enabledCount: subjectCategories.filter(c => c.enabled).length,
      questionCount: questionCount  // 题目数
    }
  })
})

// 表单数据
const form = reactive({
  id: null,
  subjectId: null,
  parentId: null,
  code: '',
  name: '',
  description: '',
  orderNum: 0,
  enabled: true
})

/**
 * 加载科目选项
 */
const loadSubjectOptions = async () => {
  try {
    const response = await getAllSubjects()
    if (response.code === 200) {
      subjectOptions.value = response.data || []
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
  }
}

/**
 * 加载科目统计数据（用于科目筛选列表）
 * 根据题目类型使用不同的 API
 */
const loadCategoryStats = async () => {
  try {
    if (questionType.value === 'mock') {
      // 模拟题：使用 /api/mock/subject-stats 获取每个科目的正确题目数量（去重后）
      const response = await getMockSubjectStats()
      if (response.code === 200) {
        const stats = response.data || []
        categoryStats.value = {
          subjectStats: stats.map(s => ({
            subjectId: s.subject_id,
            subjectName: s.subject_name,
            questionCount: s.count
          })),
          totalQuestionCount: stats.reduce((sum, s) => sum + s.count, 0)
        }
      }
    } else {
      // 真题：使用真题 API
      const response = await getCategoryStats(questionType.value)
      if (response.code === 200) {
        categoryStats.value = {
          subjectStats: response.data?.subject_stats?.map(s => ({
            subjectId: s.subject_id,
            subjectName: s.subject_name,
            questionCount: s.question_count
          })) || [],
          totalQuestionCount: response.data?.total_question_count || 0
        }
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

/**
 * 加载分类列表（筛选后显示）
 * 根据题目类型使用不同的 API
 */
const loadCategories = async () => {
  loading.value = true
  try {
    let response

    if (questionType.value === 'mock') {
      // 模拟题：使用模拟题 API（动态分类）
      if (filterSubjectId.value) {
        // 直接使用外层 response 变量，不再声明新变量
        response = await getMockCategoryStatsBySubject(filterSubjectId.value)
        if (response.code === 200) {
          const stats = response.data?.stats || []
          // 转换格式：扁平结构，适配前端显示
          // 统一ID生成逻辑：使用 科目ID-分类名 格式
          categories.value = stats.map(item => ({
            id: `${filterSubjectId.value}-${item.category}`,
            subjectId: filterSubjectId.value,
            subjectName: response.data?.subject_name,
            parentId: null,
            parentName: null,
            name: item.category,
            code: item.category.toLowerCase().replace(/\s+/g, '-'),
            description: null,
            orderNum: 0,
            enabled: true,
            questionCount: item.count,
            question_type: 'mock'
          }))
          // 同步更新全部分类数据
          allCategories.value = [...categories.value]
        }
      } else {
        // 没有选择科目，加载所有科目的模拟题分类
        const allStats = []
        for (const subject of subjectOptions.value) {
          // 直接使用外层 response 变量
          response = await getMockCategoryStatsBySubject(subject.id)
          if (response.code === 200) {
            const stats = response.data?.stats || []
            stats.forEach(item => {
              // 统一ID生成逻辑：使用 科目ID-分类名 格式
              allStats.push({
                id: `${subject.id}-${item.category}`,
                subjectId: subject.id,
                subjectName: subject.name,
                parentId: null,
                parentName: null,
                name: item.category,
                code: item.category.toLowerCase().replace(/\s+/g, '-'),
                description: null,
                orderNum: 0,
                enabled: true,
                questionCount: item.count,
                question_type: 'mock'
              })
            })
          }
        }
        categories.value = allStats
        allCategories.value = allStats
      }
    } else {
      // 真题：使用真题 API（预定义分类，有层级）
      if (filterSubjectId.value) {
        response = await getCategoriesBySubject(filterSubjectId.value, questionType.value)
      } else {
        response = await getAllCategories(questionType.value)
      }

      if (response.code === 200) {
        // 转换字段名：将 snake_case 转换为 camelCase
        categories.value = (response.data || []).map(item => ({
          ...item,
          parentId: item.parent_id,
          subjectId: item.subject_id,
          subjectName: item.subject_name,
          questionCount: item.question_count,
          orderNum: item.order_num
        }))
        // 同步更新全部分类数据（保证统计数据实时）
        allCategories.value = (response.data || []).map(item => ({
          ...item,
          parentId: item.parent_id,
          subjectId: item.subject_id,
          subjectName: item.subject_name,
          questionCount: item.question_count,
          orderNum: item.order_num
        }))
      } else {
        showToast(response.message || '加载分类列表失败', 'error')
      }
    }
  } catch (error) {
    console.error('加载分类列表失败:', error)
    showToast('加载分类列表失败', 'error')
  } finally {
    loading.value = false
  }
}

/**
 * 题目类型切换处理
 * 切换时需要更新当前显示的分类
 */
const handleQuestionTypeChange = async () => {
  // 加载科目统计数据（用于科目筛选列表显示题目数）
  await loadCategoryStats()
  // 加载所有科目的分类数据（用于统计分类数量）
  await loadCategories()
  // 默认选中第一个科目
  if (subjectOptions.value.length > 0) {
    filterSubjectId.value = subjectOptions.value[0].id
    // 重新加载选中科目的分类数据
    await loadCategories()
  }
  // 重新初始化树形视图展开状态
  initTreeExpandedKeys()
}

/**
 * 点击统计卡片筛选
 */
const handleStatClick = async (subjectId) => {
  filterSubjectId.value = subjectId
  await loadCategories()
  // 重新初始化树形视图展开状态
  initTreeExpandedKeys()
}

/**
 * 重置表单
 */
const resetForm = () => {
  form.id = null
  form.subjectId = filterSubjectId.value || null
  form.parentId = null
  form.code = ''
  form.name = ''
  form.description = ''
  form.orderNum = 0
  form.enabled = true
  parentOptions.value = []
  hasChildren.value = false
}

/**
 * 科目变更时加载可选父分类
 */
const handleSubjectChange = async () => {
  form.parentId = null
  if (form.subjectId) {
    await loadParentOptions(form.subjectId, form.id)
  } else {
    parentOptions.value = []
  }
}

/**
 * 加载可选父分类
 */
const loadParentOptions = async (subjectId, excludeId = null) => {
  try {
    const response = await getAvailableParentCategories(subjectId, excludeId)
    if (response.code === 200) {
      // 转换为 CustomSelect 需要的格式，并添加层级缩进
      parentOptions.value = (response.data || []).map(parent => ({
        value: parent.id,
        label: parent.parentId ? `└ ${parent.name}` : parent.name
      }))
    }
  } catch (error) {
    console.error('加载父分类失败:', error)
  }
}

/**
 * 新增分类
 */
const handleAdd = () => {
  resetForm()
  dialogMode.value = 'add'
  dialogVisible.value = true
}

/**
 * 编辑分类
 */
const handleEdit = async (row) => {
  resetForm()
  form.id = row.id
  form.subjectId = row.subjectId
  form.parentId = row.parentId || null
  form.code = row.code
  form.name = row.name
  form.description = row.description || ''
  form.orderNum = row.orderNum
  form.enabled = row.enabled
  
  // 加载可选父分类（排除自身）
  await loadParentOptions(row.subjectId, row.id)
  
  // 检查是否有子分类（有子分类的顶级分类不能变为子分类）
  if (row.parentId === null) {
    // 顶级分类，检查是否有子分类
    hasChildren.value = categories.value.some(c => c.parentId === row.id)
  } else {
    hasChildren.value = false
  }
  
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

/**
 * 提交表单
 * 优化：编辑时使用局部更新，新增时保持展开状态
 */
const handleSubmit = async () => {
  // 手动表单验证
  if (!form.subjectId) {
    showToast('请选择所属科目', 'warning')
    return
  }
  if (!form.code) {
    showToast('请输入分类编码', 'warning')
    return
  }
  if (!form.name) {
    showToast('请输入分类名称', 'warning')
    return
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(form.code)) {
    showToast('编码只能包含字母、数字、下划线和连字符', 'warning')
    return
  }

  submitLoading.value = true
  try {
    let response
    const data = {
      subject_id: form.subjectId,
      parent_id: form.parentId || null,
      code: form.code,
      name: form.name,
      description: form.description || null,
      order_num: form.orderNum,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      response = await createCategory(data)
    } else {
      response = await updateCategory(form.id, data)
    }

    if (response.code === 200) {
      showToast(dialogMode.value === 'add' ? '创建成功' : '更新成功', 'success')
      dialogVisible.value = false

      if (dialogMode.value === 'add') {
        // 保存树形视图展开状态
        const savedTreeExpandedKeys = getTreeExpandedKeys()

        await loadCategories()

        // 恢复树形视图展开状态
        restoreTreeExpandedKeys(savedTreeExpandedKeys)
      } else {
        // 编辑：局部更新本地数据，避免页面刷新
        const updatedData = response.data
        updateLocalCategory(form.id, updatedData)
      }
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
 * 局部更新本地分类数据
 * 用后端返回的数据更新 categories 和 allCategories 中对应的项
 * @param {Number} id 分类ID
 * @param {Object} newData 后端返回的更新后数据
 */
const updateLocalCategory = (id, newData) => {
  // 转换字段名：将 snake_case 转换为 camelCase（前端内部使用驼峰）
  const mappedData = {
    ...newData,
    // 转换 snake_case -> camelCase
    parentId: newData.parent_id,
    subjectId: newData.subject_id,
    subjectName: newData.subject_name,
    questionCount: newData.question_count,
    orderNum: newData.order_num  // 添加 orderNum 转换
  }

  // 更新 categories 数组
  const index = categories.value.findIndex(c => c.id === id)
  if (index !== -1) {
    // 保留原有的 children 引用（如果有），因为后端返回的数据可能不包含 children
    const oldChildren = categories.value[index].children
    categories.value[index] = { ...mappedData, children: oldChildren }
  }

  // 同步更新 allCategories 数组
  const allIndex = allCategories.value.findIndex(c => c.id === id)
  if (allIndex !== -1) {
    const oldChildren = allCategories.value[allIndex].children
    allCategories.value[allIndex] = { ...mappedData, children: oldChildren }
  }
}

/**
 * 删除分类
 */
const handleDelete = async (row) => {
  try {
    // 先检查引用数量
    const usageRes = await checkCategoryUsage(row.id)
    const usage = usageRes.code === 200 ? usageRes.data : 0
    
    let confirmMsg = `确认删除分类"${row.name}"吗？`
    if (usage > 0) {
      confirmMsg = `该分类被 ${usage} 道题目引用。删除后，这些题目的分类信息将不变，但无法再选择此分类。\n\n确认删除分类"${row.name}"吗？`
    }

    await showConfirm({
      title: '删除确认',
      message: confirmMsg,
      confirmText: '确定',
      cancelText: '取消',
      type: 'danger'
    })

    const response = await deleteCategory(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      // 保存树形视图展开状态
      const savedTreeExpandedKeys = getTreeExpandedKeys()

      await loadCategories()

      // 恢复树形视图展开状态（移除已删除的节点ID）
      restoreTreeExpandedKeys(savedTreeExpandedKeys.filter(id => id !== row.id))
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

/**
 * 计算分类及其所有子孙分类的题目数总和（支持三级分类）
 */
const getChildrenQuestionCount = (category) => {
  // 分类自身的题目数
  let total = category.questionCount || 0
  // 递归计算子分类的题目数
  if (category.children && category.children.length > 0) {
    for (const child of category.children) {
      total += getChildrenQuestionCount(child)
    }
  }
  return total
}

/**
 * 计算分类下所有子孙分类的总数量（支持三级分类）
 */
const getTotalChildrenCount = (category) => {
  let count = 0
  if (category.children && category.children.length > 0) {
    count = category.children.length
    for (const child of category.children) {
      if (child.children && child.children.length > 0) {
        count += child.children.length
      }
    }
  }
  return count
}

/**
 * 添加子分类（预填父分类和科目）
 */
const handleAddChild = async (parent) => {
  resetForm()
  form.subjectId = parent.subjectId
  form.parentId = parent.id
  await loadParentOptions(parent.subjectId, null)
  dialogMode.value = 'add'
  dialogVisible.value = true
}

/**
 * 初始化树形视图展开状态
 * 默认收起所有节点（空数组）
 */
const initTreeExpandedKeys = () => {
  treeExpandedKeys.value = []
}

/**
 * 树形视图拖拽节点处理
 * 功能已移除：拖拽排序功能不再使用
 * 排序通过编辑对话框中的 orderNum 字段实现
 */

// 组件挂载时加载数据
onMounted(async () => {
  await loadSubjectOptions()
  // 第一步：加载全部分类数据（用于科目筛选列表统计和分类数量统计）
  if (questionType.value === 'mock') {
    // 模拟题：收集所有科目的分类数据
    const allStats = []
    for (const subject of subjectOptions.value) {
      const response = await getMockCategoryStatsBySubject(subject.id)
      if (response.code === 200) {
        const stats = response.data?.stats || []
        stats.forEach(item => {
          allStats.push({
            id: `${subject.id}-${item.category}`,
            subjectId: subject.id,
            subjectName: subject.name,
            parentId: null,
            name: item.category,
            code: item.category.toLowerCase().replace(/\s+/g, '-'),
            questionCount: item.count,
            orderNum: 0,
            enabled: true
          })
        })
      }
    }
    allCategories.value = allStats
  } else {
    // 真题：使用真题 API
    const allResponse = await getAllCategories(questionType.value)
    if (allResponse.code === 200) {
      allCategories.value = (allResponse.data || []).map(item => ({
        ...item,
        parentId: item.parent_id,
        orderNum: item.order_num
      }))
    }
  }
  // 第二步：加载科目统计数据（用于科目筛选列表显示题目数）
  await loadCategoryStats()
  // 第三步：默认选中第一个科目（只影响显示）
  if (subjectOptions.value.length > 0) {
    filterSubjectId.value = subjectOptions.value[0].id
    // 第四步：加载选中科目的分类数据（用于显示）
    await loadCategories()
  }
  // 初始化树形视图展开状态
  initTreeExpandedKeys()
})
</script>

<style scoped>
/**
 * 分类管理页面样式
 * 大部分样式已迁移到Tailwind类，这里保留必要的CSS动画和深层样式
 */

/* 骨架屏容器 */
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* 骨架屏卡片 */
.skeleton-card {
  overflow: hidden;
}

/* 骨架屏闪烁动画 - 使用渐变流光效果 */
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgba(139, 111, 71, 0.06) 0%,
    rgba(139, 111, 71, 0.12) 35%,
    rgba(139, 111, 71, 0.18) 50%,
    rgba(139, 111, 71, 0.12) 65%,
    rgba(139, 111, 71, 0.06) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.8s ease-in-out infinite;
}

/* 骨架屏动画 */
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 树形视图加载渐入动画 */
.tree-fade-enter-active {
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}

.tree-fade-leave-active {
  transition: opacity 0.2s ease-in;
}

.tree-fade-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

.tree-fade-leave-to {
  opacity: 0;
}


/* 响应式布局 */
@media (max-width: 768px) {
  .max-w-\[1400px\] {
    padding: 16px 8px;
    height: auto;
    overflow: visible;
  }

  .max-w-\[1400px\] > .flex:first-child {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .max-w-\[1400px\] > .flex:first-child > .flex:last-child {
    flex-direction: column;
    width: 100%;
    gap: 16px;
  }

  .flex.gap-8 {
    flex-direction: column;
    gap: 24px;
  }

  .w-64 {
    width: 100%;
    position: static;
    height: auto;
    overflow: visible;
  }

  .bg-white.rounded-2xl {
    padding: 16px 24px;
  }
}
</style>
