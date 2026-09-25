/**
 * 题目无限滚动列表逻辑。
 * 使用后端分页接口分段加载数据，页面不展示传统分页条，并保留请求竞态保护。
 */
import { computed, ref } from 'vue'
import type { Ref } from 'vue'
import type { ApiResponse, PageInfo, Paginated } from '@/types'

interface Options<T> {
  pageSize?: number
  getItemKey?: (item: T) => string | number
  /** 按业务规则合并新页，例如去重并保持领域排序。 */
  mergePageItems?: (currentItems: readonly T[], nextItems: readonly T[]) => T[]
  /** 覆盖分页元数据以外的“是否还有更多”规则。 */
  getHasMore?: (items: readonly T[], pagination: PageInfo) => boolean
  /** 当前模块的请求失败兜底提示。 */
  fallbackErrorMessage?: string
  /** 是否在业务响应失败时停止后续分页。 */
  stopOnResponseError?: boolean
  /** 保留调用方的错误诊断上下文。 */
  onRequestError?: (error: unknown) => void
}

export function useInfiniteQuestionList<T>(
  loadPage: (page: number, pageSize: number) => Promise<ApiResponse<Paginated<T>>>,
  options: Options<T> = {},
) {
  const pageSize = options.pageSize || 50
  const getItemKey = options.getItemKey
  const fallbackErrorMessage = options.fallbackErrorMessage || '题目加载失败，请重试。'
  const reportRequestError = options.onRequestError ?? ((requestError: unknown) => {
    console.error('无限滚动加载题目失败:', requestError)
  })
  // 泛型元素类型在 ref 解包后不再等价于 T[]，这里保留调用方声明的元素类型
  const items = ref([]) as Ref<T[]>
  const total = ref(0)
  const currentPage = ref(0)
  const totalPages = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  const error = ref('')
  const responseFailed = ref(false)
  let requestVersion = 0

  const hasMore = computed(() => {
    if (options.stopOnResponseError && responseFailed.value) return false
    if (options.getHasMore && currentPage.value > 0) {
      return options.getHasMore(items.value, {
        page: currentPage.value,
        pageSize,
        total: total.value,
        totalPages: totalPages.value,
      })
    }
    return currentPage.value === 0 || currentPage.value < totalPages.value
  })
  const loadedCount = computed(() => items.value.length)

  const appendItems = (nextItems: T[]) => {
    if (options.mergePageItems) {
      const currentItems = currentPage.value === 0 ? [] : items.value
      items.value = options.mergePageItems(currentItems, nextItems)
      return
    }

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
    responseFailed.value = false

    try {
      const response = await loadPage(nextPage, pageSize)
      if (version !== requestVersion) return
      if (response.code !== 200 || !response.data) {
        responseFailed.value = true
        error.value = response.message || fallbackErrorMessage
        return
      }

      const pageInfo = response.data.pagination
      appendItems(response.data.lists || [])
      currentPage.value = pageInfo.page
      total.value = pageInfo.total
      totalPages.value = pageInfo.totalPages
      error.value = ''
      responseFailed.value = false
    } catch (requestError) {
      if (version !== requestVersion) return
      error.value = fallbackErrorMessage
      reportRequestError(requestError)
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
    responseFailed.value = false
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
    responseFailed.value = false
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
