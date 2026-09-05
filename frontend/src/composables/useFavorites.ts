/**
 * 收藏夹工具模块
 * 功能：管理用户收藏的题目分类
 * 遵循KISS原则：简单的localStorage存储
 * 遵循YAGNI原则：只实现当前需要的功能
 * 遵循SOLID原则：单一职责，便于未来迁移到后端API
 */
import { ref, computed } from 'vue'

export interface FavoriteCategory { id: string; category: string; subjectId: number; subjectName: string; timestamp: number }
function isFavoriteCategory(value: unknown): value is FavoriteCategory {
  return typeof value === 'object' && value !== null && 'id' in value && typeof value.id === 'string'
    && 'category' in value && typeof value.category === 'string'
    && 'subjectId' in value && typeof value.subjectId === 'number'
    && 'subjectName' in value && typeof value.subjectName === 'string'
    && 'timestamp' in value && typeof value.timestamp === 'number'
}
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
  const favorites = ref<FavoriteCategory[]>([])

  /**
   * 从localStorage加载收藏列表
   */
  const loadFavorites = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed: unknown = JSON.parse(stored)
        favorites.value = Array.isArray(parsed) ? parsed.filter(isFavoriteCategory) : []
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
  const generateId = (subjectId: number, category: string) => {
    return `${subjectId}_${category}`
  }

  /**
   * 添加分类到收藏夹
   * @param {FavoriteCategory} item - 分类信息
   */
  const addFavorite = (item: Omit<FavoriteCategory, 'id' | 'timestamp'>) => {
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
  const removeFavorite = (subjectId: number, category: string) => {
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
   * 检查分类是否已收藏
   * @param {Number} subjectId - 科目ID
   * @param {String} category - 分类名称
   * @returns {Boolean}
   */
  const isFavorite = (subjectId: number, category: string) => {
    const id = generateId(subjectId, category)
    return favorites.value.some(item => item.id === id)
  }

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
    totalCount,
    addFavorite,
    removeFavorite,
    isFavorite,
    clearAllFavorites,
    loadFavorites
  }
}
