<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>用户登录</h2>
          <span>408真题网站</span>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item>
          <CustomButton
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </CustomButton>
        </el-form-item>

        <el-form-item>
          <CustomButton
            type="text"
            @click="goToRegister"
          >
            还没有账号？立即注册
          </CustomButton>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref(null)

// 加载状态
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

/**
 * 处理登录
 */
const handleLogin = async () => {
  // 验证表单
  const valid = await loginFormRef.value.validate()
  if (!valid) return

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

    ElMessage.success('登录成功')
    
    // 跳转到首页
    router.push('/')
  } catch (error) {
    console.error('登录失败：', error)
    // 展示后端返回的错误信息，便于定位问题
    ElMessage.error(error?.response?.data?.message || error?.message || '登录失败')
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

<style scoped>
/**
 * 登录页面样式
 * 使用 Tailwind CSS
 * 注：变量和mixins已通过Vite全局注入，无需手动导入
 */

.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #FBF7F2; /* $color-primary */
}

.login-card {
  width: 450px; /* $container-width-sm */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* $box-shadow-base */
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0; /* $spacing-xs */
  color: #333; /* $color-text-primary */
  font-weight: 600; /* $font-weight-bold */
}

.card-header span {
  color: #666; /* $color-text-secondary */
  font-size: 14px; /* $font-size-base */
}
</style>

