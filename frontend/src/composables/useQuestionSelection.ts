/**
 * 模拟题临时选择集逻辑。
 * 选择集按题目 ID 去重，并保留管理员的选择顺序，供分页表格和批量复制共用。
 */
import { computed, ref } from 'vue'
import type { MockQuestion } from '@/types'

export function useQuestionSelection() {
  const selectedIds = ref<number[]>([])
  const questionMap = ref(new Map<number, MockQuestion>())

  const selectedQuestions = computed(() => {
    return selectedIds.value
      .map(id => questionMap.value.get(id))
      .filter((question): question is MockQuestion => Boolean(question))
  })

  const selectedCount = computed(() => selectedIds.value.length)

  const isSelected = (questionId: number) => selectedIds.value.includes(questionId)

  const selectQuestion = (question: MockQuestion, selected: boolean) => {
    const nextMap = new Map(questionMap.value)
    const exists = selectedIds.value.includes(question.id)

    if (selected && !exists) {
      selectedIds.value = [...selectedIds.value, question.id]
      nextMap.set(question.id, question)
    } else if (!selected && exists) {
      selectedIds.value = selectedIds.value.filter(id => id !== question.id)
      nextMap.delete(question.id)
    } else if (selected) {
      nextMap.set(question.id, question)
    }

    questionMap.value = nextMap
  }

  const selectQuestions = (questions: MockQuestion[], selected: boolean) => {
    const nextMap = new Map(questionMap.value)
    const nextIds = [...selectedIds.value]

    questions.forEach(question => {
      const index = nextIds.indexOf(question.id)
      if (selected) {
        if (index === -1) nextIds.push(question.id)
        nextMap.set(question.id, question)
      } else if (index !== -1) {
        nextIds.splice(index, 1)
        nextMap.delete(question.id)
      }
    })

    selectedIds.value = nextIds
    questionMap.value = nextMap
  }

  const syncQuestions = (questions: MockQuestion[]) => {
    const nextMap = new Map(questionMap.value)
    questions.forEach(question => {
      if (nextMap.has(question.id)) nextMap.set(question.id, question)
    })
    questionMap.value = nextMap
  }

  const updateQuestion = (question: MockQuestion) => {
    if (!questionMap.value.has(question.id)) return
    const nextMap = new Map(questionMap.value)
    nextMap.set(question.id, question)
    questionMap.value = nextMap
  }

  const removeQuestion = (questionId: number) => {
    selectedIds.value = selectedIds.value.filter(id => id !== questionId)
    const nextMap = new Map(questionMap.value)
    nextMap.delete(questionId)
    questionMap.value = nextMap
  }

  const moveQuestion = (questionId: number, direction: -1 | 1) => {
    const currentIndex = selectedIds.value.indexOf(questionId)
    const targetIndex = currentIndex + direction
    if (currentIndex === -1 || targetIndex < 0 || targetIndex >= selectedIds.value.length) return

    const nextIds = [...selectedIds.value]
    const [movedId] = nextIds.splice(currentIndex, 1)
    nextIds.splice(targetIndex, 0, movedId)
    selectedIds.value = nextIds
  }

  const clearSelection = () => {
    selectedIds.value = []
    questionMap.value = new Map()
  }

  return {
    selectedIds,
    selectedQuestions,
    selectedCount,
    isSelected,
    selectQuestion,
    selectQuestions,
    syncQuestions,
    updateQuestion,
    removeQuestion,
    moveQuestion,
    clearSelection,
  }
}
