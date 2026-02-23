<template>
  <div class="min-h-screen bg-[#FBF7F2] flex items-center justify-center p-4">
    <!-- 使用 CustomCard 替代 el-card -->
    <CustomCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h2 class="text-xl font-semibold text-[#333] mb-2">用户登录</h2>
          <span class="text-[#666] text-sm">408真题网站</span>
        </div>
      </template>

      <!-- 使用原生 form + 自定义验证 -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <!-- 用户名：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="用户名" required />
          <CustomInput
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :error="errors.username"
            @blur="validateField('username')"
          />
        </div>

        <!-- 密码：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="密码" required />
          <CustomInput
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :error="errors.password"
            @blur="validateField('password')"
            @enter="handleLogin"
          />
        </div>

        <!-- 登录按钮 -->
        <CustomButton
          type="primary"
          :loading="loading"
          class="w-full"
          @click="handleLogin"
        >
          登录
        </CustomButton>

        <!-- 注册链接 -->
        <div class="text-center">
          <CustomButton type="text" @click="goToRegister">
            还没有账号？立即注册
          </CustomButton>
        </div>
      </form>
    </CustomCard>
  </div>
</template>

<script setup>
/**
 * 用户登录页面
 * 功能：处理用户登录认证，包含表单验证、错误处理、Token存储
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import FormLabel from '@/components/basic/FormLabel.vue'

const router = useRouter()
const authStore = useAuthStore()
const { showToast } = useToast()

// 加载状态
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单错误信息
const errors = reactive({
  username: '',
  password: ''
})

/**
 * 验证单个字段
 * @param {string} field - 字段名
 */
const validateField = (field) => {
  if (field === 'username') {
    errors.username = loginForm.username.trim() ? '' : '请输入用户名'
  } else if (field === 'password') {
    errors.password = loginForm.password.trim() ? '' : '请输入密码'
  }
}

/**
 * 验证整个表单
 * @returns {boolean} 表单是否有效
 */
const validateForm = () => {
  let valid = true
  errors.username = ''
  errors.password = ''

  if (!loginForm.username.trim()) {
    errors.username = '请输入用户名'
    valid = false
  }
  if (!loginForm.password.trim()) {
    errors.password = '请输入密码'
    valid = false
  }

  return valid
}

/**
 * 处理登录
 */
const handleLogin = async () => {
  // 验证表单
  if (!validateForm()) return

  loading.value = true
  try {
    // 调用登录API
    const response = await login(loginForm)

    // 保存Token和用户信息
    authStore.setToken(response.data.token)
    authStore.setUserInfo({
      username: response.data.username,
      role: response.data.role
    })

    showToast('登录成功', 'success')

    // 跳转到首页
    router.push('/')
  } catch (error) {
    console.error('登录失败：', error)
    // 展示后端返回的错误信息，便于定位问题
    showToast(error?.response?.data?.message || error?.message || '登录失败', 'error')
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到注册页
 */
const goToRegister = () => {
  router.push('/register')
}
</script>
