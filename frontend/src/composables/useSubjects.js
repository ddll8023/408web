/**
 * 科目数据 Composable
 * 抽取科目加载的公共逻辑
 */
import { ref } from 'vue'
import { getEnabledSubjects } from '@/api/subject'

/**
 * 科目数据管理
 * @returns {Object} 科目相关状态和方法
 */
export function useSubjects() {
  // 科目选项
  const subjectOptions = ref([])

  // 科目ID到名称的映射
  const subjectMap = ref({})

  /**
   * 加载科目选项
   */
  const loadSubjectOptions = async () => {
    try {
      const res = await getEnabledSubjects()
      if (res.code === 200) {
        subjectOptions.value = res.data || []
        // 构建ID到名称的映射
        const map = {}
        subjectOptions.value.forEach(subject => {
          map[subject.id] = subject.name
        })
        subjectMap.value = map
      }
    } catch (error) {
      console.error('加载科目列表失败:', error)
    }
  }

  /**
   * 根据科目ID获取科目名称
   * @param {Number} subjectId 科目ID
   * @returns {String} 科目名称
   */
  const getSubjectName = (subjectId) => {
    return subjectMap.value[subjectId] || ''
  }

  return {
    subjectOptions,
    subjectMap,
    loadSubjectOptions,
    getSubjectName
  }
}
