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
        <CustomRadioGroup v-model="questionType" aria-label="题目类型" :disabled="moveSaving" :options="[
          { label: '真题', value: 'exam' },
          { label: '模拟题', value: 'mock' }
        ]" @change="handleQuestionTypeChange" />
        <CustomButton v-if="questionType === 'exam'" type="primary" :disabled="moveSaving || draggingId !== null" @click="handleAdd">
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
            <button
              v-for="stat in subjectStats"
              :key="stat.id"
              type="button"
              class="flex w-full items-center justify-between border-0 bg-transparent px-3 py-2.5 text-left rounded-lg cursor-pointer transition-all duration-200"
              :class="[filterSubjectId === stat.id ? 'bg-gradient-to-r from-[rgba(139,111,71,0.12)] to-[rgba(139,111,71,0.06)]' : 'hover:bg-[rgba(139,111,71,0.06)]', { 'pointer-events-none opacity-60': moveSaving }]"
              :aria-disabled="moveSaving"
              @click="handleStatClick(stat.id)"
              @keydown.enter.prevent="handleStatClick(stat.id)"
              @keydown.space.prevent="handleStatClick(stat.id)"
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
            </button>
          </div>
        </div>

      </aside>

      <!-- 右侧主内容区 -->
      <main
        ref="contentRef"
        class="flex-1 min-w-0 relative h-[calc(100vh-60px-128px)] overflow-y-auto content-scroll"
        :aria-busy="loading || moveSaving"
        @dragover="handleContainerDragOver"
        @dragleave="handleContainerDragLeave"
        @drop="handleDrop"
      >
        <!-- 背景层次增强 -->
        <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <!-- 右上角暖色光晕 -->
          <div class="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-[rgba(139,111,71,0.08)] to-transparent rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3"></div>
          <!-- 左下角冷色光晕 -->
          <div class="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-[rgba(64,158,255,0.05)] to-transparent rounded-full blur-3xl transform -translate-x-1/3 translate-y-1/3"></div>
          <!-- 几何网格纹理 -->
          <div class="absolute inset-0 opacity-[0.03]" style="background-image: radial-gradient(#8B6F47 1px, transparent 1px); background-size: 24px 24px;"></div>
        </div>

        <div v-if="categoryLoadError" class="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
          {{ categoryLoadError }}
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
            <!-- 统一的背景容器 -->
            <div class="archive-panel">
              <!-- 视图工具栏 -->
              <div class="flex gap-2 pb-3 mb-2 border-b border-[rgba(139,111,71,0.1)]">
                <CustomButton type="text" size="sm" @click="expandAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-down']" class="mr-1" />
                  全部展开
                </CustomButton>
                <CustomButton type="text" size="sm" @click="collapseAllTree">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="mr-1" />
                  全部收起
                </CustomButton>
              </div>

              <div v-if="questionType === 'exam'" class="drag-toolbar">
                <div class="drag-status" role="status" aria-live="polite">
                  {{ moveSaving ? '正在保存分类层级…' : dragMessage || moveMessage || '拖动左侧手柄：上下边缘排序，中部设为子分类；也可编辑父分类与排序。' }}
                </div>
                <div
                  data-category-root-drop
                  class="root-drop-zone"
                  :class="{ 'is-root-target': draggingId !== null && dropTarget?.targetId === null && dropTarget?.valid }"
                >移至顶级末尾</div>
              </div>

              <!-- 大纲列表 -->
              <div class="outline-list" role="tree" aria-label="分类层级大纲">
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
                    'is-drag-source': typeof row.node.id === 'number' && draggingIds.has(row.node.id),
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
                    v-if="questionType === 'exam'"
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
                  <span v-if="questionType === 'exam'" class="outline-code">{{ row.node.code }}</span>
                  <CustomTag v-if="row.level === 0 && row.node.subjectName" type="info" class="ml-1">
                    {{ row.node.subjectName }}
                  </CustomTag>

                  <span class="flex-1 min-w-4"></span>

                  <span class="outline-count">{{ getChildrenQuestionCount(row.node) }}题</span>

                  <!-- 操作按钮：仅真题模式显示，悬停行时浮现 -->
                  <div v-if="questionType === 'exam'" class="outline-actions">
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
        <div v-if="!loading && !categoryLoadError && treeCategories.length === 0" class="
          relative flex flex-col items-center justify-center py-20
          bg-white/40 backdrop-blur-sm empty-in
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
              <label for="category-subject" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                所属科目
                <span class="text-red-500">*</span>
              </label>
              <CustomSelect
                id="category-subject"
                v-model="form.subjectId"
                :options="subjectOptions.map(s => ({ label: s.name, value: s.id }))"
                placeholder="请选择科目"
                :disabled="dialogMode === 'edit'"
                @change="handleSubjectChange"
              />
              <p class="text-xs text-[#999] mt-1.5" v-if="dialogMode === 'edit'">所属科目创建后不可修改</p>
            </div>
            <div>
              <label for="category-parent" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                父分类
              </label>
              <select
                id="category-parent"
                v-model="form.parentId"
                class="w-full h-[42px] px-3 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/20 disabled:opacity-50"
                :disabled="!form.subjectId || parentLoading"
              >
                <option :value="null">无（顶级分类）</option>
                <option v-for="parent in parentOptions" :key="parent.value" :value="parent.value">{{ parent.label }}</option>
              </select>
              <p class="text-xs text-[#999] mt-1.5">{{ parentLoading ? '正在加载父分类…' : '支持多级分类；移动父分类时，其子分类一起移动。' }}</p>
            </div>
          </div>

          <!-- 第二行：系统编码 + 分类名称 -->
          <div class="grid grid-cols-2 gap-5">
            <div>
              <label for="category-code" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                分类 ID
              </label>
              <div
                id="category-code"
                class="w-full min-h-[42px] flex items-center px-4 py-2.5 rounded-lg bg-gray-100 border border-gray-200 text-sm text-gray-600 font-mono break-all"
                aria-live="polite"
              >
                {{ dialogMode === 'edit' ? form.code : '保存后自动生成' }}
              </div>
              <p class="text-xs text-[#999] mt-1.5">系统按科目、层级、编号和拼音首字母生成，无需手动填写。</p>
            </div>
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
              <label for="category-order-num" class="text-sm font-medium text-gray-700">排序顺序</label>
              <CustomInputNumber
                id="category-order-num"
                v-model="form.orderNum"
                :min="0"
                :max="9999"
              />
              <span class="text-xs text-[#999]">数字越小越靠前</span>
            </div>
            <div class="flex items-center gap-3 px-4 py-2.5 bg-[rgba(139,111,71,0.04)] rounded-xl">
              <CustomSwitch id="category-enabled" v-model="form.enabled" aria-label="是否启用分类" />
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
          <CustomButton type="primary" :loading="submitLoading" :disabled="parentLoading || parentLoadFailed" @click="handleSubmit">
            确定
          </CustomButton>
        </div>
      </template>
    </CustomDialog>
  </div>
</template>

<script setup lang="ts">
import type { CategoryNode, CategoryMoveRequest, Subject } from '@/types'
type CategoryView = Omit<CategoryNode, 'id' | 'code'> & { id: number | string; code?: string }
type CategoryViewTree = CategoryView & { children: CategoryViewTree[] }
type OutlineRow = { node: CategoryViewTree; level: number; hasChildren: boolean; isLastSibling: boolean; guideLevels: number[] }

/**
 * 分类标签管理页面
 * 功能：按科目管理分类标签的CRUD操作（仅ADMIN可访问）
 * 大纲支持整棵子树拖拽和原子保存；模拟题分类仅展示。
 */
import { ref, reactive, computed, nextTick, onBeforeUnmount, onMounted } from 'vue'

// 工具函数 / 常量
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useCategoryDrag } from '@/composables/useCategoryDrag'

// API 接口定义
import {
  getAllCategories,
  getCategoriesBySubject,
  createCategory,
  updateCategory,
  moveCategory,
  deleteCategory,
  checkCategoryUsage,
  getAvailableParentCategories,
  getCategoryStats
} from '@/api/category'
import { getAllSubjects } from '@/api/subject'
import { getMockCategoryStatsBySubject, getMockSubjectStats } from '@/api/mock'

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

const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 所有分类列表（用于统计）
const allCategories = ref<CategoryView[]>([])

// 当前显示的分类列表（筛选后）
const categories = ref<CategoryView[]>([])

// 科目选项
const subjectOptions = ref<Subject[]>([])

// 筛选科目ID
const filterSubjectId = ref<number | null>(null)

// 题目类型筛选（exam=真题, mock=模拟题）
const questionType = ref<'exam' | 'mock'>('exam')

// 大纲视图展开的节点ID列表（响应式，用于保持展开状态）
const treeExpandedKeys = ref<(number | string)[]>([])

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
 * 获取大纲视图当前展开的节点ID列表
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
const restoreTreeExpandedKeys = (keys: (number | string)[]) => {
  if (!keys) return
  treeExpandedKeys.value = [...keys]
}

/**
 * 递归获取所有树节点ID
 */
const getAllTreeNodes = (nodes: CategoryViewTree[]) => {
  const ids: (number | string)[] = []
  const traverse = (list: CategoryViewTree[]): void => {
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
const categoryStats = ref<{ subjectStats: {subjectId: number; subjectName?: string | null; questionCount: number}[]; totalQuestionCount: number }>({
  subjectStats: [],  // 各科目题目数
  totalQuestionCount: 0  // 全局题目总数
})

// 读取、移动保存分别管理，失败后的旧目录不可继续拖动。
const loading = ref(false)
const categoryLoadError = ref('')
const moveSaving = ref(false)
const moveMessage = ref('')
const contentRef = ref<HTMLElement | null>(null)
let categoryLoadVersion = 0
let statsLoadVersion = 0
let viewChangeVersion = 0
let disposed = false

// 对话框显示状态
const dialogVisible = ref(false)

// 对话框模式（add/edit）
const dialogMode = ref('add')

// 提交加载状态
const submitLoading = ref(false)
const deleteLoading = ref(false)

// 父分类选项
const parentOptions = ref<{value: number; label: string}[]>([])

const parentLoading = ref(false)
const parentLoadFailed = ref(false)
let parentLoadVersion = 0

const canDrag = computed(() => questionType.value === 'exam' && !!filterSubjectId.value
  && !loading.value && !moveSaving.value && !submitLoading.value && !deleteLoading.value
  && !dialogVisible.value && !categoryLoadError.value)
const {
  draggingId, draggingIds, dropTarget, dragMessage, canMove,
  handleDragStart, handleContainerDragOver, handleContainerDragLeave, handleDrop, resetDrag
} = useCategoryDrag({
  categories: computed(() => categories.value.filter((node): node is CategoryNode => typeof node.id === 'number' && typeof node.code === 'string')), enabled: canDrag, containerRef: contentRef, expandedKeys: treeExpandedKeys,
  onMove: (id, target) => handleMove(id, target)
})

/**
 * 将分类数据转换为树形结构或分组结构
 * 模拟题模式：按科目分组显示（扁平结构）
 * 真题模式：构建树形结构（支持多层级）
 */
const startCategoryDrag = (event: DragEvent, node: CategoryView) => {
  if (typeof node.id !== 'number' || typeof node.code !== 'string') return
  handleDragStart(event, { ...node, id: node.id, code: node.code })
}

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
  const map = new Map<number | string, CategoryViewTree>()
  list.forEach(item => {
    map.set(item.id, { ...item, children: [] })
  })

  const tree: CategoryViewTree[] = []
  list.forEach(item => {
    const node = map.get(item.id)
    if (!node) return
    if (item.parentId && map.has(item.parentId)) {
      map.get(item.parentId)?.children.push(node)
    } else {
      tree.push(node)
    }
  })

  // 对每层按orderNum排序
  const sortChildren = (nodes: CategoryViewTree[]): void => {
    nodes.sort((a, b) => (a.orderNum || 0) - (b.orderNum || 0) || Number(a.id) - Number(b.id))
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
  id: null as number | null,
  subjectId: null as number | null,
  parentId: null as number | null,
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
    if (!disposed && response.code === 200) {
      subjectOptions.value = response.data || []
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
  }
}

/**
 * 统一处理 API 已转换为驼峰命名的分类数据
 */
const normalizeCategory = (item: CategoryNode) => ({
  ...item,
  parentId: item.parentId ?? null,
  subjectId: item.subjectId,
  subjectName: item.subjectName,
  questionCount: item.questionCount ?? 0,
  subtreeQuestionCount: item.subtreeQuestionCount ?? item.questionCount ?? 0,
  orderNum: item.orderNum ?? 0
})

/**
 * 用指定科目的最新分类数据替换全部分类中的对应科目
 */
const replaceSubjectCategories = (subjectId: number | null, subjectCategories: CategoryView[]) => {
  allCategories.value = [
    ...allCategories.value.filter(item => item.subjectId !== subjectId),
    ...subjectCategories
  ]
}

/**
 * 加载科目统计数据（用于科目筛选列表）
 * 根据题目类型使用不同的 API
 */
const loadCategoryStats = async () => {
  const type = questionType.value
  const version = ++statsLoadVersion
  try {
    if (type === 'mock') {
      // 模拟题：使用 /api/mock/subject-stats 获取每个科目的正确题目数量（去重后）
      const response = await getMockSubjectStats()
      if (disposed || version !== statsLoadVersion || type !== questionType.value) return
      if (response.code === 200) {
        const stats = response.data || []
        categoryStats.value = {
          subjectStats: stats.map(s => ({
            subjectId: s.subjectId,
            subjectName: s.subjectName,
            questionCount: s.count
          })),
          totalQuestionCount: stats.reduce((sum, s) => sum + s.count, 0)
        }
      }
    } else {
      // 真题：使用真题 API
      const response = await getCategoryStats(type)
      if (disposed || version !== statsLoadVersion || type !== questionType.value) return
      if (response.code === 200) {
        categoryStats.value = {
          subjectStats: response.data?.subjectStats?.map(s => ({
            subjectId: s.subjectId,
            subjectName: s.subjectName,
            questionCount: s.questionCount
          })) || [],
          totalQuestionCount: response.data?.totalQuestionCount || 0
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
const loadCategories = async ({ background = false } = {}) => {
  const subjectId = filterSubjectId.value
  const type = questionType.value
  const version = ++categoryLoadVersion
  const isCurrent = () => !disposed && version === categoryLoadVersion
    && subjectId === filterSubjectId.value && type === questionType.value
  loading.value = !background
  categoryLoadError.value = ''
  try {
    let list: CategoryView[]
    if (type === 'mock') {
      const subjects = subjectId
        ? subjectOptions.value.filter(subject => subject.id === subjectId)
        : [...subjectOptions.value]
      list = []
      for (const subject of subjects) {
        const response = await getMockCategoryStatsBySubject(subject.id)
        if (!isCurrent()) return false
        list.push(...(response.data?.stats || []).map(item => ({
          id: `${subject.id}-${item.category}`,
          subjectId: subject.id,
          subjectName: subject.name,
          parentId: null as number | null,
          name: item.category,
          orderNum: 0,
          enabled: true,
          questionCount: item.count,
          subtreeQuestionCount: item.count
        })))
      }
    } else {
      const response = subjectId
        ? await getCategoriesBySubject(subjectId, type)
        : await getAllCategories(type)
      list = (response.data || []).map(normalizeCategory)
    }
    if (!isCurrent()) return false
    categories.value = list
    if (subjectId) replaceSubjectCategories(subjectId, list)
    else allCategories.value = list
    return true
  } catch (error) {
    if (isCurrent()) {
      categoryLoadError.value = '分类读取失败，当前列表可能已过期，请重新读取后再操作。'
    }
    return false
  } finally {
    if (isCurrent()) loading.value = false
  }
}

/**
 * 题目类型切换处理
 * 切换时需要更新当前显示的分类
 */
const handleQuestionTypeChange = async () => {
  if (moveSaving.value) return
  const version = ++viewChangeVersion
  resetDrag()
  moveMessage.value = ''
  categories.value = []
  allCategories.value = []
  categoryStats.value = { subjectStats: [], totalQuestionCount: 0 }
  filterSubjectId.value = null
  initTreeExpandedKeys()
  await Promise.all([loadCategoryStats(), loadCategories()])
  if (disposed || version !== viewChangeVersion) return
  if (subjectOptions.value.length > 0) {
    filterSubjectId.value = subjectOptions.value[0].id
    categories.value = []
    await loadCategories()
  }
}

/**
 * 点击统计卡片筛选
 */
const handleStatClick = async (subjectId: number | null) => {
  if (moveSaving.value) return
  ++viewChangeVersion
  resetDrag()
  moveMessage.value = ''
  filterSubjectId.value = subjectId
  categories.value = []
  initTreeExpandedKeys()
  await loadCategories()
}

/**
 * 重置表单
 */
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

/**
 * 科目变更时加载可选父分类
 */
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

/**
 * 加载可选父分类
 */
const loadParentOptions = async (subjectId: number, excludeId: number | null = null) => {
  const version = ++parentLoadVersion
  parentLoading.value = true
  parentLoadFailed.value = false
  try {
    const response = await getAvailableParentCategories(subjectId, excludeId)
    if (disposed || version !== parentLoadVersion) return
    const parents = response.data || []
    const byId = new Map(parents.map(parent => [parent.id, parent]))
    parentOptions.value = parents.map(parent => {
      const names = []
      const visited = new Set<number>()
      let node: CategoryNode | undefined = parent
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

/**
 * 新增分类
 */
const handleAdd = () => {
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  dialogMode.value = 'add'
  dialogVisible.value = true
  if (form.subjectId) loadParentOptions(form.subjectId)
}

/**
 * 编辑分类
 */
const handleEdit = async (row: CategoryView) => {
  if (typeof row.id !== 'number') return
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  form.id = row.id
  form.subjectId = row.subjectId
  form.parentId = row.parentId || null
  form.code = row.code ?? ''
  form.name = row.name
  form.description = row.description || ''
  form.orderNum = row.orderNum
  form.enabled = row.enabled
  
  dialogMode.value = 'edit'
  dialogVisible.value = true
  await loadParentOptions(row.subjectId, row.id)
}

/**
 * 提交表单
 * 优化：编辑时使用局部更新，新增时保持展开状态
 */
const handleSubmit = async () => {
  if (submitLoading.value || moveSaving.value || parentLoading.value || parentLoadFailed.value) return
  // 手动表单验证
  if (!form.subjectId) {
    showToast('请选择所属科目', 'warning')
    return
  }
  if (!form.name) {
    showToast('请输入分类名称', 'warning')
    return
  }

  submitLoading.value = true
  try {
    let response
    const data = {
      subjectId: form.subjectId,
      parentId: form.parentId || null,
      name: form.name,
      description: form.description || null,
      orderNum: form.orderNum,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      response = await createCategory(data)
    } else {
      if (form.id === null) return
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
        // 编辑后重新读取统计，确保重命名或移动分类时数量保持准确
        const savedTreeExpandedKeys = getTreeExpandedKeys()
        await loadCategories()
        restoreTreeExpandedKeys(savedTreeExpandedKeys)
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
 * 删除分类
 */
const handleDelete = async (row: CategoryView) => {
  if (typeof row.id !== 'number') return
  if (moveSaving.value || deleteLoading.value || submitLoading.value || draggingId.value !== null) return
  deleteLoading.value = true
  try {
    // 先检查引用数量
    const usageRes = await checkCategoryUsage(row.id)
    const usage = usageRes.code === 200 ? usageRes.data : 0
    
    let confirmMsg = `确认删除分类"${row.name}"吗？`
    if (usage > 0) {
      confirmMsg = `该分类被 ${usage} 道题目引用。删除后，这些题目的分类信息将不变，但无法再选择此分类。\n\n确认删除分类"${row.name}"吗？`
    }

    const confirmed = await showConfirm({
      title: '删除确认',
      message: confirmMsg,
      confirmText: '确定',
      cancelText: '取消',
      type: 'danger'
    })

    if (!confirmed) return
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
  } finally {
    deleteLoading.value = false
  }
}

/**
 * 获取分类及其所有子孙分类的去重题目数
 */
const getChildrenQuestionCount = (category: CategoryView) => {
  return category.subtreeQuestionCount ?? category.questionCount ?? 0
}

/**
 * 添加子分类（预填父分类和科目）
 */
const handleAddChild = async (parent: CategoryView) => {
  if (typeof parent.id !== 'number') return
  if (moveSaving.value || draggingId.value !== null) return
  resetForm()
  form.subjectId = parent.subjectId
  form.parentId = parent.id
  dialogMode.value = 'add'
  dialogVisible.value = true
  await loadParentOptions(parent.subjectId)
}

/**
 * 初始化树形视图展开状态
 * 默认收起所有节点（空数组）
 */
const initTreeExpandedKeys = () => {
  treeExpandedKeys.value = []
}

// ============ 大纲视图 ============

// 手柄独占固定左列，树线从展开控件向下连接，不穿过手柄。
const OUTLINER_BASE = 12
const OUTLINER_INDENT = 24
const OUTLINER_TOGGLE_SIZE = 20
const OUTLINER_CONTENT_BASE = computed(() => OUTLINER_BASE + (questionType.value === 'exam' ? 30 : 0))

/**
 * 扁平化大纲行：按展开状态把树铺平成行列表
 */
const outlineRows = computed(() => {
  const rows: OutlineRow[] = []
  const walk = (nodes: CategoryViewTree[], level: number, guideLevels: number[] = []): void => {
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

/** 松手提交一次移动命令；等待期间保持原树，服务端成功后才更新布局。 */
const handleMove = async (id: number, target: CategoryMoveRequest) => {
  // 请求入口再次按最新数据检查；无实际变化时不进入保存态，也不发送或刷新请求。
  if (!canDrag.value || !canMove(id, target)) return
  const subjectId = filterSubjectId.value
  const savedKeys = getTreeExpandedKeys()
  const scrollTop = contentRef.value?.scrollTop ?? 0
  moveSaving.value = true
  moveMessage.value = ''
  ++categoryLoadVersion
  try {
    const response = await moveCategory(id, target)
    if (disposed) return
    const list = (response.data || []).map(normalizeCategory)
    categories.value = list
    replaceSubjectCategories(subjectId, list)
    categoryLoadError.value = ''
    moveMessage.value = '分类层级与顺序已保存'
  } catch (error) {
    if (disposed) return
    // 网络中断不等于未提交；只重新读取，不重放写请求。
    const synced = await loadCategories({ background: true })
    if (disposed) return
    moveMessage.value = synced
      ? '移动请求未确认成功，已重新读取服务端布局，请核对结果。'
      : '无法确认移动结果，请重新读取分类后再操作。'
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
      restoreTreeExpandedKeys([...keys])
      await nextTick()
      if (contentRef.value) contentRef.value.scrollTop = scrollTop
      moveSaving.value = false
    }
  }
}

onMounted(async () => {
  await loadSubjectOptions()
  if (!disposed && viewChangeVersion === 0) await handleQuestionTypeChange()
})

onBeforeUnmount(() => {
  disposed = true
  ++categoryLoadVersion
  ++statsLoadVersion
  ++parentLoadVersion
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
  gap: 0.25rem;
}

/* 毛玻璃档案面板：树容器与骨架屏共用，视觉与原 Tailwind 串完全一致 */
.archive-panel {
  position: relative;
  padding: 1.5rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: linear-gradient(
    to bottom right,
    rgba(255, 255, 255, 0.9),
    rgba(139, 111, 71, 0.006)
  );
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow:
    0 2px 16px rgba(139, 111, 71, 0.06),
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
  border: 1px dashed rgba(139, 111, 71, 0.35);
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
  background: rgba(139, 111, 71, 0.1);
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
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.12), rgba(139, 111, 71, 0.05));
  color: #8b6f47;
  font-size: 11px;
  transition: transform 0.2s ease;
}

.outline-row:hover .outline-icon {
  transform: scale(1.06);
}

/* 名称与徽标 */
.outline-name {
  min-width: 0;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.outline-code {
  flex-shrink: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  color: #a89880;
  border: 1px solid rgba(139, 111, 71, 0.18);
  padding: 1px 6px;
  border-radius: 4px;
}

.outline-count {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: #8b6f47;
  background: rgba(139, 111, 71, 0.12);
  padding: 2px 8px;
  border-radius: 10px;
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
  color: #999;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.outline-action-btn:hover {
  color: #8b6f47;
  background: rgba(139, 111, 71, 0.1);
}

@media (max-width: 768px) {
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
  background-color: rgba(139, 111, 71, 0.15);
  border-radius: 3px;
}

.content-scroll::-webkit-scrollbar-thumb:hover {
  background-color: rgba(139, 111, 71, 0.3);
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
