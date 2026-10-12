<!--
  自定义分类管理页面
  按科目维护自定义的多级分类树，与大纲分类平行存在，仅管理员可访问。
-->
<template>
  <div class="custom-category-manage-page mx-auto max-w-[1400px] overflow-hidden px-4 py-5 sm:px-6 sm:py-8">
    <!-- 页面标题栏 -->
    <div class="custom-category-manage-header mb-6 flex flex-col items-stretch gap-4 border-b-2 border-accent/10 pb-5 lg:mb-8 lg:flex-row lg:items-center lg:justify-between lg:pb-6">
      <div class="flex flex-col gap-1">
        <h1 class="m-0 text-[1.75rem] font-semibold text-accent flex items-center">
          <span class="inline-block w-1.5 h-7 bg-gradient-to-b from-accent to-[#a88a5f] mr-4 rounded-sm"></span>
          自定义分类管理
        </h1>
        <span class="text-xs text-ink-mute ml-[calc(5px+16px)]">按科目维护自己定义的多级分类，与大纲分类并存</span>
      </div>
      <div class="custom-category-manage-actions flex flex-wrap items-center gap-2 sm:gap-3 lg:gap-6">
        <CustomButton class="md:hidden" :disabled="moveSaving" @click="subjectFilterVisible = true">
          <font-awesome-icon :icon="['fas', 'folder']" class="mr-1.5" />
          科目筛选
        </CustomButton>
        <CustomButton
          :disabled="!filterSubjectId || moveSaving || loading || codeRebuildLoading || draggingId !== null"
          :loading="codeRebuildLoading"
          @click="handleRebuildCodes"
        >
          <font-awesome-icon :icon="['fas', 'list-ol']" class="mr-1.5" />
          重排编码
        </CustomButton>
        <CustomButton type="primary" :disabled="moveSaving || draggingId !== null" @click="handleAdd">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
          新增分类
        </CustomButton>
      </div>
    </div>

    <!-- 左右分栏布局 -->
    <div class="custom-category-manage-layout flex items-start gap-8">
      <!-- 左侧筛选栏 -->
      <aside class="custom-category-manage-sidebar sticky top-4 w-64 flex-shrink-0">
        <CategorySubjectFilter
          :stats="subjectStats"
          :selected-id="filterSubjectId"
          :disabled="moveSaving"
          @select="handleStatClick"
        />
      </aside>

      <BottomSheet
        v-model:visible="subjectFilterVisible"
        title="科目筛选"
        max-height="min(78dvh, 680px)"
      >
        <CategorySubjectFilter
          :stats="subjectStats"
          :selected-id="filterSubjectId"
          :disabled="moveSaving"
          @select="handleMobileSubjectSelect"
        />
      </BottomSheet>

      <!-- 右侧主内容区 -->
      <main
        ref="contentRef"
        class="custom-category-manage-content content-scroll scrollbar-stable relative min-w-0 flex-1 overflow-y-auto"
        :aria-busy="loading || moveSaving"
        @dragover="handleContainerDragOver"
        @dragleave="handleContainerDragLeave"
        @drop="handleDrop"
      >
        <!-- 背景层次增强 -->
        <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <div class="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-accent/8 to-transparent rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3"></div>
          <div class="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-[rgba(64,158,255,0.05)] to-transparent rounded-full blur-3xl transform -translate-x-1/3 translate-y-1/3"></div>
          <div class="absolute inset-0 opacity-[0.03]" style="background-image: radial-gradient(var(--brand-accent) 1px, transparent 1px); background-size: 24px 24px;"></div>
        </div>

        <div v-if="loadError" class="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
          {{ loadError }}
          <CustomButton size="sm" type="text" :disabled="loading || moveSaving" @click="loadCategories()">重新读取分类</CustomButton>
        </div>

        <!-- 骨架屏 - 树形轮廓 -->
        <div v-if="loading" class="archive-panel">
          <div class="skeleton-container">
            <div
              v-for="i in 5"
              :key="i"
              class="flex items-center gap-3 px-3 py-2.5"
              :class="i === 1 ? 'pl-3' : i <= 3 ? 'pl-10' : 'pl-16'"
            >
              <div class="w-8 h-8 rounded-lg skeleton-shimmer flex-shrink-0"></div>
              <div
                class="h-4 rounded skeleton-shimmer"
                :class="i % 3 === 0 ? 'w-28' : i % 3 === 1 ? 'w-44' : 'w-36'"
              ></div>
              <div class="flex-1"></div>
              <div class="w-20 h-4 rounded skeleton-shimmer"></div>
            </div>
          </div>
        </div>

        <!-- 大纲视图 -->
        <template v-if="treeCategories.length > 0">
          <Transition name="tree-fade">
            <div class="archive-panel">
              <!-- 视图工具栏 -->
              <div class="flex gap-2 pb-3 mb-2 border-b border-accent/10">
                <CustomButton type="text" size="sm" @click="expandAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-down']" class="mr-1" />
                  全部展开
                </CustomButton>
                <CustomButton type="text" size="sm" @click="collapseAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="mr-1" />
                  全部收起
                </CustomButton>
              </div>

              <div class="drag-toolbar">
                <div class="drag-status" role="status" aria-live="polite">
                  {{ moveSaving ? '正在保存分类层级…' : dragMessage || moveMessage || '拖动左侧手柄：上下边缘排序，中部设为子分类；也可编辑父分类与排序。' }}
                </div>
                <div
                  data-category-root-drop
                  class="root-drop-zone"
                  :class="{ 'is-root-target': draggingId !== null && dropTarget?.targetId === null && dropTarget?.valid }"
                >移至顶级末尾</div>
              </div>

              <!-- 分类列表 -->
              <div class="outline-list" role="tree" aria-label="自定义分类层级大纲">
                <div
                  v-for="row in outlineRows"
                  :key="row.node.id"
                  class="outline-row group/row"
                  role="treeitem"
                  :aria-level="row.level + 1"
                  :aria-expanded="row.hasChildren ? isNodeExpanded(row.node.id) : undefined"
                  :data-category-id="row.node.id"
                  :class="{
                    'opacity-60': !row.node.enabled,
                    'is-drag-source': draggingIds.has(row.node.id),
                    'is-drop-before': dropTarget?.valid && dropTarget.targetId === row.node.id && dropTarget.position === 'before',
                    'is-drop-after': dropAfterRowId === row.node.id,
                    'is-drop-inside': dropTarget?.valid && dropTarget.targetId === row.node.id && dropTarget.position === 'inside',
                    'is-drop-invalid': dropTarget && !dropTarget.valid && dropTarget.targetId === row.node.id
                  }"
                  :style="{ paddingLeft: `${OUTLINER_CONTENT_BASE + row.level * OUTLINER_INDENT}px`, '--drop-indent': `${OUTLINER_CONTENT_BASE + (dropAfterRowId === row.node.id ? dropTargetLevel : row.level) * OUTLINER_INDENT}px` }"
                >
                  <!-- 仅延续仍有后续兄弟的祖先支线，末节点以圆角弯线收尾。 -->
                  <span
                    v-for="g in row.guideLevels"
                    :key="g"
                    class="outline-guide"
                    aria-hidden="true"
                    :style="{ left: `${OUTLINER_CONTENT_BASE + (g - 1) * OUTLINER_INDENT + OUTLINER_TOGGLE_SIZE / 2}px` }"
                  ></span>
                  <span
                    v-if="row.level > 0"
                    class="outline-branch"
                    :class="{ 'is-last': row.isLastSibling }"
                    aria-hidden="true"
                    :style="{
                      left: `${OUTLINER_CONTENT_BASE + (row.level - 1) * OUTLINER_INDENT + OUTLINER_TOGGLE_SIZE / 2}px`,
                      width: `${OUTLINER_INDENT - (row.hasChildren ? OUTLINER_TOGGLE_SIZE / 2 : 3)}px`
                    }"
                  ></span>
                  <span
                    v-if="row.hasChildren && isNodeExpanded(row.node.id)"
                    class="outline-child-stem"
                    aria-hidden="true"
                    :style="{ left: `${OUTLINER_CONTENT_BASE + row.level * OUTLINER_INDENT + OUTLINER_TOGGLE_SIZE / 2}px` }"
                  ></span>

                  <button
                    type="button"
                    class="outline-drag-handle"
                    :style="{ left: `${OUTLINER_BASE}px` }"
                    :draggable="canDrag"
                    :disabled="!canDrag"
                    :aria-label="`拖动 ${row.node.name}；点击或按回车编辑层级`"
                    title="拖动调整层级；点击编辑"
                    @dragstart.stop="startCategoryDrag($event, row.node)"
                    @dragend="resetDrag"
                    @click.stop="handleEdit(row.node)"
                  >
                    <font-awesome-icon :icon="['fas', 'grip']" aria-hidden="true" />
                  </button>

                  <!-- 展开/收起 -->
                  <button
                    v-if="row.hasChildren"
                    type="button"
                    class="outline-toggle"
                    :class="{ 'is-expanded': isNodeExpanded(row.node.id) }"
                    :aria-expanded="isNodeExpanded(row.node.id)"
                    :aria-label="(isNodeExpanded(row.node.id) ? '收起 ' : '展开 ') + row.node.name"
                    @click.stop="toggleExpand(row.node.id)"
                  >
                    <font-awesome-icon :icon="['fas', 'chevron-right']" />
                  </button>
                  <span v-else class="outline-toggle-placeholder" aria-hidden="true">
                    <span v-if="row.level > 0" class="outline-leaf-dot"></span>
                  </span>

                  <!-- 类型图标 -->
                  <div class="outline-icon">
                    <font-awesome-icon :icon="['fas', row.hasChildren ? 'folder-open' : 'file']" />
                  </div>

                  <!-- 名称与标签 -->
                  <span class="outline-name" :class="{ 'font-semibold': row.level === 0 }">{{ row.node.name }}</span>
                  <span class="outline-code">{{ row.node.code }}</span>

                  <span class="flex-1 min-w-4"></span>

                  <!-- 操作按钮：悬停行时浮现 -->
                  <div class="outline-actions">
                    <CustomTooltip content="添加子分类" placement="top">
                      <button type="button" class="outline-action-btn" :disabled="moveSaving || draggingId !== null" aria-label="添加子分类" @click.stop="handleAddChild(row.node)">
                        <font-awesome-icon :icon="['fas', 'plus']" />
                      </button>
                    </CustomTooltip>
                    <CustomTooltip content="编辑" placement="top">
                      <button type="button" class="outline-action-btn" :disabled="moveSaving || draggingId !== null" aria-label="编辑分类" @click.stop="handleEdit(row.node)">
                        <font-awesome-icon :icon="['fas', 'edit']" />
                      </button>
                    </CustomTooltip>
                    <CustomTooltip content="删除" placement="top">
                      <button
                        type="button"
                        class="outline-action-btn hover:text-[#c45656]! hover:bg-[rgba(196,86,86,0.08)]!"
                        aria-label="删除分类"
                        :disabled="moveSaving || draggingId !== null"
                        @click.stop="handleDelete(row.node)"
                      >
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </CustomTooltip>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </template>

        <!-- 空状态 -->
        <div v-if="!loading && !loadError && treeCategories.length === 0" class="
          relative flex flex-col items-center justify-center py-20
          bg-white/40 backdrop-blur-sm empty-in
          rounded-2xl border border-dashed border-accent/15
        ">
          <CustomEmpty description="暂无自定义分类" />
        </div>
      </main>
    </div>

    <!-- 编辑对话框 -->
    <ResponsiveDialog
      v-model:visible="dialogVisible"
      :title="dialogMode === 'add' ? '新增自定义分类' : '编辑自定义分类'"
      width="680px"
    >
      <div class="edit-form">
        <section class="edit-section">
          <div class="edit-section-heading">
            <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'folder-plus']" aria-hidden="true" />基本信息</h4>
          </div>

          <!-- 第一行：所属科目 + 父分类 -->
          <div class="edit-grid mb-4">
            <div>
              <label for="custom-category-subject" class="edit-label">
                所属科目
                <span class="text-red-500">*</span>
              </label>
              <CustomSelect
                id="custom-category-subject"
                v-model="form.subjectId"
                :options="subjectOptions.map(s => ({ label: s.name, value: s.id }))"
                placeholder="请选择科目"
                :disabled="dialogMode === 'edit'"
                @change="handleSubjectChange"
              />
              <p class="text-xs text-ink-mute mt-1.5" v-if="dialogMode === 'edit'">所属科目创建后不可修改</p>
            </div>
            <div>
              <label for="custom-category-parent" class="edit-label">
                父分类
              </label>
              <CustomSelect
                id="custom-category-parent"
                v-model="form.parentId"
                :options="[{ label: '无（顶级分类）', value: 0 }, ...parentOptions]"
                placeholder="无（顶级分类）"
                :disabled="!form.subjectId || parentLoading"
              />
              <p class="text-xs text-ink-mute mt-1.5">{{ parentLoading ? '正在加载父分类…' : '支持多级分类；移动父分类时，其子分类一起移动。' }}</p>
            </div>
          </div>

          <!-- 第二行：系统编码 + 分类名称 -->
          <div class="edit-grid">
            <div>
              <label for="custom-category-code" class="edit-label">
                分类 ID
              </label>
              <div
                id="custom-category-code"
                class="edit-readonly font-mono"
                aria-live="polite"
              >
                {{ dialogMode === 'edit' ? form.code : '保存后自动生成' }}
              </div>
              <p class="text-xs text-ink-mute mt-1.5">系统按科目、层级、编号和拼音首字母生成，无需手动填写。</p>
            </div>
            <CustomInput
              v-model="form.name"
              label="分类名称"
              placeholder="如：易错题"
              :maxlength="50"
              required
            />
          </div>
        </section>

        <section class="edit-section">
          <div class="edit-section-heading">
            <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'sliders-h']" aria-hidden="true" />排序与状态</h4>
          </div>
          <div class="edit-grid">
            <div>
              <label for="custom-category-order-num" class="edit-label">排序顺序</label>
              <CustomInputNumber
                id="custom-category-order-num"
                v-model="form.orderNum"
                :min="0"
                :max="9999"
              />
              <p class="edit-hint">数字越小，分类在列表中越靠前</p>
            </div>
            <div>
              <label for="custom-category-enabled" class="edit-label">是否启用</label>
              <div class="edit-state-row">
                <span class="text-sm text-ink-soft">{{ form.enabled ? '已启用' : '已禁用' }}</span>
                <CustomSwitch id="custom-category-enabled" v-model="form.enabled" aria-label="是否启用分类" />
              </div>
            </div>
          </div>
        </section>

        <section class="edit-section">
          <div class="edit-section-heading">
            <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'align-left']" aria-hidden="true" />详细信息</h4>
          </div>
          <div>
            <label for="custom-category-description" class="edit-label">
              分类描述
            </label>
            <textarea
              id="custom-category-description"
              v-model="form.description"
              class="edit-textarea"
              placeholder="请输入分类描述（可选）"
              :rows="3"
              :maxlength="255"
            ></textarea>
            <div class="edit-field-meta"><span class="edit-count">{{ form.description?.length || 0 }}/255</span></div>
          </div>
        </section>
      </div>

      <template #footer>
        <div class="edit-footer">
          <div class="edit-footer-actions">
            <CustomButton @click="dialogVisible = false">取消</CustomButton>
            <CustomButton type="primary" :loading="submitLoading" :disabled="parentLoading || parentLoadFailed" @click="handleSubmit">{{ dialogMode === 'add' ? '创建分类' : '保存修改' }}</CustomButton>
          </div>
        </div>
      </template>
    </ResponsiveDialog>
  </div>
</template>

<script setup lang="ts">
import type {
  ApiResponse,
  CustomCategoryNode,
  CustomCategoryTreeNode,
  Subject,
} from '@/types'

type OutlineRow = {
  node: CustomCategoryTreeNode
  level: number
  hasChildren: boolean
  isLastSibling: boolean
  guideLevels: number[]
}

/**
 * 自定义分类管理页面
 * 功能：按科目维护自定义的多级分类树（仅 ADMIN 可访问），与大纲分类互不影响。
 * 支持整棵子树拖拽和原子保存。
 */
import { ref, reactive, computed, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import BottomSheet from '@/components/basic/BottomSheet.vue'
import { MEDIA_QUERIES } from '@/shared/responsive/breakpoints'
import { useMediaQuery } from '@/shared/responsive/useViewport'

// 工具函数 / 常量
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useCategoryDrag } from '@/composables/useCategoryDrag'

// API 接口定义
import {
  getCustomCategoryTree,
  getCustomCategoryStats,
  getAvailableParentCustomCategories,
  createCustomCategory,
  updateCustomCategory,
  moveCustomCategory,
  deleteCustomCategory,
  rebuildCustomCategoryCodes,
} from '@/api/customCategory'
import { getAllSubjects } from '@/api/subject'

// 自定义组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import CustomSelect from '@/components/basic/Select.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import CustomEmpty from '@/components/basic/Empty.vue'
import CustomSwitch from '@/components/basic/Switch.vue'
import CustomInputNumber from '@/components/basic/InputNumber.vue'
import CustomTooltip from '@/components/basic/Tooltip.vue'
import CategorySubjectFilter from '@/components/business/CategorySubjectFilter.vue'
import '@/styles/edit-form.css'

const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 当前科目的扁平分类列表（拖拽与行渲染的数据源）
const categories = ref<CustomCategoryNode[]>([])

// 科目选项
const subjectOptions = ref<Subject[]>([])

// 各科目分类数量统计
const subjectStatsRaw = ref<{ subjectId: number; categoryCount: number; enabledCategoryCount: number }[]>([])

// 筛选科目ID
const filterSubjectId = ref<number | null>(null)
const subjectFilterVisible = ref(false)
const isWideViewport = useMediaQuery(MEDIA_QUERIES.wide)
watch(isWideViewport, (isWide) => {
  if (isWide) subjectFilterVisible.value = false
})

// 大纲视图展开的节点ID列表
const treeExpandedKeys = ref<(number | string)[]>([])

// 读取、移动保存分别管理，失败后的旧目录不可继续拖动。
const loading = ref(false)
const loadError = ref('')
const moveSaving = ref(false)
const moveMessage = ref('')
const contentRef = ref<HTMLElement | null>(null)
let loadVersion = 0
let disposed = false

// 对话框显示状态
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')

// 提交加载状态
const submitLoading = ref(false)
const deleteLoading = ref(false)
// 编码重排进行中，期间禁止拖动和其他写操作
const codeRebuildLoading = ref(false)

// 父分类选项
const parentOptions = ref<{ value: number; label: string }[]>([])
const parentLoading = ref(false)
const parentLoadFailed = ref(false)
let parentLoadVersion = 0

const canDrag = computed(() => !!filterSubjectId.value
  && !loading.value && !moveSaving.value && !submitLoading.value && !deleteLoading.value
  && !codeRebuildLoading.value
  && !dialogVisible.value && !loadError.value)
const {
  draggingId, draggingIds, dropTarget, dragMessage, canMove,
  handleDragStart, handleContainerDragOver, handleContainerDragLeave, handleDrop, resetDrag
} = useCategoryDrag({
  categories,
  enabled: canDrag,
  containerRef: contentRef,
  expandedKeys: treeExpandedKeys,
  onMove: (id, target) => handleMove(id, target)
})

const startCategoryDrag = (event: DragEvent, node: CustomCategoryNode) => {
  handleDragStart(event, node)
}

/** 把接口返回的分类树展平为拖拽所需的扁平列表。 */
const flattenTree = (nodes: CustomCategoryTreeNode[]): CustomCategoryNode[] => {
  const list: CustomCategoryNode[] = []
  const walk = (items: CustomCategoryTreeNode[]): void => {
    items.forEach(item => {
      list.push({
        id: item.id,
        subjectId: item.subjectId,
        subjectName: item.subjectName,
        parentId: item.parentId,
        parentName: item.parentName,
        name: item.name,
        code: item.code,
        description: item.description,
        orderNum: item.orderNum,
        enabled: item.enabled,
      })
      if (item.children.length > 0) walk(item.children)
    })
  }
  walk(nodes)
  return list
}

/** 把扁平分类列表组装成树，供大纲行渲染。 */
const treeCategories = computed(() => {
  const list = categories.value
  if (list.length === 0) return [] as CustomCategoryTreeNode[]

  const map = new Map<number, CustomCategoryTreeNode>()
  list.forEach(item => {
    map.set(item.id, { ...item, children: [] })
  })

  const tree: CustomCategoryTreeNode[] = []
  list.forEach(item => {
    const node = map.get(item.id)
    if (!node) return
    if (item.parentId && map.has(item.parentId)) {
      map.get(item.parentId)?.children.push(node)
    } else {
      tree.push(node)
    }
  })

  const sortChildren = (nodes: CustomCategoryTreeNode[]): void => {
    nodes.sort((a, b) => (a.orderNum || 0) - (b.orderNum || 0) || a.id - b.id)
    nodes.forEach(node => {
      if (node.children.length > 0) sortChildren(node.children)
    })
  }
  sortChildren(tree)

  return tree
})

/** 科目筛选列表的统计项（沿用 CategorySubjectFilter 需要的字段）。 */
const subjectStats = computed(() => subjectOptions.value.map(subject => {
  const stat = subjectStatsRaw.value.find(item => item.subjectId === subject.id)
  return {
    id: subject.id,
    name: subject.name,
    count: stat?.categoryCount ?? 0,
    enabledCount: stat?.enabledCategoryCount ?? 0,
    questionCount: stat?.categoryCount ?? 0,
  }
}))

// 表单数据
const form = reactive({
  id: null as number | null,
  subjectId: null as number | null,
  parentId: null as number | null,
  code: '',
  name: '',
  description: '',
  orderNum: 0,
  enabled: true,
})

/** 加载科目选项。 */
const loadSubjectOptions = async () => {
  try {
    const response = await getAllSubjects()
    if (!disposed && response.code === 200) {
      subjectOptions.value = response.data || []
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
  }
}

/** 加载各科目的自定义分类数量统计。 */
const loadSubjectStats = async () => {
  try {
    const response = await getCustomCategoryStats()
    if (disposed) return
    if (response.code === 200) {
      subjectStatsRaw.value = (response.data?.subjectStats || []).map(item => ({
        subjectId: item.subjectId,
        categoryCount: item.categoryCount,
        enabledCategoryCount: item.enabledCategoryCount,
      }))
    }
  } catch (error) {
    console.error('加载自定义分类统计失败:', error)
  }
}

/** 加载当前科目的自定义分类树。 */
const loadCategories = async () => {
  const subjectId = filterSubjectId.value
  if (!subjectId) return
  const version = ++loadVersion
  const isCurrent = () => !disposed && version === loadVersion && subjectId === filterSubjectId.value
  loading.value = true
  loadError.value = ''
  try {
    const response = await getCustomCategoryTree(subjectId)
    if (!isCurrent()) return
    categories.value = flattenTree(response.data || [])
  } catch (error) {
    console.error('读取自定义分类失败:', error)
    if (isCurrent()) {
      loadError.value = '自定义分类读取失败，当前列表可能已过期，请重新读取后再操作。'
    }
  } finally {
    if (isCurrent()) loading.value = false
  }
}

/** 点击科目筛选项。 */
const handleStatClick = async (subjectId: number | null) => {
  if (moveSaving.value) return
  resetDrag()
  moveMessage.value = ''
  filterSubjectId.value = subjectId
  categories.value = []
  treeExpandedKeys.value = []
  await loadCategories()
}

const handleMobileSubjectSelect = async (subjectId: number) => {
  subjectFilterVisible.value = false
  await handleStatClick(subjectId)
}

/** 重置表单。 */
const resetForm = () => {
  ++parentLoadVersion
  parentLoading.value = false
  form.id = null
  form.subjectId = filterSubjectId.value || null
  form.parentId = null
  form.code = ''
  form.name = ''
  form.description = ''
  form.orderNum = 0
  form.enabled = true
  parentOptions.value = []
  parentLoadFailed.value = false
}

/** 科目变更时加载可选父分类。 */
const handleSubjectChange = async () => {
  form.parentId = null
  if (form.subjectId) {
    await loadParentOptions(form.subjectId, form.id)
  } else {
    ++parentLoadVersion
    parentLoading.value = false
    parentOptions.value = []
  }
}

/** 加载可选父分类，标签使用完整层级路径。 */
const loadParentOptions = async (subjectId: number, excludeId: number | null = null) => {
  const version = ++parentLoadVersion
  parentLoading.value = true
  parentLoadFailed.value = false
  try {
    const response = await getAvailableParentCustomCategories(subjectId, excludeId)
    if (disposed || version !== parentLoadVersion) return
    const parents = response.data || []
    const byId = new Map(parents.map(parent => [parent.id, parent]))
    parentOptions.value = parents.map(parent => {
      const names: string[] = []
      const visited = new Set<number>()
      let node: CustomCategoryNode | undefined = parent
      while (node && !visited.has(node.id)) {
        visited.add(node.id)
        names.unshift(node.name)
        node = node.parentId == null ? undefined : byId.get(node.parentId)
      }
      return {
        value: parent.id,
        label: names.join(' / ') + (parent.enabled ? '' : '（已禁用）')
      }
    })
  } catch (error) {
    if (!disposed && version === parentLoadVersion) {
      parentLoadFailed.value = true
      showToast('父分类加载失败，请关闭弹窗后重试', 'error')
    }
  } finally {
    if (!disposed && version === parentLoadVersion) parentLoading.value = false
  }
}

/** 新增分类。 */
const handleAdd = () => {
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  dialogMode.value = 'add'
  dialogVisible.value = true
  if (form.subjectId) loadParentOptions(form.subjectId)
}

/** 新增子分类。 */
const handleAddChild = async (parent: CustomCategoryNode) => {
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  form.subjectId = parent.subjectId
  form.parentId = parent.id
  dialogMode.value = 'add'
  dialogVisible.value = true
  await loadParentOptions(parent.subjectId)
}

/** 编辑分类。 */
const handleEdit = async (row: CustomCategoryNode) => {
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  form.id = row.id
  form.subjectId = row.subjectId
  form.parentId = row.parentId || null
  form.code = row.code
  form.name = row.name
  form.description = row.description || ''
  form.orderNum = row.orderNum
  form.enabled = row.enabled

  dialogMode.value = 'edit'
  dialogVisible.value = true
  await loadParentOptions(row.subjectId, row.id)
}

/** 提交表单。 */
const handleSubmit = async () => {
  if (submitLoading.value || moveSaving.value || parentLoading.value || parentLoadFailed.value) return
  const subjectId = form.subjectId
  const name = form.name
  if (!subjectId) {
    showToast('请选择所属科目', 'warning')
    return
  }
  if (!name) {
    showToast('请输入分类名称', 'warning')
    return
  }

  submitLoading.value = true
  try {
    const data = {
      subjectId,
      parentId: form.parentId || null,
      name,
      description: form.description || null,
      orderNum: form.orderNum,
      enabled: form.enabled,
    }

    let response: ApiResponse<CustomCategoryNode> | null = null
    if (dialogMode.value === 'add') {
      response = await createCustomCategory(data)
    } else {
      if (form.id === null) return
      response = await updateCustomCategory(form.id, data)
    }

    if (response.code === 200) {
      showToast(dialogMode.value === 'add' ? '创建成功' : '更新成功', 'success')
      dialogVisible.value = false
      const savedTreeExpandedKeys = [...treeExpandedKeys.value]
      await Promise.all([loadSubjectStats(), loadCategories()])
      treeExpandedKeys.value = savedTreeExpandedKeys
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

/** 删除分类。 */
const handleDelete = async (row: CustomCategoryNode) => {
  if (moveSaving.value || deleteLoading.value || submitLoading.value || draggingId.value !== null) return
  deleteLoading.value = true
  try {
    const confirmed = await showConfirm({
      title: '删除确认',
      message: `确认删除分类“${row.name}”吗？存在子分类时需要先删除子分类。`,
      confirmText: '确定',
      cancelText: '取消',
      type: 'danger'
    })
    if (!confirmed) return

    const response = await deleteCustomCategory(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      const savedTreeExpandedKeys = treeExpandedKeys.value.filter(id => id !== row.id)
      await Promise.all([loadSubjectStats(), loadCategories()])
      treeExpandedKeys.value = savedTreeExpandedKeys
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      showToast('删除失败', 'error')
    }
  } finally {
    deleteLoading.value = false
  }
}

/** 重排当前科目的分类编码。 */
const handleRebuildCodes = async () => {
  const subjectId = filterSubjectId.value
  if (!subjectId || codeRebuildLoading.value || moveSaving.value || draggingId.value !== null) return

  const confirmed = await showConfirm({
    title: '重排编码确认',
    message: '将按当前显示顺序重排该科目所有同级分类编号（如 01、02、03），分类 ID 会随之变化。\n\n分类名称与层级不受影响。确认继续吗？',
    confirmText: '确定',
    cancelText: '取消'
  })
  if (!confirmed) return

  const savedTreeExpandedKeys = [...treeExpandedKeys.value]
  const scrollTop = contentRef.value?.scrollTop ?? 0
  codeRebuildLoading.value = true
  ++loadVersion
  try {
    const response = await rebuildCustomCategoryCodes(subjectId)
    if (disposed) return
    categories.value = response.data || []
    loadError.value = ''
    showToast('编码重排成功', 'success')
  } catch (error) {
    console.error('重排编码失败:', error)
    showToast('重排编码失败', 'error')
  } finally {
    if (!disposed) {
      treeExpandedKeys.value = savedTreeExpandedKeys
      await nextTick()
      if (contentRef.value) contentRef.value.scrollTop = scrollTop
      codeRebuildLoading.value = false
    }
  }
}

// ============ 大纲视图 ============

// 手柄独占固定左列，树线从展开控件向下连接，不穿过手柄。
const OUTLINER_BASE = 12
const OUTLINER_INDENT = 24
const OUTLINER_TOGGLE_SIZE = 20
const OUTLINER_CONTENT_BASE = OUTLINER_BASE + 30

/** 扁平化大纲行：按展开状态把树铺平成行列表。 */
const outlineRows = computed(() => {
  const rows: OutlineRow[] = []
  const walk = (nodes: CustomCategoryTreeNode[], level: number, guideLevels: number[] = []): void => {
    nodes.forEach((node, index) => {
      const children = node.children || []
      const hasChildren = children.length > 0
      const isLastSibling = index === nodes.length - 1
      rows.push({ node, level, hasChildren, isLastSibling, guideLevels })
      if (hasChildren && treeExpandedKeys.value.includes(node.id)) {
        const childGuides = level > 0 && !isLastSibling ? [...guideLevels, level] : guideLevels
        walk(children, level + 1, childGuides)
      }
    })
  }
  walk(treeCategories.value, 0)
  return rows
})

// 放在展开节点之后时，插入线画在整棵可见子树下方。
const dropTargetLevel = computed(() => outlineRows.value.find(row => row.node.id === dropTarget.value?.targetId)?.level ?? 0)
const dropAfterRowId = computed(() => {
  if (!dropTarget.value?.valid || dropTarget.value.position !== 'after') return null
  const rows = outlineRows.value
  const index = rows.findIndex(row => row.node.id === dropTarget.value?.targetId)
  if (index < 0) return null
  let last = index
  while (last + 1 < rows.length && rows[last + 1].level > rows[index].level) last++
  return rows[last].node.id
})

const isNodeExpanded = (id: number | string) => treeExpandedKeys.value.includes(id)

const toggleExpand = (id: number | string) => {
  const index = treeExpandedKeys.value.indexOf(id)
  if (index > -1) {
    treeExpandedKeys.value.splice(index, 1)
  } else {
    treeExpandedKeys.value.push(id)
  }
}

/** 递归获取所有树节点ID。 */
const getAllTreeNodes = (nodes: CustomCategoryTreeNode[]) => {
  const ids: (number | string)[] = []
  const traverse = (list: CustomCategoryTreeNode[]): void => {
    list.forEach(node => {
      ids.push(node.id)
      if (node.children.length > 0) traverse(node.children)
    })
  }
  traverse(nodes)
  return ids
}

const expandAllTree = () => {
  treeExpandedKeys.value = getAllTreeNodes(treeCategories.value)
}

const collapseAllTree = () => {
  treeExpandedKeys.value = []
}

/** 松手提交一次移动命令；等待期间保持原树，服务端成功后才更新布局。 */
const handleMove = async (id: number, target: { targetId?: number | null; position: 'before' | 'inside' | 'after' }) => {
  // 请求入口再次按最新数据检查；无实际变化时不进入保存态，也不发送或刷新请求。
  if (!canDrag.value || !canMove(id, target)) return
  const savedKeys = [...treeExpandedKeys.value]
  const scrollTop = contentRef.value?.scrollTop ?? 0
  moveSaving.value = true
  moveMessage.value = ''
  ++loadVersion
  try {
    const response = await moveCustomCategory(id, target)
    if (disposed) return
    categories.value = response.data || []
    loadError.value = ''
    moveMessage.value = '分类层级与顺序已保存'
  } catch (error) {
    if (disposed) return
    // 网络中断不等于未提交；只重新读取，不重放写请求。
    await loadCategories()
    if (disposed) return
    moveMessage.value = loadError.value
      ? '无法确认移动结果，请重新读取分类后再操作。'
      : '移动请求未确认成功，已重新读取服务端布局，请核对结果。'
  } finally {
    if (!disposed) {
      const byId = new Map(categories.value.map(item => [item.id, item]))
      const keys = new Set(savedKeys.filter(key => byId.has(key)))
      const visited = new Set([id])
      let parentId = byId.get(id)?.parentId
      while (parentId && !visited.has(parentId) && byId.has(parentId)) {
        visited.add(parentId)
        keys.add(parentId)
        parentId = byId.get(parentId)?.parentId
      }
      treeExpandedKeys.value = [...keys]
      await nextTick()
      if (contentRef.value) contentRef.value.scrollTop = scrollTop
      moveSaving.value = false
    }
  }
}

onMounted(async () => {
  await Promise.all([loadSubjectOptions(), loadSubjectStats()])
  if (disposed) return
  if (subjectOptions.value.length > 0) {
    filterSubjectId.value = subjectOptions.value[0].id
    await loadCategories()
  }
})

onBeforeUnmount(() => {
  disposed = true
  ++loadVersion
  ++parentLoadVersion
})
</script>

<style scoped>
/**
 * 自定义分类管理页面样式。
 * 大纲列表、拖拽反馈与档案面板样式与大纲分类管理页保持一致。
 */

/* 骨架屏容器 */
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

/* 毛玻璃档案面板：树容器与骨架屏共用 */
.archive-panel {
  position: relative;
  padding: 1.5rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: linear-gradient(
    to bottom right,
    rgba(255, 255, 255, 0.9),
    color-mix(in srgb, var(--brand-accent) 0.6%, transparent)
  );
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow:
    0 2px 16px color-mix(in srgb, var(--brand-accent) 6%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.archive-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -10;
  border-radius: 1rem;
  padding: 1px;
  background: linear-gradient(to bottom right, rgba(255, 255, 255, 0.4), transparent);
}

/* ============ 大纲列表 ============ */
.outline-list {
  --outline-line-color: #d7c9b6;
  position: relative;
}

.outline-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 7px;
  padding-bottom: 7px;
  padding-right: 12px;
  border-radius: 10px;
  /* 不逐行位移或延迟进场，否则相邻行的树线会暂时断开。 */
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.outline-row:hover {
  background-color: rgba(255, 255, 255, 0.6);
}

/* 拖拽只改变反馈，不在每次 dragover 时重排 DOM，避免落点跳动。 */
.drag-toolbar {
  position: sticky;
  top: 0;
  z-index: 3;
  padding: 8px 0;
  background: #fffdf9;
  border-radius: 8px;
}

.drag-status {
  min-height: 36px;
  padding: 0 8px 6px;
  font-size: 12px;
  color: #725937;
}

.root-drop-zone {
  padding: 8px 12px;
  border: 1px dashed color-mix(in srgb, var(--brand-accent) 35%, transparent);
  border-radius: 8px;
  text-align: center;
  color: #8b6f47;
  font-size: 12px;
}

.root-drop-zone.is-root-target,
.outline-row.is-drop-inside {
  background: #f3eadb;
  outline: 2px solid #8b6f47;
  outline-offset: -2px;
}

.outline-drag-handle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 24px;
  height: 28px;
  border: 0;
  border-radius: 5px;
  color: #a89880;
  background: transparent;
  cursor: grab;
}

.outline-drag-handle:active { cursor: grabbing; }

.outline-drag-handle:focus-visible,
.outline-action-btn:focus-visible {
  outline: 2px solid #8b6f47;
  outline-offset: 2px;
}

.outline-drag-handle:disabled,
.outline-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.outline-row.is-drag-source { opacity: 0.4; }

.outline-row.is-drop-invalid {
  background: #fff0ed;
  outline: 1px dashed #c45656;
  outline-offset: -1px;
}

.outline-row.is-drop-before::before,
.outline-row.is-drop-after::after {
  content: '';
  position: absolute;
  left: var(--drop-indent);
  right: 12px;
  height: 3px;
  background: #8b6f47;
  border-radius: 2px;
  pointer-events: none;
  z-index: 2;
}

.outline-row.is-drop-before::before { top: -1px; }
.outline-row.is-drop-after::after { bottom: -1px; }

/* 相邻行无间隙接续；分支仅连接到展开按钮或叶节点圆点。 */
.outline-guide,
.outline-child-stem,
.outline-branch {
  position: absolute;
  pointer-events: none;
}

.outline-guide,
.outline-child-stem {
  bottom: 0;
  width: 1px;
  background: var(--outline-line-color);
}

.outline-guide { top: 0; }
.outline-child-stem { top: calc(50% + 10px); }

.outline-branch {
  top: 0;
  bottom: 0;
}

.outline-branch::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  border-left: 1px solid var(--outline-line-color);
  border-bottom: 1px solid var(--outline-line-color);
}

.outline-branch.is-last::before { border-bottom-left-radius: 7px; }

.outline-branch:not(.is-last)::after {
  content: '';
  position: absolute;
  top: 50%;
  bottom: 0;
  left: 0;
  width: 1px;
  background: var(--outline-line-color);
}

/* 展开/收起 */
.outline-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #8b6f47;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.outline-toggle:hover {
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
}

.outline-toggle.is-expanded {
  transform: rotate(90deg);
}

.outline-toggle-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.outline-leaf-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--outline-line-color);
}

/* 类型图标 */
.outline-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand-accent) 12%, transparent), color-mix(in srgb, var(--brand-accent) 5%, transparent));
  color: #8b6f47;
  font-size: 11px;
  transition: transform 0.2s ease;
}

.outline-row:hover .outline-icon {
  transform: scale(1.06);
}

/* 名称与编码 */
.outline-name {
  min-width: 0;
  font-size: 14px;
  color: var(--brand-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.outline-code {
  flex-shrink: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  color: #a89880;
  border: 1px solid color-mix(in srgb, var(--brand-accent) 18%, transparent);
  padding: 1px 6px;
  border-radius: 4px;
}

/* 操作按钮：悬停行时浮现 */
.outline-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.outline-row:hover .outline-actions,
.outline-actions:focus-within {
  opacity: 1;
}

.outline-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--brand-ink-mute);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.outline-action-btn:hover {
  color: #8b6f47;
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
}

@media (max-width: 1023px), (pointer: coarse) {
  .outline-actions {
    opacity: 1;
  }
}

/* 空状态浮现 */
@keyframes empty-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-in {
  animation: empty-in 0.4s ease-out backwards;
}

/* 内容区滚动条：与项目侧边栏一致的细滚动条 */
.content-scroll::-webkit-scrollbar {
  width: 6px;
}

.content-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.content-scroll::-webkit-scrollbar-thumb {
  background-color: color-mix(in srgb, var(--brand-accent) 15%, transparent);
  border-radius: 3px;
}

.content-scroll::-webkit-scrollbar-thumb:hover {
  background-color: color-mix(in srgb, var(--brand-accent) 30%, transparent);
}

@media (prefers-reduced-motion: reduce) {
  .outline-row,
  .empty-in {
    animation: none;
  }
}

/* 骨架屏闪烁动画 - 使用渐变流光效果 */
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--brand-accent) 6%, transparent) 0%,
    color-mix(in srgb, var(--brand-accent) 12%, transparent) 35%,
    color-mix(in srgb, var(--brand-accent) 18%, transparent) 50%,
    color-mix(in srgb, var(--brand-accent) 12%, transparent) 65%,
    color-mix(in srgb, var(--brand-accent) 6%, transparent) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.8s ease-in-out infinite;
}

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

/* 页面在桌面端保留独立内容滚动，窄屏改用浏览器原生纵向滚动。 */
.custom-category-manage-page {
  height: var(--app-page-height);
}

.custom-category-manage-content {
  height: calc(var(--app-page-height) - 136px);
}

@media (max-width: 1023px) {
  .custom-category-manage-page {
    min-height: var(--app-page-height);
    height: auto;
    overflow: visible;
  }

  .custom-category-manage-layout {
    flex-direction: column;
    gap: 20px;
  }

  .custom-category-manage-sidebar {
    position: static;
    width: 100%;
  }

  .custom-category-manage-content {
    width: 100%;
    height: auto;
    overflow: visible;
  }
}

@media (max-width: 639px) {
  .custom-category-manage-actions {
    align-items: stretch;
  }

  .custom-category-manage-actions :deep(button) {
    flex: 1 1 auto;
  }

  .outline-row {
    padding-right: 6px;
  }

  .outline-code {
    display: none;
  }
}
</style>
