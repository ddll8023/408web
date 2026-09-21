/**
 * 分类树查询与分组工具：按分类树顺序把题目分组，并为内容区生成跳转锚点。
 */
import type { AdaptationQuestion, CategoryTreeNode, ExamQuestion, MockQuestion } from '@/types'

/** 分类分组后的题目集合。 */
export interface ExamQuestionGroup {
  category: string
  categoryId?: number
  depth: number
  items: ExamQuestion[]
}

export interface MockQuestionGroup {
  category: string
  categoryId?: number
  depth: number
  items: MockQuestion[]
}

export interface AdaptationQuestionGroup {
  category: string
  categoryId?: number
  depth: number
  items: AdaptationQuestion[]
}

/** 为内容分组生成稳定的 DOM 锚点；未归档历史分类使用编码后的名称兜底。 */
export const getCategorySectionId = (
  kind: 'exam' | 'mock' | 'adaptation',
  categoryId: number | undefined,
  categoryName: string,
) => `${kind}-category-${categoryId ?? encodeURIComponent(categoryName)}`

interface CategoryOrderEntry {
  name: string
  categoryId?: number
  order: number
  depth: number
}

interface CategorizedQuestion {
  id: number
  category?: string[] | null
}

interface CategoryQuestionGroup<T extends CategorizedQuestion> {
  category: string
  categoryId?: number
  depth: number
  items: T[]
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

const uniqueQuestionsById = <T extends CategorizedQuestion>(
  questions: readonly T[],
): T[] => {
  const uniqueById = new Map<number, T>()
  questions.forEach((question) => {
    if (!uniqueById.has(question.id)) {
      uniqueById.set(question.id, question)
    }
  })
  return Array.from(uniqueById.values())
}

/** 按题目 ID 去重，并保持真题分类页的年份/题号顺序。 */
export const uniqueExamQuestions = (questions: readonly ExamQuestion[]) => {
  return uniqueQuestionsById(questions).sort(compareQuestions)
}

const flattenCategoryTree = (
  categories: readonly CategoryTreeNode[],
): CategoryOrderEntry[] => {
  const result: CategoryOrderEntry[] = []

  const visit = (category: CategoryTreeNode, depth: number) => {
    result.push({
      name: category.name,
      categoryId: category.id,
      order: result.length,
      depth,
    })
    category.children.forEach((child) => visit(child, depth + 1))
  }

  categories.forEach((category) => visit(category, 0))
  return result
}

export const findCategoryNode = (
  categories: readonly CategoryTreeNode[],
  categoryName: string,
): CategoryTreeNode | undefined => {
  for (const category of categories) {
    if (category.name === categoryName) return category
    const child = findCategoryNode(category.children, categoryName)
    if (child) return child
  }
  return undefined
}

/**
 * 查找分类名称对应的节点路径（根 → 目标），用于自动展开侧栏中的祖先分类。
 * 名称未命中时返回空数组，调用方不应据此改写展开状态。
 */
export const findCategoryPath = (
  categories: readonly CategoryTreeNode[],
  categoryName: string,
): CategoryTreeNode[] => {
  for (const category of categories) {
    if (category.name === categoryName) return [category]
    const childPath = findCategoryPath(category.children, categoryName)
    if (childPath.length > 0) return [category, ...childPath]
  }
  return []
}

const getSelectedScope = (
  categories: readonly CategoryTreeNode[],
  selectedCategory: string,
): { entries: CategoryOrderEntry[]; found: boolean } => {
  const selected = findCategoryNode(categories, selectedCategory)
  if (!selected) {
    return {
      entries: [{ name: selectedCategory, order: 0, depth: 0 }],
      found: false,
    }
  }

  const entries: CategoryOrderEntry[] = []
  const visit = (category: CategoryTreeNode, depth: number) => {
    entries.push({
      name: category.name,
      categoryId: category.id,
      order: entries.length,
      depth,
    })
    category.children.forEach((child) => visit(child, depth + 1))
  }
  visit(selected, 0)
  return { entries, found: true }
}

/**
 * 按分类树分组题目。
 *
 * 一个题目可能同时带有多个分类标签。分组时按左侧分类树的显示顺序
 * 选择最后一个匹配标签，因此同一题目只会出现在最靠后的子标签中。
 * 仅属于父分类的题目会落在父分类组，并按树的先序顺序排在子分类之前。
 */
const groupQuestionsByCategory = <T extends CategorizedQuestion>(
  questions: readonly T[],
  categories: readonly CategoryTreeNode[],
  selectedCategory = '',
): CategoryQuestionGroup<T>[] => {
  if (questions.length === 0) return []

  const normalizedSelectedCategory = selectedCategory.trim()
  const allEntries = flattenCategoryTree(categories)
  const selectedScope = normalizedSelectedCategory
    ? getSelectedScope(categories, normalizedSelectedCategory)
    : { entries: allEntries, found: true }
  const scopeEntries = selectedScope.entries
  const scopeOrder = new Map(scopeEntries.map((entry) => [entry.name, entry.order]))
  const scopeEntriesByName = new Map(scopeEntries.map((entry) => [entry.name, entry]))
  const groups = new Map<string, T[]>()

  questions.forEach((question) => {
    const rawCategories = Array.isArray(question.category)
      ? question.category.filter((category) => category.length > 0)
      : []
    const questionCategories = new Set(rawCategories)
    const matchedCategories = scopeEntries.filter((entry) => questionCategories.has(entry.name))

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
      group.push(question)
    } else {
      groups.set(displayCategory, [question])
    }
  })

  return Array.from(groups.keys())
    .sort((first, second) => {
      const firstOrder = scopeOrder.get(first) ?? Number.POSITIVE_INFINITY
      const secondOrder = scopeOrder.get(second) ?? Number.POSITIVE_INFINITY
      if (firstOrder !== secondOrder) return firstOrder - secondOrder
      return first.localeCompare(second, 'zh-CN')
    })
    .map((category) => {
      const entry = scopeEntriesByName.get(category)
      return {
        category,
        categoryId: entry?.categoryId,
        depth: entry?.depth ?? 0,
        items: groups.get(category) ?? [],
      }
    })
}

export const groupExamQuestionsByCategory = (
  questions: readonly ExamQuestion[],
  categories: readonly CategoryTreeNode[],
  selectedCategory = '',
): ExamQuestionGroup[] => {
  return groupQuestionsByCategory(
    uniqueExamQuestions(questions),
    categories,
    selectedCategory,
  )
}

/** 按分类树顺序分组模拟题，并确保一题只展示一次。 */
export const groupMockQuestionsByCategory = (
  questions: readonly MockQuestion[],
  categories: readonly CategoryTreeNode[],
  selectedCategory = '',
): MockQuestionGroup[] => {
  return groupQuestionsByCategory(
    uniqueQuestionsById(questions),
    categories,
    selectedCategory,
  )
}

/** 按题目 ID 去重改编题，保持接口返回顺序。 */
export const uniqueAdaptationQuestions = (questions: readonly AdaptationQuestion[]) => {
  return uniqueQuestionsById(questions)
}

/** 按分类树顺序分组改编题，并确保一题只展示一次。 */
export const groupAdaptationQuestionsByCategory = (
  questions: readonly AdaptationQuestion[],
  categories: readonly CategoryTreeNode[],
  selectedCategory = '',
): AdaptationQuestionGroup[] => {
  return groupQuestionsByCategory(
    uniqueQuestionsById(questions),
    categories,
    selectedCategory,
  )
}
