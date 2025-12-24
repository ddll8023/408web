/**
 * 收藏夹工具模块
 * 功能：管理用户收藏的题目分类
 * 遵循KISS原则：简单的localStorage存储
 * 遵循YAGNI原则：只实现当前需要的功能
 * 遵循SOLID原则：单一职责，便于未来迁移到后端API
 */
import { ref, computed } from 'vue'

// 本地存储的键名
const STORAGE_KEY = 'user_favorites_categories'

/**
 * 收藏夹数据结构
 * @typedef {Object} FavoriteCategory
 * @property {String} category - 分类名称（唯一标识）
 * @property {Number} subjectId - 所属科目ID
 * @property {String} subjectName - 所属科目名称
 * @property {Number} timestamp - 收藏时间戳
 */

/**
 * 收藏夹 Composable
 * @returns {Object} 收藏夹API
 */
export function useFavorites() {
  // 收藏列表
  const favorites = ref([])

  /**
   * 从localStorage加载收藏列表
   */
  const loadFavorites = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        favorites.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('加载收藏列表失败:', error)
      favorites.value = []
    }
  }

  /**
   * 保存收藏列表到localStorage
   */
  const saveFavorites = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites.value))
    } catch (error) {
      console.error('保存收藏列表失败:', error)
    }
  }

  /**
   * 生成收藏项的唯一ID（科目ID + 分类名称）
   * @param {Number} subjectId - 科目ID
   * @param {String} category - 分类名称
   * @returns {String} 唯一ID
   */
  const generateId = (subjectId, category) => {
    return `${subjectId}_${category}`
  }

  /**
   * 添加分类到收藏夹
   * @param {FavoriteCategory} item - 分类信息
   */
  const addFavorite = (item) => {
    // 检查是否已收藏
    if (isFavorite(item.subjectId, item.category)) {
      return false
    }

    // 添加时间戳
    const favoriteItem = {
      ...item,
      id: generateId(item.subjectId, item.category),
      timestamp: Date.now()
    }

    favorites.value.push(favoriteItem)
    saveFavorites()
    return true
  }

  /**
   * 从收藏夹移除分类
   * @param {Number} subjectId - 科目ID
   * @param {String} category - 分类名称
   */
  const removeFavorite = (subjectId, category) => {
    const id = generateId(subjectId, category)
    const index = favorites.value.findIndex(item => item.id === id)
    if (index > -1) {
      favorites.value.splice(index, 1)
      saveFavorites()
      return true
    }
    return false
  }

  /**
   * 切换收藏状态
   * @param {FavoriteCategory} item - 分类信息
   * @returns {Boolean} 收藏后的状态（true=已收藏，false=未收藏）
   */
  const toggleFavorite = (item) => {
    if (isFavorite(item.subjectId, item.category)) {
      removeFavorite(item.subjectId, item.category)
      return false
    } else {
      addFavorite(item)
      return true
    }
  }

  /**
   * 检查分类是否已收藏
   * @param {Number} subjectId - 科目ID
   * @param {String} category - 分类名称
   * @returns {Boolean}
   */
  const isFavorite = (subjectId, category) => {
    const id = generateId(subjectId, category)
    return favorites.value.some(item => item.id === id)
  }

  /**
   * 按科目分组的收藏列表
   * @returns {Array<{subjectId, subjectName, categories}>}
   */
  const favoritesBySubject = computed(() => {
    const grouped = {}

    favorites.value.forEach(item => {
      const key = item.subjectId
      if (!grouped[key]) {
        grouped[key] = {
          subjectId: item.subjectId,
          subjectName: item.subjectName,
          categories: []
        }
      }
      grouped[key].categories.push(item)
    })

    // 转换为数组并按时间倒序排序
    return Object.values(grouped).map(group => ({
      ...group,
      categories: group.categories.sort((a, b) => b.timestamp - a.timestamp)
    }))
  })

  /**
   * 收藏总数
   */
  const totalCount = computed(() => favorites.value.length)

  /**
   * 清空所有收藏
   */
  const clearAllFavorites = () => {
    favorites.value = []
    saveFavorites()
  }

  // 初始化时加载数据
  loadFavorites()

  return {
    favorites,
    favoritesBySubject,
    totalCount,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isFavorite,
    clearAllFavorites,
    loadFavorites
  }
}
