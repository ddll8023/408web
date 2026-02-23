<template>
  <!-- 复制下拉菜单 -->
  <Dropdown trigger="click" @command="(command) => $emit('copy', command)">
    <template #trigger>
      <CustomButton size="sm" type="text" :icon="['fas', 'copy']">复制</CustomButton>
    </template>

    <template #dropdown>
      <!-- Markdown 格式 -->
      <DropdownItem disabled>
        <font-awesome-icon :icon="['fas', 'file-lines']" class="mr-1" />
        Markdown 格式
      </DropdownItem>
      <DropdownItem command="md-question">复制题目 (MD)</DropdownItem>
      <DropdownItem
        v-if="question.questionType === 'CHOICE' && question.options"
        command="md-options"
      >复制选项 (MD)</DropdownItem>
      <DropdownItem v-if="question.answer" command="md-answer">复制答案 (MD)</DropdownItem>
      <DropdownItem
        v-if="question.answer || (question.questionType === 'CHOICE' && question.options)"
        command="md-all"
      >复制完整内容 (MD)</DropdownItem>

      <!-- 纯文本格式 -->
      <DropdownItem disabled divided>
        <font-awesome-icon :icon="['fas', 'ticket']" class="mr-1" />
        纯文本格式
      </DropdownItem>
      <DropdownItem command="text-question">复制题目 (Text)</DropdownItem>
      <DropdownItem
        v-if="question.questionType === 'CHOICE' && question.options"
        command="text-options"
      >复制选项 (Text)</DropdownItem>
      <DropdownItem v-if="question.answer" command="text-answer">复制答案 (Text)</DropdownItem>
      <DropdownItem
        v-if="question.answer || (question.questionType === 'CHOICE' && question.options)"
        command="text-all"
      >复制完整内容 (Text)</DropdownItem>
    </template>
  </Dropdown>
</template>

<script setup>
/**
 * 公共复制菜单组件
 * 统一管理题目复制功能，支持 Markdown 和纯文本格式
 * 适用于真题(exam)和模拟题(mock)
 */
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'

defineProps({
  // 题目对象（真题或模拟题）
  question: {
    type: Object,
    required: true
  }
})

defineEmits(['copy'])
</script>
