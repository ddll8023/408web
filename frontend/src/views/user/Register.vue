<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>用户注册</h2>
          <span>408真题网站</span>
        </div>
      </template>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名（3-50字符）"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（6-20字符）"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱（可选）"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <CustomButton
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleRegister"
          >
            注册
          </CustomButton>
        </el-form-item>

        <el-form-item>
          <CustomButton
            type="text"
            @click="goToLogin"
          >
            已有账号？立即登录
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
import { register } from '@/api/auth'
import CustomButton from '@/components/basic/CustomButton.vue'

const router = useRouter()

// 表单引用
const registerFormRef = ref(null)

// 加载状态
const loading = ref(false)

// 注册表单数据
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// 自定义验证规则：确认密码
const validateConfirmPassword = (_rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

/**
 * 处理注册
 */
const handleRegister = async () => {
  // 验证表单
  const valid = await registerFormRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    // 调用注册API（不传递confirmPassword）
    await register({
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email || undefined
    })

    ElMessage.success('注册成功，请登录')
    
    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    console.error('注册失败：', error)
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

<style lang="scss" scoped>
/**
 * 注册页面样式
 * 使用Sass变量和mixins统一管理主题
 * 注：变量和mixins已通过Vite全局注入，无需手动导入
 */

.register-container {
  @include flex-center;
  min-height: 100vh;
  background-color: $color-primary; // 使用主题米色背景
}

.register-card {
  width: $container-width-sm;
  box-shadow: $box-shadow-base;
}

.card-header {
  text-align: center;
  
  h2 {
    margin: 0 0 $spacing-xs 0;
    color: $color-text-primary;
    font-weight: $font-weight-bold;
  }
  
  span {
    color: $color-text-secondary;
    font-size: $font-size-base;
  }
}
</style>

