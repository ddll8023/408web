<template>
  <div class="min-h-screen bg-[#FBF7F2] flex items-center justify-center p-4">
    <!-- 使用 CustomCard 替代 el-card -->
    <CustomCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h2 class="text-xl font-semibold text-[#333] mb-2">用户注册</h2>
          <span class="text-[#666] text-sm">408真题网站</span>
        </div>
      </template>

      <!-- 使用原生 form + 自定义验证 -->
      <form @submit.prevent="handleRegister" class="space-y-4">
        <!-- 用户名：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="用户名" required />
          <CustomInput
            v-model="registerForm.username"
            placeholder="请输入用户名（3-50字符）"
            :error="errors.username"
            @blur="validateField('username')"
          />
        </div>

        <!-- 密码：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="密码" required />
          <CustomInput
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（6-20字符）"
            :error="errors.password"
            @blur="validateField('password')"
          />
        </div>

        <!-- 确认密码：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="确认密码" required />
          <CustomInput
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :error="errors.confirmPassword"
            @blur="validateField('confirmPassword')"
          />
        </div>

        <!-- 邮箱：使用 FormLabel + CustomInput -->
        <div>
          <FormLabel label="邮箱" />
          <CustomInput
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱（可选）"
            :error="errors.email"
            @blur="validateField('email')"
          />
        </div>

        <!-- 注册按钮 -->
        <CustomButton
          type="primary"
          :loading="loading"
          class="w-full"
          @click="handleRegister"
        >
          注册
        </CustomButton>

        <!-- 登录链接 -->
        <div class="text-center">
          <CustomButton type="text" @click="goToLogin">
            已有账号？立即登录
          </CustomButton>
        </div>
      </form>
    </CustomCard>
  </div>
</template>

<script setup>
/**
 * 用户注册页面
 * 功能：处理用户注册，包含表单验证、密码确认、错误处理
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import FormLabel from '@/components/basic/FormLabel.vue'

const router = useRouter()
const { showToast } = useToast()

// 加载状态
const loading = ref(false)

// 注册表单数据
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// 表单错误信息
const errors = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

/**
 * 验证单个字段
 * @param {string} field - 字段名
 */
const validateField = (field) => {
  if (field === 'username') {
    errors.username = registerForm.username.trim()
      ? (registerForm.username.length < 3 || registerForm.username.length > 50 ? '用户名长度在3-50字符之间' : '')
      : '请输入用户名'
  } else if (field === 'password') {
    errors.password = registerForm.password
      ? (registerForm.password.length < 6 || registerForm.password.length > 20 ? '密码长度在6-20字符之间' : '')
      : '请输入密码'
  } else if (field === 'confirmPassword') {
    errors.confirmPassword = registerForm.confirmPassword
      ? (registerForm.confirmPassword !== registerForm.password ? '两次输入的密码不一致' : '')
      : '请再次输入密码'
  } else if (field === 'email') {
    if (registerForm.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      errors.email = emailRegex.test(registerForm.email) ? '' : '请输入正确的邮箱格式'
    } else {
      errors.email = ''
    }
  }
}

/**
 * 验证整个表单
 * @returns {boolean} 表单是否有效
 */
const validateForm = () => {
  // 清空所有错误
  errors.username = ''
  errors.password = ''
  errors.confirmPassword = ''
  errors.email = ''

  let valid = true

  // 验证用户名
  if (!registerForm.username.trim()) {
    errors.username = '请输入用户名'
    valid = false
  } else if (registerForm.username.length < 3 || registerForm.username.length > 50) {
    errors.username = '用户名长度在3-50字符之间'
    valid = false
  }

  // 验证密码
  if (!registerForm.password) {
    errors.password = '请输入密码'
    valid = false
  } else if (registerForm.password.length < 6 || registerForm.password.length > 20) {
    errors.password = '密码长度在6-20字符之间'
    valid = false
  }

  // 验证确认密码
  if (!registerForm.confirmPassword) {
    errors.confirmPassword = '请再次输入密码'
    valid = false
  } else if (registerForm.confirmPassword !== registerForm.password) {
    errors.confirmPassword = '两次输入的密码不一致'
    valid = false
  }

  // 验证邮箱（可选，如果有值则验证格式）
  if (registerForm.email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(registerForm.email)) {
      errors.email = '请输入正确的邮箱格式'
      valid = false
    }
  }

  return valid
}

/**
 * 处理注册
 */
const handleRegister = async () => {
  // 验证表单
  if (!validateForm()) return

  loading.value = true
  try {
    // 调用注册API（不传递confirmPassword）
    await register({
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email || undefined
    })

    showToast('注册成功，请登录', 'success')

    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    console.error('注册失败：', error)
    // 展示后端返回的错误信息
    showToast(error?.response?.data?.message || error?.message || '注册失败，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到登录页
 */
const goToLogin = () => {
  router.push('/login')
}
</script>
