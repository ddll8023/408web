/**
 * 科目数据 Composable
 * 抽取科目加载的公共逻辑
 * 使用全局 store 缓存数据，避免重复请求
 */
import { ref } from 'vue'
import { getEnabledSubjects } from '@/api/subject'
import { useSubjectsStore } from '@/stores/subjects'

// 创建全局 store 实例（单例）
const subjectsStore = useSubjectsStore()

/**
 * 科目数据管理
 * @returns {Object} 科目相关状态和方法
 */
export function useSubjects() {
  // 直接使用全局 store 的状态
  const subjectOptions = subjectsStore.subjectOptions
  const subjectMap = subjectsStore.subjectMap

  /**
   * 加载科目选项（带全局缓存）
   */
  const loadSubjectOptions = async () => {
    await subjectsStore.loadSubjectOptions()
  }

  /**
   * 根据科目ID获取科目名称
   * @param {Number} subjectId 科目ID
   * @returns {String} 科目名称
   */
  const getSubjectName = (subjectId) => {
    return subjectsStore.getSubjectName(subjectId)
  }

  return {
    subjectOptions,
    subjectMap,
    loadSubjectOptions,
    getSubjectName
  }
}
