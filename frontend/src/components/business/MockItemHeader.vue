<template>
  <!-- 模拟题头部组件：显示标题、题号、元数据、操作按钮 -->
  <div class="mock-item-header">
    <div class="question-info">
      <h3 v-if="mock.questionNumber || mock.title" class="question-title">
        <span v-if="mock.title">{{ mock.title }}</span>
        <span v-if="mock.questionNumber && mock.title" class="title-separator">·</span>
        <span v-if="mock.questionNumber" class="question-number">第{{ mock.questionNumber }}题</span>
      </h3>
      <div class="question-meta">
        <el-tag size="small" :type="mock.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ mock.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </el-tag>
        <el-tag v-if="mock.difficulty" size="small" :type="getDifficultyType(mock.difficulty)">
          {{ getDifficultyLabel(mock.difficulty) }}
        </el-tag>
        <el-tag 
          v-for="cat in (Array.isArray(mock.category) ? mock.category : [])" 
          :key="cat" 
          size="small" 
          type="info"
        >
          {{ cat }}
        </el-tag>
      </div>
    </div>
    <div class="question-actions">
      <!-- 复制下拉菜单 -->
      <el-dropdown trigger="click" @command="(command) => $emit('copy', command)">
        <CustomButton size="small" type="text" :icon="DocumentCopy">复制</CustomButton>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled class="dropdown-group-title">
              <el-icon><Document /></el-icon>
              Markdown 格式
            </el-dropdown-item>
            <el-dropdown-item command="md-question">复制题目 (MD)</el-dropdown-item>
            <el-dropdown-item v-if="mock.questionType === 'CHOICE' && mock.options" command="md-options">
              复制选项 (MD)
            </el-dropdown-item>
            <el-dropdown-item v-if="mock.answer" command="md-answer">复制答案 (MD)</el-dropdown-item>
            <el-dropdown-item v-if="mock.answer || (mock.questionType === 'CHOICE' && mock.options)" command="md-all">
              复制完整内容 (MD)
            </el-dropdown-item>
            <el-dropdown-item disabled divided class="dropdown-group-title">
              <el-icon><Tickets /></el-icon>
              纯文本格式
            </el-dropdown-item>
            <el-dropdown-item command="text-question">复制题目 (Text)</el-dropdown-item>
            <el-dropdown-item v-if="mock.questionType === 'CHOICE' && mock.options" command="text-options">
              复制选项 (Text)
            </el-dropdown-item>
            <el-dropdown-item v-if="mock.answer" command="text-answer">复制答案 (Text)</el-dropdown-item>
            <el-dropdown-item v-if="mock.answer || (mock.questionType === 'CHOICE' && mock.options)" command="text-all">
              复制完整内容 (Text)
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <!-- 管理员操作 -->
      <template v-if="isAdmin">
        <CustomButton size="small" type="text" @click="$emit('edit', mock)">编辑</CustomButton>
        <CustomButton size="small" type="text" @click="$emit('delete', mock.id)">删除</CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup>
/**
 * 模拟题头部组件
 * 与 ExamItemHeader 保持样式一致，但标题格式适配模拟题
 * 格式: {title} · 第{questionNumber}题
 */
import { DocumentCopy, Document, Tickets } from '@element-plus/icons-vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'

defineProps({
  mock: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false }
})

defineEmits(['copy', 'edit', 'delete'])
</script>

<style lang="scss" scoped>
// 样式与 ExamItemHeader 保持一致
.mock-item-header {
  @include flex-between;
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  
  .question-info {
    flex: 1;
    
    .question-title {
      margin: 0 0 8px 0;
      font-size: 18px;
      color: $color-text-primary;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      
      .title-separator {
        color: $color-text-secondary;
        font-weight: normal;
      }
      
      .question-number {
        color: $color-accent;
        font-family: 'Roboto Mono', monospace;
      }
    }
    
    .question-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
  
  .question-actions {
    display: flex;
    gap: 4px;
    opacity: 0.8;
    transition: opacity 0.2s;
    flex-shrink: 0;
    
    &:hover {
      opacity: 1;
    }
  }

  @include mobile {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-xs;
    
    .question-title {
      font-size: $font-size-base;
    }
    
    .question-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
}
</style>
