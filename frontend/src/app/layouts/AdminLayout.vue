<!-- 管理页面布局外壳：统一承载管理员页面，隔离管理端布局边界和业务页面内容。 -->
<template>
  <div class="admin-layout min-h-[var(--app-page-height)] overflow-x-clip">
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * 管理页面布局外壳。
 * 只提供管理端的页面边界，不承担具体表格、筛选、表单或权限业务。
 */
</script>
