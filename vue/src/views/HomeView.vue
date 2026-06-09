<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UpOutlined, DownOutlined, SendOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getModelPrices } from '@/api/modelPrice'
import { createImageTask } from '@/api/generation'

const userStore = useUserStore()
const inputText = ref('')
const sending = ref(false)

async function handleSend() {
  if (!inputText.value.trim()) {
    message.warning('请输入提示词')
    return
  }

  if (!userStore.isLoggedIn) {
    message.warning('请先登录')
    return
  }

  if (sending.value) return

  sending.value = true
  try {
    // 获取模型价格配置
    const priceRes: any = await getModelPrices('image')
    if (!priceRes.items || priceRes.items.length === 0) {
      message.error('暂无可用模型')
      return
    }

    // 使用第一个可用的配置
    const priceConfig = priceRes.items[0]

    // 创建生图任务
    const taskRes: any = await createImageTask({
      price_config_id: priceConfig.id,
      prompt: inputText.value
    })

    if (taskRes.status === 'success') {
      message.success('图片生成成功！')
    } else if (taskRes.status === 'failed') {
      message.error('图片生成失败，积分已退回')
    } else {
      message.info('任务已提交，请稍后查看结果')
    }

    inputText.value = ''
  } catch (error: any) {
    message.error(error?.response?.data?.detail || '发送失败')
  } finally {
    sending.value = false
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 图片生成模式
const agentModeItems = [
  { key: 'image', label: '图片生成' },
  { key: 'edit', label: '图片编辑' },
  { key: 'video', label: '视频生成' },
]
const selectedMode = ref('image')
const agentModeOpen = ref(false)

function handleAgentModeMenu({ key }: { key: string | number }) {
  selectedMode.value = key as string
  agentModeOpen.value = false
}

// 模型选择
const modelItems = [
  { key: 'gpt-image2', label: 'gpt-image2' },
]
const selectedModel = ref('gpt-image2')
const modelOpen = ref(false)
function handleModelMenu({ key }: { key: string | number }) {
  selectedModel.value = key as string
  modelOpen.value = false
}

// 图片分辨率
const resolutionItems = [
  '1024x1024',
  '1536x1024',
  '1024x1536',
  '2048x2048',
  '2048x1152',
  '3840x2160',
  '2160x3840',
]
const selectedResolution = ref('1024x1024')
const resolutionOpen = ref(false)
function handleResolutionMenu({ key }: { key: string | number }) {
  selectedResolution.value = key as string
  resolutionOpen.value = false
}

// 图片数量
const countItems = Array.from({ length: 10 }, (_, i) => ({ key: String(i + 1), label: String(i + 1) }))
const selectedCount = ref('1')
const countOpen = ref(false)
function handleCountMenu({ key }: { key: string | number }) {
  selectedCount.value = key as string
  countOpen.value = false
}
</script>

<template>
  <div class="chat-page">
    <h1 class="main-greeting">你好，想创作什么？</h1>

    <div class="input-card">
      <div class="input-area">
        <div class="upload-btn">
          <PlusOutlined />
        </div>
        <textarea
          v-model="inputText"
          class="input-text"
          placeholder="输入想法、剧本或上传参考，支持 / 使用技能，@ 添加主体，和Agent一起创作"
          rows="2"
          @keydown="handleKeyDown"
        ></textarea>
      </div>

      <div class="toolbar">
        <a-dropdown v-model:open="agentModeOpen" :trigger="['click']">
          <button class="toolbar-btn active">
            {{ agentModeItems.find(i => i.key === selectedMode)?.label || '图片生成' }}
            <DownOutlined class="toolbar-arrow" />
          </button>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="item in agentModeItems" :key="item.key" @click="handleAgentModeMenu({ key: item.key })">
                {{ item.label }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <a-dropdown v-model:open="modelOpen" :trigger="['click']">
          <button class="toolbar-btn">
            {{ modelItems.find(i => i.key === selectedModel)?.label || '选择模型' }}
          </button>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="item in modelItems" :key="item.key" @click="handleModelMenu({ key: item.key })">
                {{ item.label }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <a-dropdown v-model:open="resolutionOpen" :trigger="['click']">
          <button class="toolbar-btn">
            {{ selectedResolution || '图片分辨率' }}
          </button>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="item in resolutionItems" :key="item" @click="handleResolutionMenu({ key: item })">
                {{ item }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <a-dropdown v-model:open="countOpen" :trigger="['click']">
          <button class="toolbar-btn">
            图片数量 {{ selectedCount }}
          </button>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="item in countItems" :key="item.key" @click="handleCountMenu({ key: item.key })">
                {{ item.label }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <span class="toolbar-spacer"></span>

        <button class="send-btn" :class="{ active: inputText.trim() }" :disabled="sending" @click="handleSend">
          <SendOutlined v-if="!sending" />
          <span v-else class="sending-dot">...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  z-index: 0;
}

.main-greeting {
  font-size: 24px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
  margin-bottom: 20px;
  text-align: center;
}

[data-theme='dark'] .main-greeting {
  color: rgba(255, 255, 255, 0.88);
}

.input-card {
  width: 100%;
  max-width: 800px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

[data-theme='dark'] .input-card {
  background: #1f1f1f;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.input-area {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}

.upload-btn {
  width: 32px;
  height: 32px;
  min-width: 32px;
  border-radius: 6px;
  background: #f5f5f5;
  border: 1px dashed #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  color: #999;
  font-size: 16px;
}

.upload-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
}

[data-theme='dark'] .upload-btn {
  background: #2a2a2a;
  border-color: #424242;
  color: #666;
}

.input-text {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 13px;
  line-height: 1.4;
  color: rgba(0, 0, 0, 0.65);
  background: transparent;
  min-height: 80px;
  width: 100%;
  max-width: none;
}

.input-text::placeholder {
  color: rgba(0, 0, 0, 0.35);
}

[data-theme='dark'] .input-text {
  color: rgba(255, 255, 255, 0.65);
}

[data-theme='dark'] .input-text::placeholder {
  color: rgba(255, 255, 255, 0.35);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.toolbar-btn {
  border-radius: 14px;
  font-size: 13px;
  height: 30px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid #e8e8e8;
  background: #fff;
  color: rgba(0, 0, 0, 0.65);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.toolbar-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
}

[data-theme='dark'] .toolbar-btn {
  border-color: #424242;
  background: #2a2a2a;
  color: rgba(255, 255, 255, 0.65);
}

[data-theme='dark'] .toolbar-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
}

.toolbar-btn.active {
  color: #1677ff;
  border-color: #1677ff;
  background: #e6f4ff;
}

[data-theme='dark'] .toolbar-btn.active {
  background: rgba(22, 119, 255, 0.15);
}

.toolbar-arrow {
  font-size: 8px;
  margin-left: 2px;
}

.toolbar-spacer {
  flex: 1;
}

.send-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f0f0f0;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #bbb;
  flex-shrink: 0;
  font-size: 12px;
}

.send-btn:hover {
  background: #1677ff;
  color: #fff;
}

.send-btn.active {
  background: #1677ff;
  color: #fff;
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sending-dot {
  font-size: 14px;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

[data-theme='dark'] .send-btn {
  background: #303030;
  color: #555;
}

[data-theme='dark'] .send-btn:hover {
  background: #1677ff;
  color: #fff;
}
</style>
