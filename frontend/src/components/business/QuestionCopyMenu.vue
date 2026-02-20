<template>
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
        <el-dropdown-item v-if="question.questionType === 'CHOICE' && question.options" command="md-options">复制选项 (MD)</el-dropdown-item>
        <el-dropdown-item v-if="question.answer" command="md-answer">复制答案 (MD)</el-dropdown-item>
        <el-dropdown-item v-if="question.answer || (question.questionType === 'CHOICE' && question.options)" command="md-all">复制完整内容 (MD)</el-dropdown-item>
        <el-dropdown-item disabled divided class="dropdown-group-title">
          <el-icon><Tickets /></el-icon>
          纯文本格式
        </el-dropdown-item>
        <el-dropdown-item command="text-question">复制题目 (Text)</el-dropdown-item>
        <el-dropdown-item v-if="question.questionType === 'CHOICE' && question.options" command="text-options">复制选项 (Text)</el-dropdown-item>
        <el-dropdown-item v-if="question.answer" command="text-answer">复制答案 (Text)</el-dropdown-item>
        <el-dropdown-item v-if="question.answer || (question.questionType === 'CHOICE' && question.options)" command="text-all">复制完整内容 (Text)</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
/**
 * 公共复制菜单组件
 * 统一管理题目复制功能，支持 Markdown 和纯文本格式
 * 适用于真题(exam)和模拟题(mock)
 */
import { DocumentCopy, Document, Tickets } from '@element-plus/icons-vue'
import CustomButton from '@/components/basic/CustomButton.vue'

defineProps({
  // 题目对象（真题或模拟题）
  question: {
    type: Object,
    required: true
  }
})

defineEmits(['copy'])
</script>

<style scoped>
/* 复制菜单样式 - 与原 ExamItemHeader/MockItemHeader 保持一致 */
.dropdown-group-title {
  font-size: 12px;
  color: #999;
  cursor: default;
}

.dropdown-group-title .el-icon {
  margin-right: 4px;
}
</style>
