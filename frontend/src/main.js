/**
 * Vue应用入口文件
 * 集成Font Awesome、Router、Pinia、全局样式
 * 遵循KISS原则：简单的初始化逻辑
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
// 导入常用图标
import {
  faCaretRight,
  faPlus,
  faTrash,
  faEdit,
  faSearch,
  faUser,
  faHouse,
  faArrowRight,
  faArrowLeft,
  faArrowUp,
  faSpinner,
  faCheck,
  faTimes,
  faChevronDown,
  faChevronUp,
  faChevronRight,
  faCopy,
  faClipboard,
  faDownload,
  faUpload,
  faFolder,
  faFolderOpen,
  faBook,
  faCode,
  faClock,
  faTag,
  faList,
  faListOl,
  faBars,
  faEllipsisVertical,
  faStar,
  faPencil,
  faEye,
  faEyeSlash,
  faLock,
  faLockOpen,
  faSignOutAlt,
  faCog,
  faBell,
  faInfoCircle,
  faExclamationTriangle,
  faQuestionCircle,
  faAngleRight,
  faAngleLeft,
  faAngleUp,
  faAngleDown,
  faTimesCircle,
  faCheckCircle,
  faPlusCircle,
  faMinusCircle,
  faTrashAlt,
  faSave,
  faSync,
  faBolt,
  faFire,
  faGraduationCap,
  faSchool,
  faUniversity,
  faLaptopCode,
  faNetworkWired,
  faServer,
  faDatabase,
  faMemory,
  faFile,
  faFileLines,
  faTicket,
  faMagnifyingGlass,
  faCompress,
  faTriangleExclamation
} from '@fortawesome/free-solid-svg-icons'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'katex/dist/katex.min.css'
import App from './App.vue'
import router from './router'

// 导入全局样式（包含全局重置和通用样式）
import '@/styles/tailwind.css'

// 添加图标到库
library.add(
  faCaretRight,
  faPlus,
  faTrash,
  faEdit,
  faSearch,
  faUser,
  faHouse,
  faArrowRight,
  faArrowLeft,
  faArrowUp,
  faSpinner,
  faCheck,
  faTimes,
  faChevronDown,
  faChevronUp,
  faChevronRight,
  faCopy,
  faClipboard,
  faDownload,
  faUpload,
  faFolder,
  faFolderOpen,
  faBook,
  faCode,
  faClock,
  faTag,
  faList,
  faListOl,
  faBars,
  faEllipsisVertical,
  faStar,
  faPencil,
  faEye,
  faEyeSlash,
  faLock,
  faLockOpen,
  faSignOutAlt,
  faCog,
  faBell,
  faInfoCircle,
  faExclamationTriangle,
  faQuestionCircle,
  faAngleRight,
  faAngleLeft,
  faAngleUp,
  faAngleDown,
  faTimesCircle,
  faCheckCircle,
  faPlusCircle,
  faMinusCircle,
  faTrashAlt,
  faSave,
  faSync,
  faBolt,
  faFire,
  faGraduationCap,
  faSchool,
  faUniversity,
  faLaptopCode,
  faNetworkWired,
  faServer,
  faDatabase,
  faMemory,
  faFile,
  faFileLines,
  faTicket,
  faMagnifyingGlass,
  faCompress,
  faTriangleExclamation
)

// 创建Vue应用实例
const app = createApp(App)

// 创建Pinia实例
const pinia = createPinia()

// 注册插件
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 全局注册 FontAwesomeIcon 组件
app.component('font-awesome-icon', FontAwesomeIcon)

// 预加载全局数据（在应用挂载后立即开始加载，不阻塞渲染）
import { useSubjectsStore } from './stores/subjects'
app.mount('#app')

// 异步预加载科目数据（不影响首屏渲染）
useSubjectsStore().loadSubjectOptions()
