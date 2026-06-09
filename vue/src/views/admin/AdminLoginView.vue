<template>
  <div class="admin-login-container">
    <a-card title="后台管理登录" class="admin-login-card">
      <a-form
        :model="formState"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="请输入管理员用户名"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
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
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <router-link to="/">返回前台</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()
const loading = ref(false)

const formState = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  loading.value = true
  try {
    await adminStore.login(formState.username, formState.password)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.admin-login-card {
  width: 420px;
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.admin-login-card :deep(.ant-card-head) {
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}
</style>
