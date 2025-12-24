<template>
  <div class="exam-item-header">
    <div class="question-info">
      <h3 class="question-title">
        <span class="question-number">{{ exam.year }}年 第 {{ exam.questionNumber }} 题</span>
      </h3>
      <div class="question-meta">
        <el-tag size="small" :type="exam.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ exam.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </el-tag>
        <el-tag 
          v-for="cat in (Array.isArray(exam.category) ? exam.category : [])" 
          :key="cat" 
          size="small" 
          type="info"
        >
          {{ cat }}
        </el-tag>
      </div>
    </div>
    <div class="question-actions">
      <el-dropdown trigger="click" @command="(command) => $emit('copy', command)">
        <CustomButton
          size="small"
          type="text"
          :icon="DocumentCopy"
        >
          复制
        </CustomButton>
        <template #dropdown>
          <el-dropdown-menu>
            <!-- Markdown 格式复制 -->
            <el-dropdown-item disabled class="dropdown-group-title">
              <el-icon><Document /></el-icon>
              Markdown 格式
            </el-dropdown-item>
            <el-dropdown-item command="md-question">
              复制题目 (MD)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.questionType === 'CHOICE' && exam.options"
              command="md-options"
            >
              复制选项 (MD)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.answer"
              command="md-answer"
            >
              复制答案 (MD)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.answer || (exam.questionType === 'CHOICE' && exam.options)"
              command="md-all"
            >
              复制完整内容 (MD)
            </el-dropdown-item>
            
            <!-- 纯文本格式复制 -->
            <el-dropdown-item disabled divided class="dropdown-group-title">
              <el-icon><Tickets /></el-icon>
              纯文本格式
            </el-dropdown-item>
            <el-dropdown-item command="text-question">
              复制题目 (Text)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.questionType === 'CHOICE' && exam.options"
              command="text-options"
            >
              复制选项 (Text)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.answer"
              command="text-answer"
            >
              复制答案 (Text)
            </el-dropdown-item>
            <el-dropdown-item
              v-if="exam.answer || (exam.questionType === 'CHOICE' && exam.options)"
              command="text-all"
            >
              复制完整内容 (Text)
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <template v-if="isAdmin">
        <CustomButton
          size="small"
          type="text"
          @click="$emit('edit', exam)"
        >
          编辑
        </CustomButton>
        <CustomButton
          size="small"
          type="text"
          @click="$emit('delete', exam.id)"
        >
          删除
        </CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup>
import { DocumentCopy, Document, Tickets } from '@element-plus/icons-vue'
import CustomButton from '@/components/basic/CustomButton.vue'

defineProps({
  exam: {
    type: Object,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

defineEmits(['copy', 'edit', 'delete'])
</script>

<style lang="scss" scoped>
.exam-item-header {
  @include flex-between;
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03); // 极淡的分隔线
  
  .question-info {
    flex: 1;
    
    .question-title {
      margin: 0 0 8px 0;
      font-size: 18px; // 稍微加大标题
      color: $color-text-primary;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 12px;
      
      .question-number {
        color: $color-accent; // 使用强调色
        font-family: 'Roboto Mono', monospace; // 数字使用等宽字体（如果支持）
      }

      .question-subtitle {
        margin-left: 12px;
        font-size: 16px;
        font-weight: normal;
        color: $color-text-secondary;
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
