import type { CategoryTreeNode, ExamQuestion } from '@/types'

/** 分类分组后的题目集合。 */
export interface ExamQuestionGroup {
  category: string
  items: ExamQuestion[]
}

interface CategoryOrderEntry {
  name: string
  order: number
}

const compareQuestions = (a: ExamQuestion, b: ExamQuestion) => {
  const yearDifference = a.year - b.year
  if (yearDifference !== 0) return yearDifference

  const questionNumberA = a.questionNumber ?? Number.POSITIVE_INFINITY
  const questionNumberB = b.questionNumber ?? Number.POSITIVE_INFINITY
  const questionNumberDifference = questionNumberA - questionNumberB
  if (questionNumberDifference !== 0) return questionNumberDifference

  return a.id - b.id
}

/** 按题目 ID 去重，并保持分类页的年份/题号顺序。 */
export const uniqueExamQuestions = (questions: readonly ExamQuestion[]) => {
  const uniqueById = new Map<number, ExamQuestion>()
  questions.forEach((exam) => {
    if (!uniqueById.has(exam.id)) {
      uniqueById.set(exam.id, exam)
    }
  })
  return Array.from(uniqueById.values()).sort(compareQuestions)
}

const flattenCategoryTree = (
  categories: readonly CategoryTreeNode[],
): CategoryOrderEntry[] => {
  const result: CategoryOrderEntry[] = []

  const visit = (category: CategoryTreeNode) => {
    result.push({ name: category.name, order: result.length })
    category.children.forEach(visit)
  }

  categories.forEach(visit)
  return result
}

const findCategory = (
  categories: readonly CategoryTreeNode[],
  categoryName: string,
): CategoryTreeNode | undefined => {
  for (const category of categories) {
    if (category.name === categoryName) return category
    const child = findCategory(category.children, categoryName)
    if (child) return child
  }
  return undefined
}

const getSelectedScope = (
  categories: readonly CategoryTreeNode[],
  selectedCategory: string,
): { entries: CategoryOrderEntry[]; found: boolean } => {
  const selected = findCategory(categories, selectedCategory)
  if (!selected) {
    return {
      entries: [{ name: selectedCategory, order: 0 }],
      found: false,
    }
  }

  const entries: CategoryOrderEntry[] = []
  const visit = (category: CategoryTreeNode) => {
    entries.push({ name: category.name, order: entries.length })
    category.children.forEach(visit)
  }
  visit(selected)
  return { entries, found: true }
}

/**
 * 按分类树分组题目。
 *
 * 一个题目可能同时带有多个分类标签。分组时按左侧分类树的显示顺序
 * 选择最后一个匹配标签，因此同一题目只会出现在最靠后的子标签中。
 */
export const groupExamQuestionsByCategory = (
  questions: readonly ExamQuestion[],
  categories: readonly CategoryTreeNode[],
  selectedCategory = '',
): ExamQuestionGroup[] => {
  const uniqueQuestions = uniqueExamQuestions(questions)
  if (uniqueQuestions.length === 0) return []

  const normalizedSelectedCategory = selectedCategory.trim()
  const allEntries = flattenCategoryTree(categories)
  const selectedScope = normalizedSelectedCategory
    ? getSelectedScope(categories, normalizedSelectedCategory)
    : { entries: allEntries, found: true }
  const scopeEntries = selectedScope.entries
  const scopeOrder = new Map(scopeEntries.map((entry) => [entry.name, entry.order]))
  const groups = new Map<string, ExamQuestion[]>()

  uniqueQuestions.forEach((exam) => {
    const rawCategories = Array.isArray(exam.category)
      ? exam.category.filter((category) => category.length > 0)
      : []
    const examCategories = new Set(rawCategories)
    const matchedCategories = scopeEntries.filter((entry) => examCategories.has(entry.name))

    let displayCategory = matchedCategories.at(-1)?.name
    if (!displayCategory && normalizedSelectedCategory && !selectedScope.found) {
      // 分类树暂未加载或该标签已从目录移除时，后端已经完成范围过滤，不能丢失题目。
      displayCategory = normalizedSelectedCategory
    }
    if (!displayCategory && !normalizedSelectedCategory) {
      displayCategory = rawCategories[0] || '未分类'
    }
    if (!displayCategory) return

    const group = groups.get(displayCategory)
    if (group) {
      group.push(exam)
    } else {
      groups.set(displayCategory, [exam])
    }
  })

  return Array.from(groups.keys())
    .sort((first, second) => {
      const firstOrder = scopeOrder.get(first) ?? Number.POSITIVE_INFINITY
      const secondOrder = scopeOrder.get(second) ?? Number.POSITIVE_INFINITY
      if (firstOrder !== secondOrder) return firstOrder - secondOrder
      return first.localeCompare(second, 'zh-CN')
    })
    .map((category) => ({
      category,
      items: groups.get(category) ?? [],
    }))
}
