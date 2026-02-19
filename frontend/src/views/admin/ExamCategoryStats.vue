<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <el-card class="shadow-sm">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">真题分类统计</h2>
          <el-dropdown trigger="click" @command="handleExportCommand">
            <CustomButton type="success">
              <el-icon style="margin-right: 6px"><Download /></el-icon>
              导出统计
            </CustomButton>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="markdown-no-answer">导出为 Markdown（不含答案）</el-dropdown-item>
                <el-dropdown-item command="markdown-with-answer">导出为 Markdown（含答案）</el-dropdown-item>
                <el-dropdown-item command="xlsx">导出为 Excel 文件 (.xlsx)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="mb-6 p-4 bg-[#efefef] rounded flex items-center">
        <span class="font-bold text-[#666] mr-2">科目筛选:</span>
        <el-select
          v-model="statsSubjectId"
          placeholder="全部科目"
          clearable
          @change="loadStats"
          style="width: 200px"
        >
          <el-option
            v-for="subject in subjectOptions"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
        
        <CustomButton type="primary" @click="loadStats" style="margin-left: 16px">
          <el-icon style="margin-right: 6px"><Refresh /></el-icon>
          刷新数据
        </CustomButton>
      </div>

      <!-- 统计表格 -->
      <el-table :data="statsData" v-loading="statsLoading" border stripe style="width: 100%">
        <el-table-column prop="subjectName" label="科目" width="180" sortable />
        <el-table-column prop="category" label="分类" min-width="200" sortable />
        <el-table-column prop="choiceCount" label="选择题数量" width="130" sortable />
        <el-table-column prop="subjectiveCount" label="主观题数量" width="130" sortable />
        <el-table-column prop="count" label="总题数" width="120" sortable />
        <el-table-column label="题目分布" min-width="360">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
              <el-tag
                v-for="q in row.questions"
                :key="q"
                size="small"
                type="info"
                class="mr-1 mb-1"
              >
                {{ q }}
              </el-tag>
              <span v-if="!row.questions || row.questions.length === 0" class="text-xs text-[#999]">
                暂无数据
              </span>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="mt-6 pt-4 border-t border-[#dfe2e5] text-right text-lg text-[#333]">
        <strong>总计题目：{{ totalQuestions }}</strong>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import { getExamCategoryStats } from '@/api/exam'
import { getEnabledSubjects } from '@/api/subject'
import CustomButton from '@/components/basic/CustomButton.vue'

// State
const statsLoading = ref(false)
const statsData = ref([])
const statsSubjectId = ref(null)
const subjectOptions = ref([])

/**
 * 加载科目选项
 */
const loadSubjectOptions = async () => {
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjectOptions.value = res.data || []
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
  }
}

/**
 * 加载统计数据
 */
const loadStats = async () => {
  statsLoading.value = true
  try {
    const res = await getExamCategoryStats(statsSubjectId.value || undefined)
    if (res.code === 200) {
      statsData.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

/**
 * 计算总题数
 */
const totalQuestions = computed(() => {
  return statsData.value.reduce((sum, item) => sum + (item.count || 0), 0)
})

// getPercentage 已移除，改用题目分布标签展示

const handleExportCommand = (command) => {
  switch (command) {
    case 'markdown-no-answer':
      exportStats('markdown', false)
      break
    case 'markdown-with-answer':
      exportStats('markdown', true)
      break
    case 'xlsx':
      exportStats('xlsx', false)
      break
    default:
      ElMessage.warning('不支持的导出格式')
  }
}

const exportStats = (format, includeAnswer = false) => {
  if (!statsData.value || statsData.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  const subjectId = statsSubjectId.value

  let subjectName = '全部科目'
  if (subjectId !== null && subjectId !== undefined) {
    const found = subjectOptions.value.find((s) => s.id === subjectId)
    subjectName = (found && found.name) ? found.name : `科目${subjectId}`
  }

  let url = `/api/exam/category-stats/export?format=${format}&includeAnswer=${includeAnswer}`
  if (subjectId !== null && subjectId !== undefined) {
    url += `&subjectId=${subjectId}`
  }

  const link = document.createElement('a')
  link.href = url
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const dateStr = `${year}${month}${day}`

  let ext = 'md'
  if (format === 'docx') {
    ext = 'docx'
  } else if (format === 'xlsx') {
    ext = 'xlsx'
  }

  link.download = `真题分类统计_${subjectName}_${dateStr}.${ext}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success('导出已开始')
}

onMounted(() => {
  loadSubjectOptions()
  loadStats()
})
</script>

<style scoped>
/**
 * 真题分类统计页面样式
 * 已迁移至 Tailwind CSS
 */
</style>
