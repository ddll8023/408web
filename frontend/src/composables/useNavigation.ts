/**
 * 全局导航的共享状态与动作。
 * 桌面导航和窄屏导航只负责呈现，搜索、跳转、退出和管理入口逻辑集中在这里。
 */
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

export type SearchType = 'exam' | 'mock' | 'adaptation'

export interface SearchTypeOption {
  label: string
  value: SearchType
}

export const searchTypeOptions = [
  { label: '真题', value: 'exam' },
  { label: '模拟题', value: 'mock' },
  { label: '改编题', value: 'adaptation' },
] satisfies SearchTypeOption[]

export const manageItems = [
  { command: 'subject', label: '科目管理' },
  { command: 'category', label: '分类标签管理' },
  { command: 'exam', label: '真题管理' },
  { command: 'mock', label: '模拟题管理' },
  { command: 'adaptation', label: '改编题管理' },
  { command: 'compose', label: '出题工作台' },
  { command: 'image', label: '图片管理' },
  { command: 'exam-category', label: '分类统计' },
] as const

export type ManageCommand = typeof manageItems[number]['command']
export type ManageItem = typeof manageItems[number]

const manageRouteMap: Record<ManageCommand, string> = {
  subject: '/manage/subject',
  category: '/manage/category',
  exam: '/manage/exam',
  mock: '/manage/mock',
  adaptation: '/manage/adaptation',
  compose: '/manage/compose',
  image: '/manage/image',
  'exam-category': '/manage/exam-category',
}

export function useNavigation() {
  const router = useRouter()
  const route = useRoute()
  const authStore = useAuthStore()
  const { showToast } = useToast()

  const searchType = ref<SearchType>('exam')
  const searchKeyword = ref('')
  const mobileMenuOpen = ref(false)

  const closeMobileMenu = () => {
    mobileMenuOpen.value = false
  }

  const handleSearch = () => {
    const keyword = searchKeyword.value.trim()
    if (!keyword) {
      showToast('请输入搜索关键词', 'warning')
      return
    }

    const routeMap: Record<SearchType, string> = {
      exam: '/manage/exam',
      mock: '/manage/mock',
      adaptation: '/manage/adaptation',
    }

    closeMobileMenu()
    void router.push({ path: routeMap[searchType.value], query: { keyword } })
  }

  const goToLogin = () => {
    closeMobileMenu()
    void router.push('/login')
  }

  const goToRegister = () => {
    closeMobileMenu()
    void router.push('/register')
  }

  const goToUserCenter = () => {
    closeMobileMenu()
    void router.push('/user/center')
  }

  const handleManageCommand = (command: string | number) => {
    if (typeof command !== 'string' || !Object.prototype.hasOwnProperty.call(manageRouteMap, command)) return

    closeMobileMenu()
    void router.push(manageRouteMap[command as ManageCommand])
  }

  const handleLogout = () => {
    authStore.clearAuth()
    closeMobileMenu()
    showToast('已退出登录', 'success')
    void router.push('/exam')
  }

  watch(() => route.fullPath, closeMobileMenu)

  return {
    authStore,
    searchTypeOptions,
    manageItems,
    searchType,
    searchKeyword,
    mobileMenuOpen,
    handleSearch,
    goToLogin,
    goToRegister,
    goToUserCenter,
    handleManageCommand,
    handleLogout,
  }
}
