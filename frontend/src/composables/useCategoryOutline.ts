import { nextTick, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import type { CategoryOutlineItem } from '@/types'

interface UseCategoryOutlineOptions {
  containerRef: Ref<HTMLElement | null>
  items: Readonly<Ref<CategoryOutlineItem[]>>
}

/**
 * 管理分类大纲的当前项、滚动跳转和内容分组观察。
 * 观察根节点使用题目内容滚动容器，而不是浏览器窗口。
 */
export function useCategoryOutline({
  containerRef,
  items,
}: UseCategoryOutlineOptions) {
  const activeId = ref('')
  let observer: IntersectionObserver | null = null
  let refreshVersion = 0

  const disconnect = () => {
    observer?.disconnect()
    observer = null
  }

  const refresh = async () => {
    const version = ++refreshVersion
    disconnect()
    await nextTick()

    if (version !== refreshVersion) return

    const root = containerRef.value
    const currentItems = items.value
    if (
      !root
      || currentItems.length === 0
      || typeof IntersectionObserver === 'undefined'
    ) {
      activeId.value = currentItems[0]?.anchorId || ''
      return
    }

    const currentIds = new Set(currentItems.map(item => item.anchorId))
    if (!currentIds.has(activeId.value)) {
      activeId.value = currentItems[0].anchorId
    }

    const sections = currentItems
      .map(item => document.getElementById(item.anchorId))
      .filter((element): element is HTMLElement => element instanceof HTMLElement)

    if (sections.length === 0) return

    observer = new IntersectionObserver((entries) => {
      const visibleSections = entries
        .filter(entry => entry.isIntersecting)
        .sort((first, second) => first.boundingClientRect.top - second.boundingClientRect.top)

      const firstVisibleSection = visibleSections[0]
      if (firstVisibleSection) {
        activeId.value = firstVisibleSection.target.id
      }
    }, {
      root,
      rootMargin: '-12% 0px -68% 0px',
      threshold: 0,
    })

    sections.forEach(section => observer?.observe(section))
  }

  const scrollToCategory = (anchorId: string) => {
    const target = document.getElementById(anchorId)
    if (!target) return

    activeId.value = anchorId
    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false
    target.scrollIntoView({
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
      block: 'start',
    })
  }

  watch(items, refresh, { flush: 'post', immediate: true })
  onBeforeUnmount(() => {
    refreshVersion += 1
    disconnect()
  })

  return {
    activeId,
    scrollToCategory,
  }
}
