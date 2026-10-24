/**
 * 管理分类大纲的激活状态、滚动观察和页内跳转，并绑定到业务页面提供的内容滚动容器。
 */
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

  const scrollToElement = (
    target: HTMLElement,
    block: 'start' | 'center' = 'start',
    animate = true,
  ) => {
    const root = containerRef.value
    if (!root || !root.contains(target)) return false

    const rootRect = root.getBoundingClientRect()
    const targetRect = target.getBoundingClientRect()
    const targetStyle = getComputedStyle(target)
    const scrollMarginTop = Number.parseFloat(targetStyle.scrollMarginTop) || 0
    const scrollMarginBottom = Number.parseFloat(targetStyle.scrollMarginBottom) || 0
    const scrollportTop = rootRect.top + root.clientTop
    const targetTop = block === 'center'
      ? root.scrollTop + targetRect.top + targetRect.height / 2
        + (scrollMarginTop - scrollMarginBottom) / 2
        - scrollportTop - root.clientHeight / 2
      : root.scrollTop + targetRect.top - scrollportTop - scrollMarginTop
    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false

    // 只滚动题目内容容器，避免 scrollIntoView 连带移动外层布局。
    if (!animate || prefersReducedMotion) {
      root.scrollTop = targetTop
    } else {
      root.scrollTo({
        top: targetTop,
        behavior: 'smooth',
      })
    }
    return true
  }

  const scrollToCategory = (anchorId: string, animate = true) => {
    const target = document.getElementById(anchorId)
    if (!target || !scrollToElement(target, 'start', animate)) return

    activeId.value = anchorId
  }

  const scrollToCategoryImmediately = (anchorId: string) => scrollToCategory(anchorId, false)

  // 布局外壳负责创建滚动容器，容器引用变化时也需要重新建立观察器。
  watch([items, containerRef], refresh, { flush: 'post', immediate: true })
  onBeforeUnmount(() => {
    refreshVersion += 1
    disconnect()
  })

  return {
    activeId,
    scrollToCategory,
    scrollToCategoryImmediately,
    scrollToElement,
  }
}
