import { computed, onBeforeUnmount, onDeactivated, ref, watch } from 'vue'

/** 管理大纲的原生鼠标拖拽；持久化由页面负责，不直接修改分类数组。 */
export function useCategoryDrag({ categories, enabled, containerRef, expandedKeys, onMove }) {
  const draggingId = ref(null)
  const dropTarget = ref(null)
  let expandTimer = null
  let expandTargetId = null
  let scrollFrame = null
  let pointer = null

  const draggingIds = computed(() => {
    if (draggingId.value === null) return new Set()
    const children = new Map()
    for (const item of categories.value) {
      const list = children.get(item.parentId) || []
      list.push(item.id)
      children.set(item.parentId, list)
    }
    const ids = new Set()
    const stack = [draggingId.value]
    while (stack.length) {
      const id = stack.pop()
      if (ids.has(id)) continue
      ids.add(id)
      stack.push(...(children.get(id) || []))
    }
    return ids
  })

  const dragMessage = computed(() => {
    if (draggingId.value === null) return ''
    if (!dropTarget.value) return '拖到行的上下边缘排序，拖到中部设为子分类；Esc 取消'
    return dropTarget.value.message
  })

  const clearExpandTimer = () => {
    clearTimeout(expandTimer)
    expandTimer = null
    expandTargetId = null
  }

  const clearTarget = () => {
    dropTarget.value = null
    clearExpandTimer()
  }

  const resetDrag = () => {
    draggingId.value = null
    clearTarget()
    pointer = null
    cancelAnimationFrame(scrollFrame)
    scrollFrame = null
    window.removeEventListener('keydown', handleKeydown)
  }

  const handleKeydown = (event) => {
    if (event.key === 'Escape') resetDrag()
  }

  const evaluateTarget = (targetId, position, sourceId = draggingId.value) => {
    const byId = new Map(categories.value.map(item => [item.id, item]))
    const source = byId.get(sourceId)
    const target = byId.get(targetId)
    const result = { targetId, position, valid: false, message: '' }
    // 提交时拖拽状态已经清理，不能依赖 draggingIds 判断目标是否合法。
    const targetAncestors = new Set()
    let ancestor = target
    while (ancestor && !targetAncestors.has(ancestor.id)) {
      targetAncestors.add(ancestor.id)
      ancestor = byId.get(ancestor.parentId)
    }
    if (!['before', 'inside', 'after'].includes(position)
      || (targetId === null && position !== 'inside')) {
      result.message = '无效的放置位置'
    } else if (!source || (targetId !== null && !target)) {
      result.message = '分类已变化，请刷新后重试'
    } else if (target && source.subjectId !== target.subjectId) {
      result.message = '不能跨科目移动分类'
    } else if (targetAncestors.has(sourceId)) {
      result.message = '不能放到自身或自己的子孙分类中'
    } else {
      const parentId = !target ? null : position === 'inside' ? target.id : (target.parentId ?? null)
      const siblings = categories.value
        .filter(item => item.subjectId === source.subjectId && (item.parentId ?? null) === parentId)
        .sort((a, b) => (a.orderNum ?? 0) - (b.orderNum ?? 0) || a.id - b.id)
      const nextIds = siblings.filter(item => item.id !== source.id).map(item => item.id)
      let index = nextIds.length
      if (target && position !== 'inside') {
        index = nextIds.indexOf(target.id) + (position === 'after' ? 1 : 0)
      }
      nextIds.splice(index, 0, source.id)
      // 比较实际父级与同级 ID 顺序，而非落点位置或排序数字是否变化。
      if ((source.parentId ?? null) === parentId && siblings.length === nextIds.length
        && siblings.every((item, i) => item.id === nextIds[i])) {
        result.message = '位置未改变'
      } else {
        result.valid = true
        result.message = !target ? '移至顶级末尾'
          : position === 'inside' ? `移入「${target.name}」，成为最后一个子分类`
            : `放到「${target.name}」${position === 'before' ? '之前' : '之后'}，与其同级`
      }
    }
    return result
  }

  const canMove = (sourceId, { targetId = null, position }) => (
    evaluateTarget(targetId, position, sourceId).valid
  )

  const setTarget = (targetId, position) => {
    const target = evaluateTarget(targetId, position)
    if (dropTarget.value?.targetId !== targetId || dropTarget.value?.position !== position
      || dropTarget.value?.message !== target.message) {
      dropTarget.value = target
    }
    if (target.valid && position === 'inside' && targetId !== null
      && !expandedKeys.value.includes(targetId)) {
      if (expandTargetId !== targetId) {
        clearExpandTimer()
        expandTargetId = targetId
        expandTimer = setTimeout(() => {
          if (!expandedKeys.value.includes(targetId)) expandedKeys.value.push(targetId)
          clearExpandTimer()
        }, 650)
      }
    } else {
      clearExpandTimer()
    }
    return target
  }

  const getPosition = (element, clientY) => {
    const rect = element.getBoundingClientRect()
    const ratio = (clientY - rect.top) / rect.height
    return ratio < 0.25 ? 'before' : ratio > 0.75 ? 'after' : 'inside'
  }

  // 滚动后重新命中落点，避免鼠标静止时仍保存滚动前的目标。
  const updateTargetAtPointer = () => {
    const container = containerRef.value
    if (!container || !pointer) return clearTarget()
    const element = document.elementFromPoint(pointer.x, pointer.y)
    if (!element || !container.contains(element)) return clearTarget()
    if (element.closest('[data-category-root-drop]')) return setTarget(null, 'inside')
    const row = element.closest('[data-category-id]')
    if (row) return setTarget(Number(row.dataset.categoryId), getPosition(row, pointer.y))
    clearTarget()
  }

  const scrollStep = () => {
    if (draggingId.value === null) return
    const container = containerRef.value
    if (container && pointer) {
      const rect = container.getBoundingClientRect()
      if (pointer.x >= rect.left && pointer.x <= rect.right
        && pointer.y >= rect.top && pointer.y <= rect.bottom) {
        const edge = 48
        const top = pointer.y - rect.top
        const bottom = rect.bottom - pointer.y
        const speed = top < edge ? -Math.ceil((edge - top) / 4)
          : bottom < edge ? Math.ceil((edge - bottom) / 4) : 0
        if (speed) {
          container.scrollTop += speed
          updateTargetAtPointer()
        }
      }
    }
    scrollFrame = requestAnimationFrame(scrollStep)
  }

  const handleDragStart = (event, node) => {
    if (!enabled.value || !event.dataTransfer) {
      event.preventDefault()
      return
    }
    resetDrag()
    draggingId.value = node.id
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(node.id))
    const row = event.currentTarget.closest('[data-category-id]')
    if (row) event.dataTransfer.setDragImage(row, 24, row.clientHeight / 2)
    window.addEventListener('keydown', handleKeydown)
    scrollFrame = requestAnimationFrame(scrollStep)
  }

  const handleContainerDragOver = (event) => {
    if (draggingId.value === null) return
    event.preventDefault()
    pointer = { x: event.clientX, y: event.clientY }
    updateTargetAtPointer()
    if (event.dataTransfer) event.dataTransfer.dropEffect = dropTarget.value?.valid ? 'move' : 'none'
  }

  const handleContainerDragLeave = (event) => {
    if (event.relatedTarget && containerRef.value?.contains(event.relatedTarget)) return
    pointer = null
    clearTarget()
  }

  const handleDrop = (event) => {
    if (draggingId.value === null) return
    event.preventDefault()
    const preview = dropTarget.value
    pointer = { x: event.clientX, y: event.clientY }
    updateTargetAtPointer()
    const sourceId = draggingId.value
    const target = dropTarget.value
    // 松手重新命中的位置必须与最后预览一致，避免自动展开/滚动后意外提交新目标。
    const canSave = enabled.value && preview?.valid && target?.valid
      && preview.targetId === target.targetId && preview.position === target.position
    resetDrag()
    if (canSave) onMove(sourceId, { targetId: target.targetId, position: target.position })
  }

  watch(enabled, value => {
    if (!value) resetDrag()
  })
  onDeactivated(resetDrag)
  onBeforeUnmount(resetDrag)

  return {
    draggingId, draggingIds, dropTarget, dragMessage, canMove,
    handleDragStart, handleContainerDragOver, handleContainerDragLeave, handleDrop, resetDrag
  }
}
