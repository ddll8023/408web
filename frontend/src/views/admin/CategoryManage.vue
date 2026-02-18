<template>
  <div class="category-manage-container">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">分类标签管理</h1>
        <span class="page-subtitle">管理各科目的题目分类层级结构</span>
      </div>
      <div class="header-right">
        <!-- 视图切换 -->
        <div class="view-switcher">
          <el-tooltip content="卡片视图" placement="top">
            <div 
              class="view-btn" 
              :class="{ active: viewMode === 'card' }"
              @click="viewMode = 'card'"
            >
              <el-icon><Grid /></el-icon>
            </div>
          </el-tooltip>
          <el-tooltip content="树形视图" placement="top">
            <div 
              class="view-btn" 
              :class="{ active: viewMode === 'tree' }"
              @click="viewMode = 'tree'"
            >
              <el-icon><List /></el-icon>
            </div>
          </el-tooltip>
        </div>
        <!-- 题目类型切换 -->
        <el-radio-group v-model="questionType" size="default" @change="handleQuestionTypeChange">
          <el-radio-button value="exam">真题</el-radio-button>
          <el-radio-button value="mock">模拟题</el-radio-button>
        </el-radio-group>
        <CustomButton type="primary" @click="handleAdd">
          <el-icon style="margin-right: 6px"><Plus /></el-icon>
          新增分类
        </CustomButton>
      </div>
    </div>

    <!-- 左右分栏布局 -->
    <div class="main-layout">
      <!-- 左侧筛选栏 -->
      <aside class="sidebar">
        <!-- 科目筛选列表 -->
        <div class="sidebar-section">
          <h3 class="sidebar-title">
            <el-icon><Folder /></el-icon>
            科目筛选
          </h3>
          <div class="subject-list">
            <!-- 各科目选项 -->
            <div 
              v-for="stat in subjectStats" 
              :key="stat.id" 
              class="subject-item"
              :class="{ active: filterSubjectId === stat.id }"
              @click="handleStatClick(stat.id)"
            >
              <div class="subject-info">
                <el-icon class="subject-icon"><Folder /></el-icon>
                <span class="subject-name">{{ stat.name }}</span>
                <el-tooltip 
                  v-if="stat.enabledCount < stat.count" 
                  :content="`${stat.count - stat.enabledCount} 个分类已禁用`" 
                  placement="top"
                >
                  <el-icon class="warning-icon"><Warning /></el-icon>
                </el-tooltip>
              </div>
              <!-- 显示题目引用数量（去重后），预留4位数展示空间 -->
              <span class="question-count-badge" :class="{ active: filterSubjectId === stat.id }">
                {{ stat.questionCount }}
              </span>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="sidebar-section stats-section">
          <h3 class="sidebar-title">
            <el-icon><DataAnalysis /></el-icon>
            统计概览
          </h3>
          <div class="stats-summary">
            <div class="stat-row">
              <span class="stat-label">{{ questionTypeLabel }}引用</span>
              <span class="stat-value">{{ totalQuestionCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">总分类数</span>
              <span class="stat-value">{{ totalCategoryCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">已启用</span>
              <span class="stat-value enabled">{{ enabledCategoryCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">科目数</span>
              <span class="stat-value">{{ subjectOptions.length }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧主内容区 -->
      <main class="main-content">
        <!-- 骨架屏加载状态 -->
        <div v-if="loading" class="skeleton-container">
          <div v-for="i in 3" :key="i" class="skeleton-card">
            <div class="skeleton-header">
              <div class="skeleton-icon"></div>
              <div class="skeleton-title"></div>
              <div class="skeleton-code"></div>
            </div>
            <div class="skeleton-meta">
              <div class="skeleton-tag"></div>
              <div class="skeleton-tag"></div>
            </div>
            <div class="skeleton-children">
              <div v-for="j in 4" :key="j" class="skeleton-child"></div>
            </div>
          </div>
        </div>

        <!-- 卡片视图 -->
        <template v-else-if="viewMode === 'card'">
          <div class="category-cards">
            <TransitionGroup name="card-list">
              <template v-for="parent in treeCategories" :key="parent.id">
                <!-- 父分类卡片 -->
                <div class="parent-card" :class="{ 'is-disabled': !parent.enabled }">
                  <!-- 卡片头部 -->
                  <div class="card-header">
                    <div class="card-title">
                      <el-icon class="folder-icon"><FolderOpened /></el-icon>
                      <span class="name">{{ parent.name }}</span>
                      <span class="code">{{ parent.code }}</span>
                    </div>
                    <div class="card-actions">
                      <!-- 展开/折叠按钮 -->
                      <el-tooltip :content="isExpanded(parent.id) ? '收起' : '展开'" placement="top">
                        <div 
                          class="expand-btn"
                          :class="{ expanded: isExpanded(parent.id) }"
                          @click="toggleExpand(parent.id)"
                        >
                          <el-icon><ArrowDown /></el-icon>
                        </div>
                      </el-tooltip>
                      <CustomButton type="text-primary" size="small" @click="handleEdit(parent)">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </CustomButton>
                      <CustomButton type="danger" size="small" @click="handleDelete(parent)">
                        <el-icon><Delete /></el-icon>
                        删除
                      </CustomButton>
                    </div>
                  </div>
                  
                  <!-- 卡片元信息 -->
                  <div class="card-meta">
                    <el-tag type="info" size="small" effect="plain">
                      {{ parent.subjectName }}
                    </el-tag>
                    <el-tag 
                      :type="getChildrenQuestionCount(parent) > 0 ? 'success' : 'info'" 
                      size="small" 
                      effect="light"
                    >
                      {{ getChildrenQuestionCount(parent) }} 题
                    </el-tag>
                  </div>
                  
                  <!-- 子分类区域（带展开/折叠动画） -->
                  <Transition name="collapse">
                    <div v-show="isExpanded(parent.id)" class="children-wrapper">
                      <div class="children-section" v-if="parent.children && parent.children.length > 0">
                        <div class="children-header">
                          <span class="children-label">子分类</span>
                          <span class="children-count">{{ getTotalChildrenCount(parent) }}</span>
                        </div>
                        <!-- 二级分类列表 -->
                        <div class="children-list">
                          <div 
                            v-for="child in parent.children" 
                            :key="child.id" 
                            class="child-item"
                            :class="{ 'is-disabled': !child.enabled, 'has-children': child.children && child.children.length > 0 }"
                          >
                            <!-- 二级分类标签 -->
                            <div class="child-tag-row">
                              <div 
                                class="child-tag level-2"
                                @click="handleEdit(child)"
                              >
                                <span class="child-name">{{ child.name }}</span>
                                <span class="child-count">{{ getChildrenQuestionCount(child) }}题</span>
                              </div>
                              <!-- 二级分类添加子分类按钮 -->
                              <CustomButton 
                                type="text"
                                size="small" 
                                class="add-grandchild-btn"
                                @click.stop="handleAddChild(child)"
                                title="添加三级分类"
                              >
                                <el-icon><Plus /></el-icon>
                              </CustomButton>
                            </div>
                            <!-- 三级分类标签（如果有） -->
                            <div class="grandchildren-tags" v-if="child.children && child.children.length > 0">
                              <div 
                                v-for="grandchild in child.children" 
                                :key="grandchild.id" 
                                class="child-tag level-3"
                                :class="{ 'is-disabled': !grandchild.enabled }"
                                @click="handleEdit(grandchild)"
                              >
                                <span class="child-name">{{ grandchild.name }}</span>
                                <span class="child-count">{{ grandchild.questionCount || 0 }}题</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <!-- 无子分类提示 -->
                      <div class="children-section empty" v-else>
                        <span class="empty-hint">暂无子分类</span>
                      </div>
                      
                      <!-- 添加子分类按钮 -->
                      <div class="card-footer">
                        <CustomButton 
                          type="text"
                          size="small" 
                          :icon="Plus"
                          @click="handleAddChild(parent)"
                        >
                          添加子分类
                        </CustomButton>
                      </div>
                    </div>
                  </Transition>
                </div>
              </template>
            </TransitionGroup>
          </div>
        </template>

        <!-- 树形视图（延迟渲染优化性能） -->
        <template v-else-if="viewMode === 'tree'">
          <div class="tree-view-container" v-if="treeViewReady">
            <!-- 树形视图工具栏 -->
            <div class="tree-toolbar">
              <CustomButton type="text" size="small" @click="expandAllTree">
                <el-icon><ArrowDown /></el-icon>
                全部展开
              </CustomButton>
              <CustomButton type="text" size="small" @click="collapseAllTree">
                <el-icon><ArrowRight /></el-icon>
                全部收起
              </CustomButton>
            </div>
            <el-tree
              ref="treeRef"
              :data="treeCategories"
              :props="treeProps"
              node-key="id"
              :default-expanded-keys="treeExpandedKeys"
              :expand-on-click-node="false"
              draggable
              :allow-drop="allowDrop"
              :allow-drag="allowDrag"
              @node-expand="handleTreeNodeExpand"
              @node-collapse="handleTreeNodeCollapse"
              @node-drop="handleTreeNodeDrop"
            >
              <template #default="{ node, data }">
                <div class="tree-node" :class="{ 'is-disabled': !data.enabled }">
                  <div class="tree-node-content">
                    <el-icon class="tree-node-icon">
                      <FolderOpened v-if="data.children && data.children.length > 0" />
                      <Document v-else />
                    </el-icon>
                    <span class="tree-node-name">{{ data.name }}</span>
                    <span class="tree-node-code">{{ data.code }}</span>
                    <el-tag 
                      v-if="node.level === 1" 
                      type="info" 
                      size="small" 
                      effect="plain"
                      class="tree-node-subject"
                    >
                      {{ data.subjectName }}
                    </el-tag>
                    <span class="tree-node-count">{{ getChildrenQuestionCount(data) }}题</span>
                  </div>
                  <div class="tree-node-actions">
                    <el-tooltip content="添加子分类" placement="top" v-if="node.level < 3">
                      <el-icon class="action-icon" @click.stop="handleAddChild(data)"><Plus /></el-icon>
                    </el-tooltip>
                    <el-tooltip content="编辑" placement="top">
                      <el-icon class="action-icon" @click.stop="handleEdit(data)"><Edit /></el-icon>
                    </el-tooltip>
                    <el-tooltip content="删除" placement="top">
                      <el-icon class="action-icon danger" @click.stop="handleDelete(data)"><Delete /></el-icon>
                    </el-tooltip>
                  </div>
                </div>
              </template>
            </el-tree>
          </div>
          <!-- 树形视图加载占位 -->
          <div v-else class="tree-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
        </template>
        
        <!-- 空状态 -->
        <el-empty v-if="!loading && treeCategories.length === 0" description="暂无分类数据" />
      </main>
    </div>
    
    <!-- 拖拽保存中提示 -->
    <Transition name="fade">
      <div v-if="dragSaving" class="drag-saving-overlay">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在保存排序...</span>
      </div>
    </Transition>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增分类' : '编辑分类'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="所属科目" prop="subjectId">
          <el-select
            v-model="form.subjectId"
            placeholder="请选择科目"
            style="width: 100%"
            :disabled="dialogMode === 'edit'"
            @change="handleSubjectChange"
          >
            <el-option
              v-for="subject in subjectOptions"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
          <div class="form-tip" v-if="dialogMode === 'edit'">所属科目创建后不可修改</div>
        </el-form-item>

        <el-form-item label="父分类" prop="parentId">
          <el-select
            v-model="form.parentId"
            placeholder="无（顶级分类）"
            style="width: 100%"
            clearable
            :loading="loadingParents"
            :disabled="!form.subjectId || (dialogMode === 'edit' && hasChildren)"
          >
            <!-- 三级分类支持：显示顶级分类和二级分类，带层级缩进 -->
            <el-option
              v-for="parent in parentOptions"
              :key="parent.id"
              :label="parent.parentId ? `└ ${parent.name}` : parent.name"
              :value="parent.id"
            >
              <span :style="{ paddingLeft: parent.parentId ? '20px' : '0' }">
                {{ parent.parentId ? '└ ' : '' }}{{ parent.name }}
                <span v-if="parent.parentName" class="parent-hint">（{{ parent.parentName }}）</span>
              </span>
            </el-option>
          </el-select>
          <div class="form-tip">
            <span v-if="hasChildren">该分类已有子分类，变更层级可能受限</span>
            <span v-else>留空表示顶级分类，支持三级分类结构</span>
          </div>
        </el-form-item>

        <el-form-item label="分类编码" prop="code">
          <el-input
            v-model="form.code"
            placeholder="请输入分类编码（如：stack-queue）"
            maxlength="50"
            clearable
          />
          <div class="form-tip">建议使用英文小写字母和连字符</div>
        </el-form-item>

        <el-form-item label="分类名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入分类名称（如：栈和队列）"
            maxlength="50"
            clearable
          />
        </el-form-item>

        <el-form-item label="分类描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入分类描述（可选）"
            :rows="3"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="排序顺序" prop="orderNum">
          <el-input-number
            v-model="form.orderNum"
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
 * 分类标签管理页面
 * 功能：按科目管理分类标签的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+对话框实现
 */
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Folder, FolderOpened, Warning, Edit, Delete, DataAnalysis, Grid, List, ArrowDown, ArrowRight, Document, Loading } from '@element-plus/icons-vue'
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
import CustomButton from '@/components/basic/CustomButton.vue'

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

// 视图模式（card=卡片视图, tree=树形视图）
// 默认展示树形视图
const viewMode = ref('tree')

// 树形视图引用
const treeRef = ref(null)

// 拖拽排序相关（仅树形视图）
const dragSaving = ref(false)  // 拖拽保存中状态

// 树形视图延迟渲染标志（优化切换性能）
const treeViewReady = ref(false)

// 卡片展开状态（存储已展开的父分类ID）
const expandedCards = ref(new Set())

// 树形视图展开的节点ID列表（响应式，用于保持展开状态）
const treeExpandedKeys = ref([])

// 树形视图配置
const treeProps = {
  children: 'children',
  label: 'name'
}

/**
 * 监听视图模式切换，延迟渲染树形视图优化性能
 */
watch(viewMode, (newMode) => {
  if (newMode === 'tree') {
    // 延迟渲染树形视图，避免切换卡顿
    treeViewReady.value = false
    nextTick(() => {
      setTimeout(() => {
        treeViewReady.value = true
      }, 50)
    })
  }
})

/**
 * 树形视图：全部展开
 * 通过 treeRef 实例方法实现
 */
const expandAllTree = () => {
  if (treeRef.value) {
    const allNodes = getAllTreeNodes(treeCategories.value)
    allNodes.forEach(id => {
      const node = treeRef.value.getNode(id)
      if (node) node.expand()
    })
    // 同步更新 treeExpandedKeys
    treeExpandedKeys.value = allNodes
  }
}

/**
 * 树形视图：全部收起
 * 通过 treeRef 实例方法实现
 */
const collapseAllTree = () => {
  if (treeRef.value) {
    const allNodes = getAllTreeNodes(treeCategories.value)
    allNodes.forEach(id => {
      const node = treeRef.value.getNode(id)
      if (node) node.collapse()
    })
    // 同步更新 treeExpandedKeys
    treeExpandedKeys.value = []
  }
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
 * 使用 treeRef 实例方法展开节点
 * @param {Array} keys 需要展开的节点ID列表
 */
const restoreTreeExpandedKeys = (keys) => {
  if (!keys) return
  treeExpandedKeys.value = [...keys]
  // 使用 nextTick 确保 DOM 更新后再操作
  nextTick(() => {
    if (treeRef.value && keys.length > 0) {
      keys.forEach(id => {
        const node = treeRef.value.getNode(id)
        if (node) node.expand()
      })
    }
  })
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

// 去重后的统计数据（解决多标签重复计数问题）
const categoryStats = ref({
  subjectStats: [],  // 各科目去重题目数
  totalQuestionCount: 0  // 全局去重题目总数
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

// 加载父分类状态
const loadingParents = ref(false)

// 编辑时检查是否有子分类
const hasChildren = ref(false)

/**
 * 将扁平分类数据转换为树形结构
 */
const treeCategories = computed(() => {
  const list = categories.value
  if (!list || list.length === 0) return []
  
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
 * 计算各科目分类统计（基于全部数据）
 * 使用去重后的统计数据，解决多标签重复计数问题
 */
const subjectStats = computed(() => {
  return subjectOptions.value.map(subject => {
    const subjectCategories = allCategories.value.filter(c => c.subjectId === subject.id)
    // 从去重统计数据中获取该科目的题目数
    const statItem = categoryStats.value.subjectStats.find(s => s.subjectId === subject.id)
    const questionCount = statItem ? statItem.questionCount : 0
    return {
      id: subject.id,
      name: subject.name,
      count: subjectCategories.length,  // 分类数量
      enabledCount: subjectCategories.filter(c => c.enabled).length,
      questionCount: questionCount  // 去重后的题目数
    }
  })
})

/**
 * 总分类数（基于全部数据）
 */
const totalCategoryCount = computed(() => allCategories.value.length)

/**
 * 已启用分类数
 */
const enabledCategoryCount = computed(() => allCategories.value.filter(c => c.enabled).length)

/**
 * 题目引用总数（使用去重后的统计数据）
 */
const totalQuestionCount = computed(() => {
  return categoryStats.value.totalQuestionCount || 0
})

/**
 * 题目类型标签
 */
const questionTypeLabel = computed(() => {
  const labels = {
    exam: '真题',
    mock: '模拟题'
  }
  return labels[questionType.value] || '题目'
})

// 表单引用
const formRef = ref(null)

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

// 表单验证规则
const formRules = {
  subjectId: [
    { required: true, message: '请选择所属科目', trigger: 'change' }
  ],
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { max: 50, message: '编码长度不能超过50字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '编码只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 50, message: '名称长度不能超过50字符', trigger: 'blur' }
  ],
  orderNum: [
    { required: true, message: '请输入排序顺序', trigger: 'blur' }
  ]
}

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
 * 加载所有分类（用于统计）
 */
const loadAllCategories = async () => {
  try {
    const response = await getAllCategories(questionType.value)
    if (response.code === 200) {
      allCategories.value = response.data || []
    }
  } catch (error) {
    console.error('加载全部分类失败:', error)
  }
}

/**
 * 加载去重后的统计数据
 * 解决一道题目有多个标签时的重复计数问题
 */
const loadCategoryStats = async () => {
  try {
    const response = await getCategoryStats(questionType.value)
    if (response.code === 200) {
      categoryStats.value = response.data || { subjectStats: [], totalQuestionCount: 0 }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

/**
 * 加载分类列表（筛选后显示）
 */
const loadCategories = async () => {
  loading.value = true
  try {
    let response
    if (filterSubjectId.value) {
      response = await getCategoriesBySubject(filterSubjectId.value, questionType.value)
    } else {
      response = await getAllCategories(questionType.value)
    }
    
    if (response.code === 200) {
      categories.value = response.data || []
      // 同步更新全部分类数据（保证统计数据实时）
      if (!filterSubjectId.value) {
        allCategories.value = response.data || []
      }
    } else {
      ElMessage.error(response.message || '加载分类列表失败')
    }
  } catch (error) {
    console.error('加载分类列表失败:', error)
    ElMessage.error('加载分类列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 题目类型切换处理
 * 切换时需要同时更新当前显示的分类和全部分类统计
 * 修复：切换题目类型后需要重新初始化展开状态
 */
const handleQuestionTypeChange = async () => {
  // 并行加载：全部分类数据 + 去重统计数据
  await Promise.all([
    loadAllCategories(),
    loadCategoryStats()
  ])
  // 再加载当前筛选的分类数据
  await loadCategories()
  // 重新初始化展开状态，确保新数据的分类正确展开
  initExpandedCards()
  initTreeExpandedKeys()
}

/**
 * 点击统计卡片筛选
 * 修复：切换科目后需要重新初始化展开状态
 */
const handleStatClick = async (subjectId) => {
  filterSubjectId.value = subjectId
  await loadCategories()
  // 重新初始化展开状态，确保新科目的分类正确展开
  initExpandedCards()
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
  formRef.value?.clearValidate()
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
  loadingParents.value = true
  try {
    const response = await getAvailableParentCategories(subjectId, excludeId)
    if (response.code === 200) {
      parentOptions.value = response.data || []
    }
  } catch (error) {
    console.error('加载父分类失败:', error)
  } finally {
    loadingParents.value = false
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
      parentId: form.parentId || null,
      code: form.code,
      name: form.name,
      description: form.description || null,
      orderNum: form.orderNum,
      enabled: form.enabled
    }

    if (dialogMode.value === 'add') {
      response = await createCategory(data)
    } else {
      response = await updateCategory(form.id, data)
    }

    if (response.code === 200) {
      ElMessage.success(dialogMode.value === 'add' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      
      if (dialogMode.value === 'add') {
        // 新增：保存当前展开状态，重新加载后恢复
        const savedExpandedCards = new Set(expandedCards.value)
        const savedTreeExpandedKeys = getTreeExpandedKeys()
        
        await loadCategories()
        
        // 恢复卡片展开状态
        expandedCards.value = savedExpandedCards
        // 如果新增的是顶级分类，自动展开它
        const newCategory = response.data
        if (!newCategory.parentId) {
          expandedCards.value.add(newCategory.id)
        } else {
          // 如果新增的是子分类，确保其父分类展开
          expandedCards.value.add(newCategory.parentId)
        }
        
        // 恢复树形视图展开状态
        restoreTreeExpandedKeys(savedTreeExpandedKeys)
      } else {
        // 编辑：局部更新本地数据，避免页面刷新
        const updatedData = response.data
        updateLocalCategory(form.id, updatedData)
      }
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
 * 局部更新本地分类数据
 * 用后端返回的数据更新 categories 和 allCategories 中对应的项
 * @param {Number} id 分类ID
 * @param {Object} newData 后端返回的更新后数据
 */
const updateLocalCategory = (id, newData) => {
  // 更新 categories 数组
  const index = categories.value.findIndex(c => c.id === id)
  if (index !== -1) {
    // 保留原有的 children 引用（如果有），因为后端返回的数据可能不包含 children
    const oldChildren = categories.value[index].children
    categories.value[index] = { ...newData, children: oldChildren }
  }
  
  // 同步更新 allCategories 数组
  const allIndex = allCategories.value.findIndex(c => c.id === id)
  if (allIndex !== -1) {
    const oldChildren = allCategories.value[allIndex].children
    allCategories.value[allIndex] = { ...newData, children: oldChildren }
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

    await ElMessageBox.confirm(
      confirmMsg,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    const response = await deleteCategory(row.id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      // 保存当前展开状态
      const savedExpandedCards = new Set(expandedCards.value)
      const savedTreeExpandedKeys = getTreeExpandedKeys()
      // 从展开状态中移除被删除的分类ID
      savedExpandedCards.delete(row.id)
      
      await loadCategories()
      
      // 恢复展开状态
      expandedCards.value = savedExpandedCards
      restoreTreeExpandedKeys(savedTreeExpandedKeys.filter(id => id !== row.id))
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
 * 判断卡片是否展开
 */
const isExpanded = (id) => {
  return expandedCards.value.has(id)
}

/**
 * 切换卡片展开/折叠状态
 */
const toggleExpand = (id) => {
  if (expandedCards.value.has(id)) {
    expandedCards.value.delete(id)
  } else {
    expandedCards.value.add(id)
  }
}

/**
 * 初始化卡片展开状态
 * 默认收起所有卡片
 */
const initExpandedCards = () => {
  // 清空旧状态，默认收起
  expandedCards.value.clear()
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
 * 仅支持同级排序，不支持跨层级拖拽
 * 优化：使用局部更新而非重新加载整个列表
 * @param {Object} draggingNode 被拖拽的节点
 * @param {Object} dropNode 目标节点
 * @param {String} dropType 放置类型：before/after/inner
 * @param {Event} ev 事件对象
 */
const handleTreeNodeDrop = async (draggingNode, dropNode, dropType, ev) => {
  // 只处理同级排序（before/after），不处理 inner（跨层级）
  if (dropType === 'inner') {
    ElMessage.warning('暂不支持跨层级拖拽')
    // 局部恢复：el-tree 已经移动了节点，需要恢复原位置
    restoreTreeOrder()
    return
  }
  
  // 获取被拖拽节点的数据
  const dragData = draggingNode.data
  const dropData = dropNode.data
  
  // 确保是同一父级下的排序
  if (dragData.parentId !== dropData.parentId) {
    ElMessage.warning('只能在同一层级内排序')
    restoreTreeOrder()
    return
  }
  
  // 获取同级节点列表（从 categories 中获取，保证数据一致性）
  const parentId = dragData.parentId
  let siblings = categories.value.filter(c => c.parentId === parentId)
  siblings.sort((a, b) => (a.orderNum || 0) - (b.orderNum || 0))
  
  // 计算新的排序
  const oldIndex = siblings.findIndex(s => s.id === dragData.id)
  let newIndex = siblings.findIndex(s => s.id === dropData.id)
  
  if (dropType === 'after') {
    newIndex = newIndex + 1
  }
  
  // 如果位置没变，不处理
  if (oldIndex === newIndex || (dropType === 'after' && oldIndex === newIndex - 1)) {
    return
  }
  
  // 移动元素计算新顺序
  const reorderedSiblings = [...siblings]
  const [movedItem] = reorderedSiblings.splice(oldIndex, 1)
  if (oldIndex < newIndex) newIndex--
  reorderedSiblings.splice(newIndex, 0, movedItem)
  
  // 更新排序
  dragSaving.value = true
  try {
    // 收集需要更新的项
    const updateItems = []
    reorderedSiblings.forEach((item, index) => {
      if (item.orderNum !== index) {
        updateItems.push({ id: item.id, newOrderNum: index })
      }
    })
    
    // 批量更新后端
    const updatePromises = updateItems.map(({ id, newOrderNum }) => {
      const item = categories.value.find(c => c.id === id)
      return updateCategory(id, { ...item, orderNum: newOrderNum })
    })
    
    await Promise.all(updatePromises)
    
    // 局部更新本地数据：直接修改 categories 中对应项的 orderNum
    updateItems.forEach(({ id, newOrderNum }) => {
      const item = categories.value.find(c => c.id === id)
      if (item) {
        item.orderNum = newOrderNum
      }
      // 同步更新 allCategories
      const allItem = allCategories.value.find(c => c.id === id)
      if (allItem) {
        allItem.orderNum = newOrderNum
      }
    })
    
    ElMessage.success('排序已更新')
  } catch (error) {
    console.error('更新排序失败:', error)
    ElMessage.error('排序更新失败')
    // 失败时恢复原顺序
    restoreTreeOrder()
  } finally {
    dragSaving.value = false
  }
}

/**
 * 恢复树形视图的原始排序
 * 通过重新触发 categories 的响应式更新来恢复
 */
const restoreTreeOrder = () => {
  // 触发响应式更新，让 treeCategories 重新计算
  categories.value = [...categories.value]
}

/**
 * 判断节点是否允许放置
 * 只允许同级排序，不允许跨层级
 */
const allowDrop = (draggingNode, dropNode, type) => {
  // 只允许 before 和 after，不允许 inner（跨层级）
  if (type === 'inner') return false
  // 只允许同一父级下排序
  return draggingNode.data.parentId === dropNode.data.parentId
}

/**
 * 判断节点是否可拖拽
 * 所有节点都可拖拽
 */
const allowDrag = (node) => {
  return true
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadSubjectOptions()
  // 默认选中第一个科目
  if (subjectOptions.value.length > 0) {
    filterSubjectId.value = subjectOptions.value[0].id
  }
  // 并行加载：分类数据 + 去重统计数据
  await Promise.all([loadCategories(), loadCategoryStats()])
  // 初始化展开所有卡片和树节点
  initExpandedCards()
  initTreeExpandedKeys()
  // 如果默认是树形视图，需要初始化treeViewReady
  if (viewMode.value === 'tree') {
    nextTick(() => {
      setTimeout(() => {
        treeViewReady.value = true
      }, 50)
    })
  }
})
</script>

<style scoped>
/**
 * 分类管理页面样式 - 现代化设计
 * 移除 SCSS，使用普通 CSS
 */

.category-manage-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
  min-height: calc(100vh - 60px);
}

/* 页面标题栏 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid rgba(139, 111, 71, 0.1);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.page-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: #8B6F47;
  display: flex;
  align-items: center;
}

.page-title::before {
  content: '';
  display: inline-block;
  width: 5px;
  height: 28px;
  background: linear-gradient(180deg, #8B6F47, #a88a5f);
  margin-right: 16px;
  border-radius: 3px;
}

.page-subtitle {
  font-size: 12px;
  color: #999;
  margin-left: calc(5px + 16px);
}

/* 左右分栏布局 */
.main-layout {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}

/* 左侧侧边栏 */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: calc(60px + 24px);
}

.sidebar-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(139, 111, 71, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(139, 111, 71, 0.08);
}

.sidebar-section + .sidebar-section {
  margin-top: 24px;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #8B6F47;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(139, 111, 71, 0.1);
}

.sidebar-title .el-icon {
  font-size: 16px;
}

/* 科目列表 */
.subject-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subject-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
}

.subject-item:hover {
  background: rgba(139, 111, 71, 0.06);
}

.subject-item.active {
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.12), rgba(139, 111, 71, 0.06));
}

.subject-item.active .subject-icon {
  color: #8B6F47;
  background: rgba(139, 111, 71, 0.15);
}

.subject-item.active .subject-name {
  color: #8B6F47;
  font-weight: 600;
}

.subject-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.subject-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(139, 111, 71, 0.08);
  color: #999;
  font-size: 14px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.subject-name {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s ease;
}

/* 题目数量徽章 */
.question-count-badge {
  min-width: 36px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  border-radius: 10px;
  background: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
}

.question-count-badge.active {
  background: #8B6F47;
  color: white;
}

.warning-icon {
  color: #e6a23c;
  font-size: 14px;
  margin-left: 4px;
}

/* 统计概览区 */
.stats-section {
  background: linear-gradient(180deg, white, rgba(64, 158, 255, 0.5));
}

.stats-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.6);
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: #8B6F47;
}

.stat-value.enabled {
  color: #67c23a;
}

.stat-value.disabled {
  color: #999;
}

/* 右侧主内容区 */
.main-content {
  flex: 1;
  min-width: 0;
}

/* 分类卡片列表容器 */
.category-cards {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 父分类卡片 */
.parent-card {
  background: white;
  border-radius: 16px;
  padding: 24px 32px;
  box-shadow: 0 2px 12px rgba(139, 111, 71, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(139, 111, 71, 0.08);
  transition: all 0.3s ease;
}

.parent-card:hover {
  box-shadow: 0 8px 24px rgba(139, 111, 71, 0.1), 0 2px 6px rgba(0, 0, 0, 0.04);
  transform: translateY(-2px);
}

.parent-card.is-disabled {
  opacity: 0.6;
  background: linear-gradient(180deg, white, rgba(153, 153, 153, 0.05));
}

.parent-card.is-disabled .card-title .name {
  color: #999;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-title .folder-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #8B6F47, #968657);
  color: white;
  border-radius: 10px;
  font-size: 18px;
  box-shadow: 0 3px 10px rgba(139, 111, 71, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.card-title .name {
  font-size: 16px;
  font-weight: 600;
  color: #8B6F47;
}

.card-title .code {
  font-size: 12px;
  color: #999;
  font-family: monospace;
  background: rgba(139, 111, 71, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 卡片元信息 */
.card-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px dashed rgba(139, 111, 71, 0.1);
}

/* 子分类区域 */
.children-section {
  margin-bottom: 16px;
}

.children-section.empty {
  padding: 16px 0;
}

.children-section.empty .empty-hint {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.children-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.children-label {
  font-size: 13px;
  color: #999;
  font-weight: 500;
}

.children-count {
  font-size: 12px;
  background: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

/* 视图切换器 */
.view-switcher {
  display: flex;
  background: rgba(139, 111, 71, 0.08);
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.view-btn {
  width: 36px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.2s ease;
}

.view-btn:hover {
  color: #8B6F47;
  background: rgba(139, 111, 71, 0.1);
}

.view-btn.active {
  background: white;
  color: #8B6F47;
  box-shadow: 0 2px 6px rgba(139, 111, 71, 0.15);
}

.view-btn .el-icon {
  font-size: 18px;
}

/* 骨架屏样式 */
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.skeleton-card {
  background: white;
  border-radius: 16px;
  padding: 24px 32px;
  box-shadow: 0 2px 12px rgba(139, 111, 71, 0.06);
  border: 1px solid rgba(139, 111, 71, 0.08);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.skeleton-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-title {
  width: 120px;
  height: 20px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-code {
  width: 80px;
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px dashed rgba(139, 111, 71, 0.1);
}

.skeleton-tag {
  width: 60px;
  height: 22px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skeleton-child {
  width: 100px;
  height: 36px;
  border-radius: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 展开/折叠按钮 */
.expand-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.3s ease;
}

.expand-btn:hover {
  background: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
}

.expand-btn .el-icon {
  transition: transform 0.3s ease;
}

.expand-btn.expanded .el-icon {
  transform: rotate(180deg);
}

/* 子分类区域包装器（用于动画） */
.children-wrapper {
  overflow: hidden;
}

/* 展开/折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  opacity: 1;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

/* 卡片列表动画 */
.card-list-enter-active,
.card-list-leave-active {
  transition: all 0.3s ease;
}

.card-list-enter-from,
.card-list-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.card-list-move {
  transition: transform 0.3s ease;
}

/* 树形视图拖拽节点样式 */
:deep(.el-tree) .el-tree-node.is-drop-inner > .el-tree-node__content {
  background: rgba(139, 111, 71, 0.15);
  border-radius: 8px;
}

:deep(.el-tree) .el-tree__drop-indicator {
  height: 3px;
  background: linear-gradient(90deg, #8B6F47, #a88a5f);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(139, 111, 71, 0.5);
}

:deep(.el-tree) .is-dragging .tree-node {
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.15), rgba(139, 111, 71, 0.08));
  border: 2px solid #8B6F47;
  box-shadow: 0 8px 24px rgba(139, 111, 71, 0.3);
  transform: scale(1.02);
}

/* 拖拽保存中的加载提示 */
.drag-saving-overlay {
  position: fixed;
  top: 20px;
  right: 20px;
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 2000;
  animation: slide-in 0.3s ease;
}

.drag-saving-overlay .el-icon {
  color: #8B6F47;
  animation: spin 1s linear infinite;
}

@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* fade 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 树形视图容器 */
.tree-view-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(139, 111, 71, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(139, 111, 71, 0.08);
}

.tree-view-container :deep(.el-tree) {
  background: transparent;
}

.tree-view-container :deep(.el-tree) .el-tree-node__content {
  height: auto;
  padding: 8px 0;
}

.tree-view-container :deep(.el-tree) .el-tree-node__content:hover {
  background: rgba(139, 111, 71, 0.04);
}

.tree-view-container :deep(.el-tree) .el-tree-node__expand-icon {
  color: #8B6F47;
  font-size: 16px;
}

.tree-view-container :deep(.el-tree) .el-tree-node__expand-icon.is-leaf {
  color: transparent;
}

/* 树形视图工具栏 */
.tree-toolbar {
  display: flex;
  gap: 8px;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(139, 111, 71, 0.1);
}

/* 树形视图加载状态 */
.tree-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #999;
}

.tree-loading .el-icon {
  font-size: 20px;
  color: #8B6F47;
}

/* 树形节点样式 */
.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.tree-node:hover {
  background: rgba(139, 111, 71, 0.06);
}

.tree-node:hover .tree-node-actions {
  opacity: 1;
}

.tree-node.is-disabled {
  opacity: 0.6;
}

.tree-node.is-disabled .tree-node-name {
  color: #999;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tree-node-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(139, 111, 71, 0.15), rgba(139, 111, 71, 0.08));
  color: #8B6F47;
  border-radius: 6px;
  font-size: 14px;
}

.tree-node-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.tree-node-code {
  font-size: 12px;
  color: #999;
  font-family: monospace;
  background: rgba(139, 111, 71, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

.tree-node-subject {
  margin-left: 4px;
}

.tree-node-count {
  font-size: 12px;
  color: #999;
  background: rgba(139, 111, 71, 0.08);
  padding: 2px 8px;
  border-radius: 10px;
}

.tree-node-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.action-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.2s ease;
}

.action-icon:hover {
  background: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
}

.action-icon.danger:hover {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

/* 子分类列表容器（横向排列） */
.children-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

/* 子分类项（二级分类及其三级子分类） */
.child-item {
  display: inline-flex;
  flex-direction: column;
  gap: 6px;
}

.child-item.is-disabled {
  opacity: 0.6;
}

/* 子分类标签行（包含标签和添加按钮） */
.child-tag-row {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 添加三级分类按钮 */
.add-grandchild-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
  padding: 2px !important;
  min-width: auto !important;
}

.child-tag-row:hover .add-grandchild-btn {
  opacity: 1;
}

/* 三级分类标签容器 */
.grandchildren-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  padding-left: 8px;
  border-left: 2px solid rgba(139, 111, 71, 0.2);
}

/* 子分类标签（通用样式） */
.child-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.08), rgba(139, 111, 71, 0.04));
  border: 1px solid rgba(139, 111, 71, 0.12);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.child-tag:hover {
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.15), rgba(139, 111, 71, 0.08));
  border-color: rgba(139, 111, 71, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 111, 71, 0.15);
}

.child-tag.is-disabled {
  opacity: 0.5;
  background: rgba(153, 153, 153, 0.08);
  border-color: rgba(153, 153, 153, 0.15);
}

.child-tag.is-disabled .child-name {
  color: #999;
}

/* 二级分类样式 */
.child-tag.level-2 {
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.1), rgba(139, 111, 71, 0.05));
  border-color: rgba(139, 111, 71, 0.15);
}

/* 三级分类样式（更小更淡） */
.child-tag.level-3 {
  padding: 5px 10px;
  font-size: 12px;
  background: linear-gradient(135deg, rgba(139, 111, 71, 0.06), rgba(139, 111, 71, 0.02));
  border-color: rgba(139, 111, 71, 0.1);
}

.child-tag.level-3 .child-name {
  font-size: 12px;
}

.child-tag.level-3 .child-count {
  font-size: 10px;
}

.child-tag .child-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.child-tag .child-count {
  font-size: 12px;
  color: #999;
  background: rgba(255, 255, 255, 0.8);
  padding: 2px 6px;
  border-radius: 8px;
}

/* 卡片底部 */
.card-footer {
  padding-top: 16px;
  border-top: 1px solid rgba(139, 111, 71, 0.06);
}

/* 标签样式优化 */
:deep(.el-tag).el-tag--success {
  background-color: rgba(103, 194, 58, 0.1);
  border-color: rgba(103, 194, 58, 0.2);
  color: #5daf34;
}

:deep(.el-tag).el-tag--info {
  background-color: rgba(139, 111, 71, 0.08);
  border-color: rgba(139, 111, 71, 0.15);
  color: #8B6F47;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 父分类选择器中的层级提示 */
.parent-hint {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .category-manage-container {
    padding: 16px 8px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-right {
    flex-direction: column;
    width: 100%;
    gap: 16px;
  }

  .header-right .el-radio-group {
    width: 100%;
    display: flex;
  }

  .header-right .el-radio-group .el-radio-button {
    flex: 1;
  }

  .main-layout {
    flex-direction: column;
    gap: 24px;
  }

  .sidebar {
    width: 100%;
    position: static;
  }

  .sidebar .subject-list {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
    gap: 8px;
  }

  .sidebar .subject-list::-webkit-scrollbar {
    height: 4px;
  }

  .sidebar .subject-list::-webkit-scrollbar-thumb {
    background: rgba(139, 111, 71, 0.2);
    border-radius: 2px;
  }

  .sidebar .subject-item {
    flex-shrink: 0;
    min-width: 120px;
    padding: 8px 12px;
  }

  .sidebar-section + .sidebar-section {
    margin-top: 12px;
  }

  .stats-summary {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }

  .stats-summary .stat-row {
    flex: 1;
    min-width: calc(50% - 3px);
    padding: 6px 10px;
  }

  /* 移动端卡片优化 */
  .parent-card {
    padding: 16px 24px;
  }

  .card-header {
    flex-wrap: wrap;
    gap: 16px;
  }

  .card-title .folder-icon {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }

  .card-title .name {
    font-size: 15px;
  }

  .children-tags {
    gap: 6px;
  }

  .child-tag {
    padding: 6px 10px;
  }

  .child-tag .child-name {
    font-size: 13px;
  }
}
</style>
