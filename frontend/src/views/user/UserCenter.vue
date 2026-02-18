<template>
  <div class="user-center-page">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <!-- 个人信息卡片 -->
      <el-card class="user-info-card" shadow="never">
        <div class="user-avatar">
          <el-icon :size="60" color="#8B7355">
            <User />
          </el-icon>
        </div>
        <div class="user-details">
          <h3 class="username">{{ authStore.userInfo?.username }}</h3>
          <el-tag :type="roleTagType" size="small">{{ roleText }}</el-tag>
        </div>
      </el-card>

      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="favorites">
          <el-icon><Star /></el-icon>
          <span>我的收藏</span>
          <span v-if="totalCount > 0" class="favorite-count">{{ totalCount }}</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧内容区域 -->
    <main class="content-area">
      <el-card v-if="activeMenu === 'favorites'" class="content-card">
        <!-- 收藏夹标题 -->
        <template #header>
          <div class="card-header">
            <h2>
              <el-icon><Star /></el-icon>
              我的收藏
            </h2>
            <div class="header-actions">
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
        <div v-loading="loadingSubjects" class="favorites-tabs-container">
          <el-tabs v-model="activeSubjectTab" class="favorites-tabs">
            <el-tab-pane
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :name="subject.id"
            >
              <div class="tab-content">
                <template v-if="getFavoritesForSubject(subject.id).length > 0">
                  <div class="categories-grid">
                    <div
                      v-for="item in getFavoritesForSubject(subject.id)"
                      :key="item.id"
                      class="category-card"
                    >
                      <div class="category-info" @click="handleCategoryClick(item)">
                        <el-icon class="category-icon"><Folder /></el-icon>
                        <span class="category-name">{{ item.category }}</span>
                      </div>
                      <CustomButton
                        class="remove-btn"
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
      <div class="add-dialog-content">
        <el-tabs 
          v-model="activeAddSubject" 
          @tab-click="handleAddSubjectChange"
          class="dialog-tabs"
        >
          <el-tab-pane
            v-for="subject in subjects"
            :key="subject.id"
            :label="subject.name"
            :name="subject.id"
          >
            <div class="dialog-category-container" v-loading="loadingCategories">
              <template v-if="categoryList && categoryList.length > 0">
                <div class="category-items">
                  <div 
                    v-for="category in categoryList" 
                    :key="category"
                    class="dialog-category-item"
                    :class="{ 'is-favorite': isFavorite(subject.id, category) }"
                    @click="toggleCategoryFavorite(category, subject.id)"
                  >
                    <span class="item-name">{{ category }}</span>
                    <el-icon class="item-icon">
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

.user-center-page {
  min-height: calc(100vh - 60px);
  padding-top: 60px;
  background-color: #FBF7F2;
  display: flex;
  gap: 16px;
  padding-left: 16px;
  padding-right: 16px;
  padding-bottom: 16px;
}

/* 左侧边栏 */
.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.sidebar .user-info-card {
  margin-bottom: 16px;
  text-align: center;
}

.sidebar .user-info-card .user-avatar {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background-color: rgba(139, 111, 71, 0.1);
}

.sidebar .user-info-card .user-details .username {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.sidebar .sidebar-menu {
  border: none;
  background-color: transparent;
}

.sidebar .sidebar-menu :deep(.el-menu-item) {
  background-color: white;
  margin-bottom: 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.sidebar .sidebar-menu :deep(.el-menu-item:hover) {
  background-color: rgba(139, 111, 71, 0.05);
}

.sidebar .sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(139, 111, 71, 0.1);
  color: #8B6F47;
}

.sidebar .sidebar-menu .favorite-count {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f56c6c;
  color: white;
  font-size: 11px;
  font-weight: 500;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  line-height: 1;
}

/* 右侧内容区域 */
.content-area {
  flex: 1;
}

.content-area .content-card {
  min-height: 600px;
}

.content-area .content-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.content-area .content-card .card-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  color: #333;
  margin: 0;
}

.content-area .content-card .card-header .header-actions {
  display: flex;
  gap: 16px;
}

/* Tabs 样式优化 */
.favorites-tabs-container :deep(.el-tabs__nav-wrap::after) {
  background-color: #dfe2e5;
}

.favorites-tabs-container :deep(.el-tabs__item) {
  font-size: 16px;
  height: 48px;
}

.favorites-tabs-container :deep(.el-tabs__item.is-active) {
  color: #8B6F47;
  font-weight: 600;
}

.favorites-tabs-container :deep(.el-tabs__item:hover) {
  color: #9d825a;
}

.favorites-tabs-container :deep(.el-tabs__active-bar) {
  background-color: #8B6F47;
}

.tab-content {
  padding: 16px 0;
}

/* 分类卡片网格 */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.categories-grid .category-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background-color: #fff;
  border: 1px solid rgba(139, 111, 71, 0.2);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.categories-grid .category-card:hover {
  border-color: #8B6F47;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.categories-grid .category-card .category-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  cursor: pointer;
}

.categories-grid .category-card .category-info .category-icon {
  font-size: 16px;
  color: #8B6F47;
  flex-shrink: 0;
}

.categories-grid .category-card .category-info .category-name {
  color: #333;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.categories-grid .category-card .category-info:hover .category-name {
  color: #8B6F47;
}

.categories-grid .category-card .remove-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.categories-grid .category-card:hover .remove-btn {
  opacity: 1;
}

/* 添加弹窗样式 */
.add-dialog-content {
  padding: 0;
}

.add-dialog-content .dialog-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0 16px;
}

.add-dialog-content .dialog-tabs :deep(.el-tabs__content) {
  padding: 0;
}

.add-dialog-content .dialog-category-container {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.add-dialog-content .category-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.add-dialog-content .dialog-category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background-color: #fff;
  border: 1px solid #dfe2e5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-dialog-content .dialog-category-item .item-name {
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
  text-align: left;
}

.add-dialog-content .dialog-category-item .item-icon {
  font-size: 16px;
  color: #666;
  transition: all 0.2s;
}

.add-dialog-content .dialog-category-item:hover {
  border-color: #8B6F47;
  background-color: rgba(139, 111, 71, 0.05);
}

.add-dialog-content .dialog-category-item:hover .item-icon {
  color: #8B6F47;
}

.add-dialog-content .dialog-category-item:hover .item-name {
  color: #8B6F47;
}

.add-dialog-content .dialog-category-item.is-favorite {
  background-color: rgba(103, 194, 58, 0.1);
  border-color: #67c23a;
}

.add-dialog-content .dialog-category-item.is-favorite .item-name {
  color: #67c23a;
}

.add-dialog-content .dialog-category-item.is-favorite .item-icon {
  color: #67c23a;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .user-center-page {
    flex-direction: column;
    padding: 8px;
  }

  .sidebar {
    width: 100%;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .add-dialog-content .category-items {
    grid-template-columns: 1fr;
  }
}
</style>
