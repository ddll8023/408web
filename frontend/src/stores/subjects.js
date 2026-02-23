/**
 * 科目数据全局 Store
 * 预加载并缓存科目数据，避免重复请求
 */
import { ref } from 'vue'
import { getEnabledSubjects } from '@/api/subject'

// 全局状态
const subjectOptions = ref([])
const subjectMap = ref({})
const loaded = ref(false)
const loading = ref(false)

/**
 * 加载科目数据（全局缓存一次）
 */
export function useSubjectsStore() {
  /**
   * 加载科目选项（带缓存）
   */
  const loadSubjectOptions = async () => {
    // 如果已经加载过，直接返回缓存数据
    if (loaded.value && subjectOptions.value.length > 0) {
      return
    }

    // 如果正在加载，等待加载完成
    if (loading.value) {
      // 等待一小段时间后重试
      await new Promise(resolve => setTimeout(resolve, 100))
      return loadSubjectOptions()
    }

    loading.value = true
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
        loaded.value = true
      }
    } catch (error) {
      console.error('加载科目列表失败:', error)
    } finally {
      loading.value = false
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

  /**
   * 重置缓存（用于退出登录等场景）
   */
  const resetCache = () => {
    subjectOptions.value = []
    subjectMap.value = {}
    loaded.value = false
  }

  return {
    subjectOptions,
    subjectMap,
    loaded,
    loadSubjectOptions,
    getSubjectName,
    resetCache
  }
}
