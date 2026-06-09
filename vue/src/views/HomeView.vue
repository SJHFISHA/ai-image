<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DownOutlined,
  SendOutlined,
  CopyOutlined,
  EditOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getModelPrices } from '@/api/modelPrice'
import type { ModelPriceItem, ModelPriceListResult } from '@/api/modelPrice'
import { createImageTask, getTaskDetail } from '@/api/generation'
import type { TaskCreateResult, TaskDetailResult } from '@/api/generation'

const userStore = useUserStore()
const inputText = ref('')
const sending = ref(false)
const generatedImages = ref<string[]>([])
const previewImage = ref('')
const currentPrompt = ref('')
const promptExpanded = ref(false)
interface LoadingDot {
  id: number
  delay: string
  opacity: number
}

const loadingDots = Array.from({ length: 144 }, (_, index) => ({
  id: index,
  delay: `${Math.random() * 1.8}s`,
  opacity: 0.2 + Math.random() * 0.8,
})) as LoadingDot[]

function openImagePreview(image: string) {
  previewImage.value = image
}

function closeImagePreview() {
  previewImage.value = ''
}

async function copyPrompt() {
  if (!currentPrompt.value) return

  try {
    await navigator.clipboard.writeText(currentPrompt.value)
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

function editPrompt() {
  if (!currentPrompt.value) return

  inputText.value = currentPrompt.value
  generatedImages.value = []
  previewImage.value = ''
}

function downloadImage(image: string) {
  const link = document.createElement('a')
  link.href = image
  link.download = `ai-image-${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function togglePromptExpanded() {
  promptExpanded.value = !promptExpanded.value
}

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
  currentPrompt.value = inputText.value.trim()
  promptExpanded.value = false
  generatedImages.value = []
  try {
    // 获取模型价格配置
    const priceRes = await getModelPrices('image')
    if (!priceRes.items || priceRes.items.length === 0) {
      message.error('暂无可用模型')
      return
    }

    // 使用第一个可用的配置
    // 根据当前选择的模型、分辨率、图片数量匹配价格配置
    const priceConfig = priceRes.items.find((item) => {
      return (
        item.model_key === selectedModel.value &&
        item.image_size === selectedResolution.value &&
        Number(item.image_count) === Number(selectedCount.value)
      )
    })

    if (!priceConfig) {
      message.error(`当前模型不支持 ${selectedResolution.value} / ${selectedCount.value} 张，请重新选择`)
      return
    }

    // 创建生图任务
    const taskRes = await createImageTask({
      price_config_id: priceConfig.id,
      prompt: inputText.value
    })

    if (taskRes.status === 'success') {
      const detail = await getTaskDetail(taskRes.task_id)
      generatedImages.value = detail.images || []
      message.success('图片生成成功！')
    } else if (taskRes.status === 'failed') {
      generatedImages.value = []
      message.error(taskRes.error_message ? `图片生成失败，积分已退回：${taskRes.error_message}` : '图片生成失败，积分已退回')
    } else {
      generatedImages.value = []
      message.info('任务已提交，请稍后查看结果')
    }

    inputText.value = ''
  } catch (error: unknown) {
    const errorMessage =
      error &&
      typeof error === 'object' &&
      'response' in error &&
      error.response &&
      typeof error.response === 'object' &&
      'data' in error.response &&
      error.response.data &&
      typeof error.response.data === 'object' &&
      'detail' in error.response.data
        ? String(error.response.data.detail)
        : '发送失败'

    message.error(errorMessage)
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
  { key: 'gpt-image-2', label: 'gpt-image-2' },
]
const selectedModel = ref('gpt-image-2')
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
  <div class="chat-page" :class="{ 'has-chat': currentPrompt || generatedImages.length || sending }">
    <h1 v-if="!currentPrompt && !generatedImages.length && !sending" class="main-greeting">
      你好，想创作什么？
    </h1>

    <div v-if="currentPrompt || sending || generatedImages.length" class="chat-thread">
      <div v-if="currentPrompt" class="user-row">
        <div class="user-bubble-wrap">
          <div class="user-bubble" :class="{ expanded: promptExpanded }">
            {{ currentPrompt }}
          </div>

          <div class="prompt-actions">
            <button
              class="prompt-action-btn"
              type="button"
              title="复制"
              @click="copyPrompt"
            >
              <CopyOutlined />
            </button>

            <button
              v-if="currentPrompt.length > 80"
              class="prompt-toggle-btn"
              type="button"
              @click="togglePromptExpanded"
            >
              {{ promptExpanded ? '收起' : '展开' }}
            </button>

            <button
              class="prompt-action-btn"
              type="button"
              title="编辑"
              @click="editPrompt"
            >
              <EditOutlined />
            </button>
          </div>
        </div>
      </div>

      <div v-if="sending" class="assistant-row">
        <div class="generation-card">
          <div class="generation-title">正在创建图片</div>
          <div class="dot-field">
            <span
              v-for="dot in loadingDots"
              :key="dot.id"
              class="loading-dot"
              :style="{ animationDelay: dot.delay, opacity: dot.opacity }"
            ></span>
          </div>
        </div>
      </div>

      <div v-else-if="generatedImages.length" class="assistant-row">
        <div class="image-result-card">
          <div
            v-for="image in generatedImages"
            :key="image"
            class="image-thumb-wrap"
          >
            <button
              class="image-thumb-btn"
              type="button"
              @click="openImagePreview(image)"
            >
              <img
                :src="image"
                class="chat-result-image"
                alt="生成结果"
              />
            </button>

            <button
              class="image-download-btn"
              type="button"
              title="下载"
              @click.stop="downloadImage(image)"
            >
              <DownloadOutlined />
            </button>
          </div>
        </div>
      </div>
    </div>
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
    <div v-if="previewImage" class="image-preview-mask" @click="closeImagePreview">
      <button class="image-preview-close" type="button" @click.stop="closeImagePreview">
        ×
      </button>
      <img
        :src="previewImage"
        class="image-preview-img"
        alt="图片预览"
        @click.stop
      />
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
  padding: 72px 24px 32px;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  z-index: 0;
}

.chat-page.has-chat {
  justify-content: flex-start;
  min-height: auto;
  padding-bottom: 24px;
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
.chat-page.has-chat .input-card {
  position: sticky;
  bottom: 24px;
  width: 100%;
  max-width: 800px;
  z-index: 100;
  margin-top: 24px;
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

.chat-thread {
  width: 100%;
  max-width: 800px;
  margin-top: 20px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.user-row {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.user-bubble-wrap {
  max-width: min(560px, 72%);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.user-bubble {
  width: 100%;
  padding: 10px 18px;
  border-radius: 20px;
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  box-sizing: border-box;
}

.user-bubble.expanded {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset;
}

.prompt-toggle-btn {
  border: none;
  background: transparent;
  color: #1677ff;
  font-size: 12px;
  line-height: 1;
  padding: 2px 4px;
  cursor: pointer;
}

.prompt-toggle-btn:hover {
  color: #4096ff;
}

[data-theme='dark'] .user-bubble {
  background: #2f2f2f;
  color: rgba(255, 255, 255, 0.92);
}

[data-theme='dark'] .user-bubble {
  background: #2f2f2f;
  color: rgba(255, 255, 255, 0.92);
}

.assistant-row {
  display: flex;
  justify-content: flex-start;
}

.generation-card {
  width: min(480px, 100%);
  min-height: 360px;
  border-radius: 28px;
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
  padding: 26px 28px;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

[data-theme='dark'] .generation-card {
  background: #303030;
  color: rgba(255, 255, 255, 0.92);
  box-shadow: none;
}

.generation-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 42px;
}

.dot-field {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 14px;
  padding: 12px 0;
}

.loading-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #777;
  animation: dotPulse 1.8s ease-in-out infinite;
}

[data-theme='dark'] .loading-dot {
  background: #d8d8d8;
}

@keyframes dotPulse {
  0%, 100% {
    transform: scale(0.65);
    opacity: 0.08;
  }

  45% {
    transform: scale(1.35);
    opacity: 0.85;
  }
}

.image-result-card {
  width: min(400px, 100%);
  display: grid;
  gap: 12px;
}

.image-thumb-btn {
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  cursor: zoom-in;
  border-radius: 28px;
  overflow: hidden;
}

.chat-result-image {
  width: 100%;
  aspect-ratio: 1 / 1;
  display: block;
  object-fit: cover;
  border-radius: 28px;
  background: #f5f5f5;
}

.image-preview-mask {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  box-sizing: border-box;
}

.image-preview-img {
  max-width: 92vw;
  max-height: 92vh;
  object-fit: contain;
  border-radius: 12px;
  background: #111;
}

.image-preview-close {
  position: fixed;
  top: 24px;
  right: 28px;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 26px;
  line-height: 38px;
  cursor: pointer;
}

.image-preview-close:hover {
  background: rgba(255, 255, 255, 0.28);
}
.prompt-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-height: 24px;
}

.prompt-action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(0, 0, 0, 0.58);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.prompt-action-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.88);
}

[data-theme='dark'] .prompt-action-btn {
  color: rgba(255, 255, 255, 0.68);
}

[data-theme='dark'] .prompt-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.image-thumb-wrap {
  position: relative;
  width: 100%;
}

.image-download-btn {
  position: absolute;
  right: 14px;
  bottom: 14px;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.48);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(8px);
}

.image-download-btn:hover {
  background: rgba(0, 0, 0, 0.68);
}
</style>
