<template>
  <div class="mock-list-container">
    <el-card class="list-card" v-loading="loading">
      <!-- 顶部操作栏 -->
      <div class="list-header">
        <div class="header-left">
          <CustomButton type="text" :icon="ArrowLeft" @click="goBack">
            返回
          </CustomButton>
          <h2>{{ source }} - 模拟题</h2>
        </div>
        <div class="header-actions" v-if="isAdmin">
          <CustomButton type="primary" @click="handleCreate">
            创建模拟题
          </CustomButton>
        </div>
      </div>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form inline>
          <el-form-item label="科目">
            <el-select
              v-model="filters.subjectId"
              placeholder="全部科目"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="subject in subjectOptions"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="难度">
            <el-select
              v-model="filters.difficulty"
              placeholder="全部难度"
              clearable
              style="width: 120px"
            >
              <el-option label="简单" value="EASY" />
              <el-option label="中等" value="MEDIUM" />
              <el-option label="困难" value="HARD" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <CustomButton type="primary" @click="loadMockList">查询</CustomButton>
          </el-form-item>
        </el-form>
      </div>

      <!-- 题目列表 -->
      <div v-if="mockList.length > 0" class="mock-list">
        <ExamQuestionCard
          v-for="mock in mockList"
          :key="mock.id"
          :question="mock"
          :show-answer="showAnswers[mock.id]"
          density="compact"
          @toggle-answer="toggleAnswer(mock.id)"
        />
      </div>

      <!-- 空状态 -->
      <el-empty
        v-else-if="!loading"
        description="暂无模拟题数据"
        :image-size="200"
      />
    </el-card>
  </div>
</template>

<script setup>
/**
 * 模拟题列表页面
 * 功能：展示指定来源的所有模拟题
 * 遵循KISS原则：简单直观的列表展示
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getMockQuestionsBySource } from '@/api/mock'
import { getEnabledSubjects } from '@/api/subject'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 计算是否为管理员
const isAdmin = computed(() => authStore.isAdmin())

// 当前来源
const source = computed(() => decodeURIComponent(route.params.source || ''))

// 题目列表
const mockList = ref([])
const loading = ref(false)

// 答案显示状态
const showAnswers = ref({})

// 科目选项
const subjectOptions = ref([])

// 筛选条件
const filters = reactive({
  subjectId: null,
  difficulty: ''
})

/**
 * 返回上一页
 */
const goBack = () => {
  router.push('/mock')
}

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
 * 加载模拟题列表
 */
const loadMockList = async () => {
  if (!source.value) {
    ElMessage.error('来源参数缺失')
    return
  }

  loading.value = true
  showAnswers.value = {}
  
  try {
    const response = await getMockQuestionsBySource(source.value, {
      subjectId: filters.subjectId || undefined,
      difficulty: filters.difficulty || undefined
    })
    
    if (response.code === 200) {
      mockList.value = response.data || []
    } else {
      ElMessage.error(response.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载模拟题失败')
    console.error('加载模拟题失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 切换答案显示
 */
const toggleAnswer = (id) => {
  showAnswers.value[id] = !showAnswers.value[id]
}

/**
 * 创建模拟题
 */
const handleCreate = () => {
  router.push('/mock/create')
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadSubjectOptions()
  await loadMockList()
})
</script>

<style lang="scss" scoped>
.mock-list-container {
  min-height: calc(100vh - #{$nav-height});
  padding: $spacing-md;
  background-color: $color-primary;
}

.list-card {
  max-width: $container-width-lg;
  margin: 0 auto;
  box-shadow: $box-shadow-light;
}

.list-header {
  @include flex-between;
  margin-bottom: $spacing-md;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    
    h2 {
      margin: 0;
      font-size: $font-size-xl;
      color: $color-text-primary;
      font-weight: $font-weight-bold;
    }
  }
}

.filter-bar {
  margin-bottom: $spacing-md;
  padding: $spacing-sm;
  background-color: $color-bg-light;
  border-radius: $border-radius-base;
}

.mock-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

@include mobile {
  .mock-list-container {
    padding: $spacing-sm;
  }
  
  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-sm;
  }
  
  .filter-bar {
    :deep(.el-form) {
      display: block;
      
      .el-form-item {
        display: block;
        margin-bottom: $spacing-sm;
        
        .el-select {
          width: 100% !important;
        }
      }
    }
  }
}
</style>
