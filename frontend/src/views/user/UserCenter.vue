<template>
  <div class="min-h-[calc(100vh-60px)] pt-[60px] bg-[#FBF7F2] flex gap-4 px-4 pb-4">
    <!-- 左侧边栏 -->
    <aside class="w-[280px] flex-shrink-0">
      <!-- 个人信息卡片 -->
      <div class="mb-4 text-center bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex justify-center items-center w-20 h-20 mx-auto mb-4 rounded-full bg-[rgba(139,111,71,0.1)]">
          <font-awesome-icon :icon="['fas', 'user']" class="text-5xl text-[#8B7355]" />
        </div>
        <div>
          <h3 class="text-[#333] text-lg mb-2">{{ authStore.userInfo?.username }}</h3>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium"
            :class="roleTagType === 'danger' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'">
            {{ roleText }}
          </span>
        </div>
      </div>

      <!-- 菜单导航 -->
      <nav class="space-y-2">
        <button
          class="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200"
          :class="activeMenu === 'favorites'
            ? 'bg-[rgba(139,111,71,0.1)] text-[#8B6F47]'
            : 'bg-white text-gray-700 hover:bg-[rgba(139,111,71,0.05)]'"
          @click="handleMenuSelect('favorites')"
        >
          <font-awesome-icon :icon="['fas', 'star']" />
          <span>我的收藏</span>
          <span v-if="totalCount > 0" class="ml-auto inline-flex items-center justify-center bg-[#f56c6c] text-white text-[11px] font-medium w-[18px] h-[18px] rounded-full leading-1">
            {{ totalCount }}
          </span>
        </button>
      </nav>
    </aside>

    <!-- 右侧内容区域 -->
    <main class="flex-1">
      <div v-if="activeMenu === 'favorites'" class="min-h-[600px] bg-white rounded-lg border border-gray-200">
        <!-- 收藏夹标题 -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 class="flex items-center gap-2 text-[#333] text-xl m-0">
            <font-awesome-icon :icon="['fas', 'star']" class="text-[#8B6F47]" />
            我的收藏
          </h2>
          <div class="flex gap-4">
            <CustomButton
              size="sm"
              type="primary"
              @click="openAddDialogForSubject()"
            >
              添加收藏
            </CustomButton>
            <CustomButton
              v-if="totalCount > 0"
              size="sm"
              type="danger"
              @click="handleClearAll"
            >
              清空收藏
            </CustomButton>
          </div>
        </div>

        <!-- 按科目分类展示 -->
        <div class="pt-4">
          <!-- 加载状态 -->
          <div v-if="loadingSubjects" class="flex items-center justify-center py-12">
            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-primary-600" />
            <span class="ml-3 text-gray-500">加载中...</span>
          </div>

          <!-- Tabs 标题栏 -->
          <div v-else class="flex border-b border-gray-200 px-4">
            <button
              v-for="subject in subjects"
              :key="subject.id"
              class="px-6 py-3 text-base font-medium transition-colors relative"
              :class="activeSubjectTab === subject.id
                ? 'text-[#8B6F47] font-semibold'
                : 'text-gray-500 hover:text-[#9d825a]'"
              @click="activeSubjectTab = subject.id"
            >
              {{ subject.name }}
              <div
                v-if="activeSubjectTab === subject.id"
                class="absolute bottom-0 left-0 w-full h-0.5 bg-[#8B6F47]"
              />
            </button>
          </div>

          <!-- Tab 内容区 -->
          <div class="p-4">
            <div v-show="activeSubjectTab === subject.id" v-for="subject in subjects" :key="subject.id">
              <template v-if="getFavoritesForSubject(subject.id).length > 0">
                <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4">
                  <div
                    v-for="item in getFavoritesForSubject(subject.id)"
                    :key="item.id"
                    class="flex items-center justify-between p-4 bg-white border border-[rgba(139,111,71,0.2)] rounded transition-all duration-300 hover:border-[#8B6F47] hover:shadow-[0_2px_4px_rgba(0,0,0,0.08)] group"
                  >
                    <div class="flex items-center gap-2 flex-1 cursor-pointer" @click="handleCategoryClick(item)">
                      <font-awesome-icon :icon="['fas', 'folder']" class="text-[#8B6F47] flex-shrink-0" />
                      <span class="text-[#333] text-sm truncate">{{ item.category }}</span>
                    </div>
                    <button
                      class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 text-gray-400 hover:text-red-500 p-1"
                      @click="handleRemoveFavorite(item)"
                    >
                      <font-awesome-icon :icon="['fas', 'trash']" />
                    </button>
                  </div>
                </div>
              </template>
              <div v-else class="py-12">
                <Empty description="该科目下暂无收藏" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 添加收藏弹窗 -->
    <Dialog
      v-model:visible="addDialogVisible"
      title="添加收藏"
      width="600px"
      top="15vh"
    >
      <!-- 弹窗内 Tabs -->
      <!-- Tabs 标题栏 -->
      <div class="flex border-b border-gray-200">
        <button
          v-for="subject in subjects"
          :key="subject.id"
          class="px-6 py-3 text-base font-medium transition-colors relative"
          :class="activeAddSubject === subject.id
            ? 'text-[#8B6F47] font-semibold'
            : 'text-gray-500 hover:text-[#9d825a]'"
          @click="handleAddSubjectChange(subject.id)"
        >
          {{ subject.name }}
          <div
            v-if="activeAddSubject === subject.id"
            class="absolute bottom-0 left-0 w-full h-0.5 bg-[#8B6F47]"
          />
        </button>
      </div>

      <!-- Tab 内容区 -->
      <div class="h-[400px] overflow-y-auto p-4">
        <!-- 加载状态 -->
        <div v-if="loadingCategories" class="flex items-center justify-center py-12">
          <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-primary-600" />
          <span class="ml-3 text-gray-500">加载中...</span>
        </div>

        <template v-else-if="categoryList && categoryList.length > 0">
          <div class="grid grid-cols-2 gap-3">
            <div
              v-for="category in categoryList"
              :key="category"
              class="flex items-center justify-between p-3 bg-white border border-[#dfe2e5] rounded cursor-pointer transition-all duration-200 hover:border-[#8B6F47] hover:bg-[rgba(139,111,71,0.05)]"
              :class="{ 'bg-[rgba(103,194,58,0.1)] border-[#67c23a]': isFavorite(activeAddSubject, category) }"
              @click="toggleCategoryFavorite(category, activeAddSubject)"
            >
              <span class="text-sm truncate flex-1 mr-2 text-left overflow-hidden text-ellipsis whitespace-nowrap"
                :class="isFavorite(activeAddSubject, category) ? 'text-[#67c23a]' : 'text-[#666]'">
                {{ category }}
              </span>
              <font-awesome-icon
                class="text-base transition-all duration-200"
                :class="isFavorite(activeAddSubject, category) ? 'text-[#67c23a]' : 'text-[#666]'"
                :icon="isFavorite(activeAddSubject, category) ? ['fas', 'check'] : ['fas', 'plus']"
              />
            </div>
          </div>
        </template>
        <div v-else class="py-12">
          <Empty description="该科目暂无题目分类" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
/**
 * 个人中心页面
 * 功能：展示个人信息和收藏夹（收藏题目分类）
 * 遵循KISS原则：简洁的左右布局
 * 遵循YAGNI原则：只实现当前需要的功能
 * 遵循SOLID原则：单一职责，左侧导航，右侧内容
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavorites } from '@/composables/useFavorites'
import { getEnabledSubjects } from '@/api/subject'
import { getExamCategoriesBySubject } from '@/api/exam'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dialog from '@/components/basic/Dialog.vue'
import Empty from '@/components/basic/Empty.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

const router = useRouter()
const authStore = useAuthStore()
const { favorites, totalCount, removeFavorite, clearAllFavorites, isFavorite, addFavorite } = useFavorites()
const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 当前激活的菜单项
const activeMenu = ref('favorites')

// 科目数据
const subjects = ref([])
const loadingSubjects = ref(false)
const activeSubjectTab = ref(null)

// 添加弹窗状态
const addDialogVisible = ref(false)
const activeAddSubject = ref(null)
const categoryList = ref([])
const loadingCategories = ref(false)

// 角色标签类型
const roleTagType = computed(() => {
  return authStore.isAdmin() ? 'danger' : 'primary'
})

// 角色文本
const roleText = computed(() => {
  return authStore.isAdmin() ? '管理员' : '普通用户'
})

// 初始化
onMounted(async () => {
  await loadSubjects()
})

/**
 * 加载科目数据
 */
const loadSubjects = async () => {
  loadingSubjects.value = true
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjects.value = res.data || []
      // 默认选中第一个科目
      if (subjects.value.length > 0) {
        activeSubjectTab.value = subjects.value[0].id
      }
    }
  } catch (error) {
    console.error('加载科目失败:', error)
  } finally {
    loadingSubjects.value = false
  }
}

/**
 * 获取指定科目的收藏列表
 */
const getFavoritesForSubject = (subjectId) => {
  return favorites.value
    .filter(item => item.subjectId === subjectId)
    .sort((a, b) => b.timestamp - a.timestamp)
}

/**
 * 处理菜单选择
 */
const handleMenuSelect = (index) => {
  activeMenu.value = index
}

/**
 * 为指定科目打开添加收藏弹窗
 * @param {Number} subjectId - 科目ID
 */
const openAddDialogForSubject = (subjectId) => {
  addDialogVisible.value = true
  const targetSubjectId = subjectId || activeSubjectTab.value || (subjects.value.length > 0 ? subjects.value[0].id : null)
  if (targetSubjectId) {
    activeAddSubject.value = targetSubjectId
    loadCategoriesForSubject(targetSubjectId)
  }
}

/**
 * 加载指定科目的题目分类列表
 */
const loadCategoriesForSubject = async (subjectId) => {
  if (!subjectId) return
  
  loadingCategories.value = true
  categoryList.value = []
  
  try {
    const res = await getExamCategoriesBySubject(subjectId)
    if (res.code === 200) {
      categoryList.value = res.data || []
    }
  } catch (error) {
    console.error('加载分类失败:', error)
    showToast('加载分类失败', 'error')
  } finally {
    loadingCategories.value = false
  }
}

/**
 * 处理添加弹窗中的科目切换
 * @param {Number} subjectId - 科目ID
 */
const handleAddSubjectChange = (subjectId) => {
  activeAddSubject.value = subjectId
  loadCategoriesForSubject(subjectId)
}

/**
 * 在弹窗中切换收藏状态
 */
const toggleCategoryFavorite = (category, subjectId) => {
  if (isFavorite(subjectId, category)) {
    // 已收藏则取消收藏
    removeFavorite(subjectId, category)
    showToast('已取消收藏', 'success')
  } else {
    // 未收藏则添加收藏
    const subject = subjects.value.find(s => s.id === subjectId)
    const subjectName = subject ? subject.name : ''

    const categoryData = {
      category: category,
      subjectId: subjectId,
      subjectName: subjectName
    }

    if (addFavorite(categoryData)) {
      showToast('添加成功', 'success')
    }
  }
}

/**
 * 处理分类点击 - 在新标签页打开真题分类页面
 */
const handleCategoryClick = (item) => {
  // 构建目标URL
  const url = router.resolve({
    path: '/exam/classify',
    query: {
      subject: item.subjectName,
      category: item.category
    }
  })
  
  // 在新标签页打开
  window.open(url.href, '_blank')
}

/**
 * 移除收藏
 */
const handleRemoveFavorite = (item) => {
  showConfirm({
    title: '提示',
    message: `确定要取消收藏「${item.category}」吗？`,
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning'
  }).then((confirmed) => {
    if (confirmed) {
      removeFavorite(item.subjectId, item.category)
      showToast('已取消收藏', 'success')
    }
  })
}

/**
 * 清空所有收藏
 */
const handleClearAll = () => {
  showConfirm({
    title: '警告',
    message: '确定要清空所有收藏吗？此操作不可恢复。',
    confirmText: '确定',
    cancelText: '取消',
    type: 'danger'
  }).then((confirmed) => {
    if (confirmed) {
      clearAllFavorites()
      showToast('已清空收藏', 'success')
    }
  })
}
</script>


<style scoped>
/**
 * 个人中心样式
 * 采用经典左右布局
 * 使用 Tailwind CSS
 */

/* 分类卡片悬停效果（已通过 group 类实现） */

/* 响应式布局 */
@media (max-width: 768px) {
  .sidebar {
    width: 100%;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .category-items {
    grid-template-columns: 1fr;
  }
}
</style>
