/**
 * 题目无限滚动列表逻辑。
 * 使用后端分页接口分段加载数据，页面不展示传统分页条，并保留请求竞态保护。
 */
import { computed, ref } from 'vue'
import type { ApiResponse, Paginated } from '@/types'

interface Options<T> {
  pageSize?: number
  getItemKey?: (item: T) => string | number
}

export function useInfiniteQuestionList<T>(
  loadPage: (page: number, pageSize: number) => Promise<ApiResponse<Paginated<T>>>,
  options: Options<T> = {},
) {
  const pageSize = options.pageSize || 50
  const getItemKey = options.getItemKey
  const items = ref<T[]>([])
  const total = ref(0)
  const currentPage = ref(0)
  const totalPages = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  const error = ref('')
  let requestVersion = 0

  const hasMore = computed(() => {
    return currentPage.value === 0 || currentPage.value < totalPages.value
  })
  const loadedCount = computed(() => items.value.length)

  const appendItems = (nextItems: T[]) => {
    if (!getItemKey) {
      items.value = currentPage.value === 0 ? nextItems : [...items.value, ...nextItems]
      return
    }

    const existingKeys = new Set(items.value.map(getItemKey))
    const uniqueItems = nextItems.filter(item => {
      const key = getItemKey(item)
      if (existingKeys.has(key)) return false
      existingKeys.add(key)
      return true
    })
    items.value = currentPage.value === 0 ? uniqueItems : [...items.value, ...uniqueItems]
  }

  const loadMoreInternal = async (version: number, retry = false) => {
    if (version !== requestVersion) return
    if (currentPage.value > 0 && !hasMore.value) return
    if (loading.value || loadingMore.value) return
    if (error.value && !retry) return

    const nextPage = currentPage.value + 1
    if (nextPage === 1) loading.value = true
    else loadingMore.value = true
    if (retry) error.value = ''

    try {
      const response = await loadPage(nextPage, pageSize)
      if (version !== requestVersion) return
      if (response.code !== 200 || !response.data) {
        error.value = response.message || '题目加载失败，请重试。'
        return
      }

      const pageInfo = response.data.pagination
      appendItems(response.data.lists || [])
      currentPage.value = pageInfo.page
      total.value = pageInfo.total
      totalPages.value = pageInfo.totalPages
      error.value = ''
    } catch (requestError) {
      if (version !== requestVersion) return
      error.value = '题目加载失败，请重试。'
      console.error('无限滚动加载题目失败:', requestError)
    } finally {
      if (version === requestVersion) {
        loading.value = false
        loadingMore.value = false
      }
    }
  }

  const reload = async () => {
    requestVersion += 1
    const version = requestVersion
    items.value = []
    total.value = 0
    currentPage.value = 0
    totalPages.value = 0
    loading.value = false
    loadingMore.value = false
    error.value = ''
    await loadMoreInternal(version)
  }

  const loadMore = async () => {
    await loadMoreInternal(requestVersion)
  }

  const retry = async () => {
    if (currentPage.value === 0) {
      await reload()
      return
    }
    await loadMoreInternal(requestVersion, true)
  }

  const reset = () => {
    requestVersion += 1
    items.value = []
    total.value = 0
    currentPage.value = 0
    totalPages.value = 0
    loading.value = false
    loadingMore.value = false
    error.value = ''
  }

  return {
    items,
    total,
    loadedCount,
    currentPage,
    totalPages,
    hasMore,
    loading,
    loadingMore,
    error,
    pageSize,
    reload,
    loadMore,
    retry,
    reset,
  }
}
