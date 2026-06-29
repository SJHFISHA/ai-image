<template>
  <div class="register-container">
    <a-card title="注册" class="register-card">
      <a-form
        :model="formState"
        @finish="handleRegister"
        layout="vertical"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[
            { required: true, message: '请输入用户名' },
            { min: 2, message: '用户名至少2个字符' }
          ]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          :rules="[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少6个字符' }
          ]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="确认密码"
          name="confirmPassword"
          :rules="[
            { required: true, message: '请确认密码' },
            { validator: validateConfirmPassword }
          ]"
        >
          <a-input-password
            v-model:value="formState.confirmPassword"
            placeholder="请再次输入密码"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="邀请码"
          name="inviteCode"
        >
          <a-input
            v-model:value="formState.inviteCode"
            placeholder="选填，填写好友邀请码双方各得50积分"
            size="large"
            :maxlength="16"
          />
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
            size="large"
          >
            注册
          </a-button>
        </a-form-item>
      </a-form>

      <div class="register-footer">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance } from 'ant-design-vue'

const userStore = useUserStore()
const loading = ref(false)

const formState = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  inviteCode: ''
})

const validateConfirmPassword = async (_rule: any, value: string) => {
  if (value !== formState.password) {
    throw new Error('两次输入的密码不一致')
  }
}

const handleRegister = async () => {
  loading.value = true
  try {
    await userStore.register(
      formState.username,
      formState.password,
      formState.confirmPassword,
      formState.inviteCode || undefined
    )
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.register-footer {
  text-align: center;
  margin-top: 16px;
}
</style>
