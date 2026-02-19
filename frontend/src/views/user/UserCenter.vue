<template>
  <div class="min-h-[calc(100vh-60px)] pt-[60px] bg-[#FBF7F2] flex gap-4 px-4 pb-4">
    <!-- 左侧边栏 -->
    <aside class="w-[280px] flex-shrink-0">
      <!-- 个人信息卡片 -->
      <el-card class="mb-4 text-center" shadow="never">
        <div class="flex justify-center items-center w-20 h-20 mx-auto mb-4 rounded-full bg-[rgba(139,111,71,0.1)]">
          <el-icon :size="60" color="#8B7355">
            <User />
          </el-icon>
        </div>
        <div>
          <h3 class="text-[#333] text-lg mb-2">{{ authStore.userInfo?.username }}</h3>
          <el-tag :type="roleTagType" size="small">{{ roleText }}</el-tag>
        </div>
      </el-card>

      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        class="border-none bg-transparent"
        @select="handleMenuSelect"
      >
        <el-menu-item index="favorites">
          <el-icon><Star /></el-icon>
          <span>我的收藏</span>
          <span v-if="totalCount > 0" class="ml-auto inline-flex items-center justify-center bg-[#f56c6c] text-white text-[11px] font-medium w-[18px] h-[18px] rounded-full leading-1">{{ totalCount }}</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧内容区域 -->
    <main class="flex-1">
      <el-card v-if="activeMenu === 'favorites'" class="min-h-[600px]">
        <!-- 收藏夹标题 -->
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="flex items-center gap-2 text-[#333] text-xl m-0">
              <el-icon><Star /></el-icon>
              我的收藏
            </h2>
            <div class="flex gap-4">
              <CustomButton
                size="small"
                type="primary"
                @click="openAddDialogForSubject()"
              >
                添加收藏
              </CustomButton>
              <CustomButton
                v-if="totalCount > 0"
                size="small"
                type="danger"
                @click="handleClearAll"
              >
                清空收藏
              </CustomButton>
            </div>
          </div>
        </template>

        <!-- 按科目分类展示 -->
        <div v-loading="loadingSubjects" class="pt-4">
          <el-tabs v-model="activeSubjectTab" class="">
            <el-tab-pane
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :name="subject.id"
            >
              <div class="pt-4">
                <template v-if="getFavoritesForSubject(subject.id).length > 0">
                  <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4">
                    <div
                      v-for="item in getFavoritesForSubject(subject.id)"
                      :key="item.id"
                      class="flex items-center justify-between p-4 bg-white border border-[rgba(139,111,71,0.2)] rounded transition-all duration-300 hover:border-[#8B6F47] hover:shadow-[0_2px_4px_rgba(0,0,0,0.08)]"
                    >
                      <div class="flex items-center gap-2 flex-1 cursor-pointer" @click="handleCategoryClick(item)">
                        <el-icon class="text-[#8B6F47] flex-shrink-0" :size="16"><Folder /></el-icon>
                        <span class="text-[#333] text-sm truncate">{{ item.category }}</span>
                      </div>
                      <CustomButton
                        class="flex-shrink-0 opacity-0 transition-opacity duration-150"
                        type="text"
                        size="small"
                        :icon="Delete"
                        @click="handleRemoveFavorite(item)"
                      />
                    </div>
                  </div>
                </template>
                <el-empty
                  v-else
                  description="该科目下暂无收藏"
                  :image-size="120"
                />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>
    </main>

    <!-- 添加收藏弹窗 -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加收藏"
      width="600px"
      append-to-body
      top="15vh"
    >
      <div>
        <el-tabs
          v-model="activeAddSubject"
          @tab-click="handleAddSubjectChange"
          class=""
        >
          <el-tab-pane
            v-for="subject in subjects"
            :key="subject.id"
            :label="subject.name"
            :name="subject.id"
          >
            <div class="h-[400px] overflow-y-auto p-4" v-loading="loadingCategories">
              <template v-if="categoryList && categoryList.length > 0">
                <div class="grid grid-cols-2 gap-3">
                  <div
                    v-for="category in categoryList"
                    :key="category"
                    class="flex items-center justify-between p-3 bg-white border border-[#dfe2e5] rounded cursor-pointer transition-all duration-200 hover:border-[#8B6F47] hover:bg-[rgba(139,111,71,0.05)]"
                    :class="{ 'bg-[rgba(103,194,58,0.1)] border-[#67c23a]': isFavorite(subject.id, category) }"
                    @click="toggleCategoryFavorite(category, subject.id)"
                  >
                    <span class="text-sm text-[#666] truncate flex-1 mr-2 text-left overflow-hidden text-ellipsis whitespace-nowrap" :class="{ 'text-[#67c23a]': isFavorite(subject.id, category) }">{{ category }}</span>
                    <el-icon class="text-[#666] text-base transition-all duration-200" :class="{ 'text-[#67c23a]': isFavorite(subject.id, category) }">
                      <Check v-if="isFavorite(subject.id, category)" />
                      <Plus v-else />
                    </el-icon>
                  </div>
                </div>
              </template>
              <el-empty v-else description="该科目暂无题目分类" :image-size="100" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Star, Folder, Delete, Plus, Check } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useFavorites } from '@/composables/useFavorites'
import { getEnabledSubjects } from '@/api/subject'
import { getExamCategoriesBySubject } from '@/api/exam'
import CustomButton from '@/components/basic/CustomButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const { favorites, totalCount, removeFavorite, clearAllFavorites, isFavorite, addFavorite } = useFavorites()

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
    ElMessage.error('加载分类失败')
  } finally {
    loadingCategories.value = false
  }
}

/**
 * 处理添加弹窗中的科目切换
 */
const handleAddSubjectChange = (tab) => {
  loadCategoriesForSubject(tab.props.name)
}

/**
 * 在弹窗中切换收藏状态
 */
const toggleCategoryFavorite = (category, subjectId) => {
  if (isFavorite(subjectId, category)) {
    // 已收藏则取消收藏
    removeFavorite(subjectId, category)
    ElMessage.success('已取消收藏')
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
      ElMessage.success('添加成功')
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
  ElMessageBox.confirm(
    `确定要取消收藏「${item.category}」吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    removeFavorite(item.subjectId, item.category)
    ElMessage.success('已取消收藏')
  }).catch(() => {
    // 用户取消
  })
}

/**
 * 清空所有收藏
 */
const handleClearAll = () => {
  ElMessageBox.confirm(
    '确定要清空所有收藏吗？此操作不可恢复。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    clearAllFavorites()
    ElMessage.success('已清空收藏')
  }).catch(() => {
    // 用户取消
  })
}
</script>


<style scoped>
/**
 * 个人中心样式
 * 采用经典左右布局
 * 使用 Tailwind CSS
 */

/* Element Plus 菜单组件样式覆盖 */
.sidebar-menu :deep(.el-menu-item) {
  background-color: white;
  margin-bottom: 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: rgba(139, 111, 71, 0.05);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
}

/* 分类卡片悬停显示删除按钮 */
.category-card:hover .remove-btn {
  opacity: 1;
}

/* Tabs 样式优化 */
:deep(.el-tabs__nav-wrap::after) {
  background-color: #dfe2e5;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  height: 48px;
}

:deep(.el-tabs__item.is-active) {
  color: #8B6F47;
  font-weight: 600;
}

:deep(.el-tabs__item:hover) {
  color: #9d825a;
}

:deep(.el-tabs__active-bar) {
  background-color: #8B6F47;
}

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
