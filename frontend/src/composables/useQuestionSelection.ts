/**
 * 出题工作台临时选择集逻辑。
 * 选择集以「题目来源类型:题目 ID」为键去重，并保留管理员的选择顺序，供章节列表和批量复制共用；
 * 使用复合键是因为模拟题与改编题的主键来自不同数据表，裸 ID 会互相覆盖。
 */
import { computed, ref, shallowRef } from 'vue'

/** 选择集可容纳的最小题目结构：来源类型加主键即可生成唯一键。 */
export interface SelectableQuestion {
  id: number
  questionKind: 'mock' | 'adaptation'
}

/** 生成跨题目类型唯一的选择键，供选择集、出题篮和批量子组件共用。 */
export function getQuestionSelectionKey(question: SelectableQuestion): string {
  return `${question.questionKind}:${question.id}`
}

/** 管理跨来源题目的选择顺序和数据同步，供出题篮与章节列表共用。 */
export function useQuestionSelection<T extends SelectableQuestion>() {
  const selectedKeys = ref<string[]>([])
  // Map 通过复制并替换根值更新，避免泛型解包，同时保留题目已有的响应式引用。
  const questionMap = shallowRef(new Map<string, T>())

  const selectedQuestions = computed<T[]>(() => {
    return selectedKeys.value
      .map(key => questionMap.value.get(key))
      .filter((question): question is T => question !== undefined)
  })

  const selectedCount = computed(() => selectedKeys.value.length)

  const isSelected = (question: T) =>
    selectedKeys.value.includes(getQuestionSelectionKey(question))

  const selectQuestion = (question: T, selected: boolean) => {
    const key = getQuestionSelectionKey(question)
    const nextMap = new Map(questionMap.value)
    const exists = selectedKeys.value.includes(key)

    if (selected && !exists) {
      selectedKeys.value = [...selectedKeys.value, key]
      nextMap.set(key, question)
    } else if (!selected && exists) {
      selectedKeys.value = selectedKeys.value.filter(current => current !== key)
      nextMap.delete(key)
    } else if (selected) {
      nextMap.set(key, question)
    }

    questionMap.value = nextMap
  }

  const selectQuestions = (questions: T[], selected: boolean) => {
    const nextMap = new Map(questionMap.value)
    const nextKeys = [...selectedKeys.value]

    questions.forEach(question => {
      const key = getQuestionSelectionKey(question)
      const index = nextKeys.indexOf(key)
      if (selected) {
        if (index === -1) nextKeys.push(key)
        nextMap.set(key, question)
      } else if (index !== -1) {
        nextKeys.splice(index, 1)
        nextMap.delete(key)
      }
    })

    selectedKeys.value = nextKeys
    questionMap.value = nextMap
  }

  const syncQuestions = (questions: T[]) => {
    const nextMap = new Map(questionMap.value)
    questions.forEach(question => {
      const key = getQuestionSelectionKey(question)
      if (nextMap.has(key)) nextMap.set(key, question)
    })
    questionMap.value = nextMap
  }

  const updateQuestion = (question: T) => {
    const key = getQuestionSelectionKey(question)
    if (!questionMap.value.has(key)) return
    const nextMap = new Map(questionMap.value)
    nextMap.set(key, question)
    questionMap.value = nextMap
  }

  const removeQuestion = (key: string) => {
    selectedKeys.value = selectedKeys.value.filter(current => current !== key)
    const nextMap = new Map(questionMap.value)
    nextMap.delete(key)
    questionMap.value = nextMap
  }

  const moveQuestion = (key: string, direction: -1 | 1) => {
    const currentIndex = selectedKeys.value.indexOf(key)
    const targetIndex = currentIndex + direction
    if (currentIndex === -1 || targetIndex < 0 || targetIndex >= selectedKeys.value.length) return

    const nextKeys = [...selectedKeys.value]
    const [movedKey] = nextKeys.splice(currentIndex, 1)
    nextKeys.splice(targetIndex, 0, movedKey)
    selectedKeys.value = nextKeys
  }

  const clearSelection = () => {
    selectedKeys.value = []
    questionMap.value = new Map()
  }

  return {
    selectedKeys,
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
