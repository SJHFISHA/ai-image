<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DownOutlined,
  SendOutlined,
  CopyOutlined,
  EditOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getModelPrices } from '@/api/modelPrice'
import type { ModelPriceItem } from '@/api/modelPrice'
import { createImageTask, createImageEditTask, uploadReferenceImage, getTaskDetail } from '@/api/generation'
import { getConversationDetail } from '@/api/conversation'
import type { ConversationMessage } from '@/api/conversation'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const currentSessionId = ref<string | null>(null)
const historyMessages = ref<ConversationMessage[]>([])
const inputText = ref('')
interface ReferenceImageItem {
  id: string
  file: File
  preview: string
}

const selectedReferenceImages = ref<ReferenceImageItem[]>([])
const isDraggingReferenceImage = ref(false)

function revokeReferencePreviews() {
  selectedReferenceImages.value.forEach(item => {
    URL.revokeObjectURL(item.preview)
  })
}

function clearReferenceImages() {
  revokeReferencePreviews()
  selectedReferenceImages.value = []
}
const sending = ref(false)
const generatedImages = ref<string[]>([])
const previewImage = ref('')
const currentPrompt = ref('')

interface RegeneratePayload {
  mode: 'image' | 'edit'
  prompt: string
  priceConfigId: number
  imageUrls?: string[]
}

const lastRegeneratePayload = ref<RegeneratePayload | null>(null)
const promptExpanded = ref(false)
const expandedHistoryMessageIds = ref<Set<string>>(new Set())

function toggleHistoryMessageExpanded(messageId: string) {
  const next = new Set(expandedHistoryMessageIds.value)
  if (next.has(messageId)) {
    next.delete(messageId)
  } else {
    next.add(messageId)
  }
  expandedHistoryMessageIds.value = next
}

function isHistoryMessageExpanded(messageId: string) {
  return expandedHistoryMessageIds.value.has(messageId)
}
const pollTimer = ref<ReturnType<typeof setInterval> | undefined>(undefined)
const isCreatingSession = ref(false)

// 监听路由 query 变化，加载会话历史
watch(() => route.query.session_id, async (sid) => {
  // 如果是创建流程中 router.replace 触发的，只同步 sessionId，不加载历史
  if (isCreatingSession.value) {
    currentSessionId.value = sid ? String(sid) : null
    return
  }

  currentSessionId.value = sid ? String(sid) : null
  generatedImages.value = []
  currentPrompt.value = ''
  historyMessages.value = []

  // 如果有 session_id，加载历史消息（只用 historyMessages 渲染，不设置 generatedImages/currentPrompt）
  if (currentSessionId.value) {
    try {
      const detail = await getConversationDetail(currentSessionId.value)
      historyMessages.value = detail.messages || []
      await nextTick()
      document.querySelector('.main-content')?.scrollTo({ top: 0 })

      const runningMessage = historyMessages.value.find(
        msg => msg.content_type === 'image' && msg.status === 'running' && msg.task_id
      )

      if (runningMessage?.task_id) {
        startPolling(runningMessage.task_id)
      }
    } catch {
      // 静默处理
    }
  }
}, { immediate: true })
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

async function copyPrompt(text = currentPrompt.value) {
  const value = text.trim()
  if (!value) return

  try {
    await navigator.clipboard.writeText(value)
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

function editPrompt(text = currentPrompt.value) {
  const value = text.trim()
  if (!value) return

  inputText.value = value
  generatedImages.value = []
  previewImage.value = ''
  currentPrompt.value = ''
  promptExpanded.value = false
}

async function downloadImage(image: string) {
  try {
    const response = await fetch(image, {
      mode: 'cors',
    })

    if (!response.ok) {
      throw new Error('图片下载失败')
    }

    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const suffix = blob.type === 'image/jpeg' ? 'jpg' : 'png'

    const link = document.createElement('a')
    link.href = objectUrl
    link.download = `ai-image-${Date.now()}.${suffix}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    URL.revokeObjectURL(objectUrl)
  } catch {
    message.error('下载失败，请检查图片链接或稍后重试')
  }
}

function getReferenceImageUrls(msg?: ConversationMessage) {
  const metadata = msg?.metadata_json || {}
  return metadata.reference_image_urls || (metadata.reference_image_url ? [metadata.reference_image_url] : [])
}

function findPreviousUserMessage(messageId: string) {
  const index = historyMessages.value.findIndex(msg => msg.message_id === messageId)
  if (index <= 0) return undefined

  for (let i = index - 1; i >= 0; i -= 1) {
    const messageItem = historyMessages.value[i]
    if (messageItem?.role === 'user') {
      return messageItem
    }
  }

  return undefined
}

async function resolveRegeneratePriceConfigId(taskId: string, mode: 'image' | 'edit') {
  const task = await getTaskDetail(taskId)
  const prices = await getModelPrices(mode === 'edit' ? 'image_edit' : 'image')
  const matched = prices.items?.find(item =>
    item.model_key === task.model_key &&
    item.image_size === task.image_size &&
    (item.aspect_ratio || '') === (task.aspect_ratio || '') &&
    Number(item.image_count) === Number(task.image_count || 1)
  )

  if (!matched) {
    throw new Error('未找到原任务对应的模型价格配置，无法重新生成')
  }

  return matched.id
}

async function submitRegenerate(payload: RegeneratePayload) {
  if (!userStore.isLoggedIn) {
    message.warning('请先登录')
    return
  }

  if (sending.value) return

  sending.value = true
  currentPrompt.value = payload.prompt
  promptExpanded.value = false
  generatedImages.value = []

  try {
    const taskRes = payload.mode === 'edit'
      ? await createImageEditTask({
        session_id: currentSessionId.value || undefined,
        price_config_id: payload.priceConfigId,
        prompt: payload.prompt,
        image_urls: payload.imageUrls || [],
      })
      : await createImageTask({
        session_id: currentSessionId.value || undefined,
        price_config_id: payload.priceConfigId,
        prompt: payload.prompt,
      })

    if (!currentSessionId.value && taskRes.session_id) {
      currentSessionId.value = taskRes.session_id
      isCreatingSession.value = true
      await router.replace({ path: '/image-generate', query: { session_id: taskRes.session_id } })
    }

    if (taskRes.status === 'success') {
      const detail = await getTaskDetail(taskRes.task_id)

      if (currentSessionId.value) {
        const conversation = await getConversationDetail(currentSessionId.value)
        historyMessages.value = conversation.messages || []
        generatedImages.value = []
        currentPrompt.value = ''
      } else {
        generatedImages.value = detail.images || []
      }

      message.success('图片重新生成成功')
      await userStore.fetchUserInfo()
      window.dispatchEvent(new Event('history-refresh'))
      sending.value = false
    } else if (taskRes.status === 'failed') {
      generatedImages.value = []
      message.error(taskRes.error_message ? `图片重新生成失败，积分已退回：${taskRes.error_message}` : '图片重新生成失败，积分已退回')
      await userStore.fetchUserInfo()
      window.dispatchEvent(new Event('history-refresh'))
      sending.value = false
    } else {
      message.info('重新生成任务已提交，正在生成中...')
      startPolling(taskRes.task_id)
    }
  } catch (error: unknown) {
    const errorMessage =
      error &&
      typeof error === 'object' &&
      'message' in error
        ? String(error.message)
        : '重新生成失败'

    message.error(errorMessage)
    sending.value = false
  } finally {
    isCreatingSession.value = false
  }
}

async function regenerateCurrentResult() {
  if (!lastRegeneratePayload.value) {
    message.warning('没有可重新生成的记录')
    return
  }

  await submitRegenerate(lastRegeneratePayload.value)
}

async function regenerateHistoryResult(msg: ConversationMessage) {
  const userMessage = findPreviousUserMessage(msg.message_id)
  const prompt = userMessage?.content_text?.trim()

  if (!prompt || !msg.task_id) {
    message.warning('缺少原提示词，无法重新生成')
    return
  }

  const imageUrls = getReferenceImageUrls(userMessage)
  const mode = imageUrls.length ? 'edit' : 'image'
  const priceConfigId = await resolveRegeneratePriceConfigId(msg.task_id, mode)

  await submitRegenerate({
    mode,
    prompt,
    priceConfigId,
    imageUrls,
  })
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

  if (selectedMode.value === 'edit' && selectedReferenceImages.value.length === 0) {
    message.warning('请先上传需要编辑的图片')
    return
  }

  // 检查是否已选择有效配置
  if (!selectedPriceConfig.value) {
    message.error('当前模型/分辨率/数量组合不可用，请重新选择')
    return
  }

  sending.value = true
  currentPrompt.value = inputText.value.trim()
  promptExpanded.value = false
  generatedImages.value = []

  try {
    // 创建生图任务
    let taskRes

    if (selectedMode.value === 'edit') {
      const uploadResults = await Promise.all(
        selectedReferenceImages.value.map(item => uploadReferenceImage(item.file))
      )
      const imageUrls = uploadResults.map(item => item.url)

      lastRegeneratePayload.value = {
        mode: 'edit',
        prompt: inputText.value,
        priceConfigId: selectedPriceConfig.value.id,
        imageUrls,
      }

      taskRes = await createImageEditTask({
        session_id: currentSessionId.value || undefined,
        price_config_id: selectedPriceConfig.value.id,
        prompt: inputText.value,
        image_urls: imageUrls,
      })
    } else {
      lastRegeneratePayload.value = {
        mode: 'image',
        prompt: inputText.value,
        priceConfigId: selectedPriceConfig.value.id,
      }

      taskRes = await createImageTask({
        session_id: currentSessionId.value || undefined,
        price_config_id: selectedPriceConfig.value.id,
        prompt: inputText.value,
      })
    }

    // 如果后端创建了新会话，更新当前 session_id 并同步 URL
    if (!currentSessionId.value && taskRes.session_id) {
      currentSessionId.value = taskRes.session_id
      isCreatingSession.value = true
      await router.replace({ path: '/image-generate', query: { session_id: taskRes.session_id } })
    }

    // 如果任务已经完成（同步返回成功或失败）
    if (taskRes.status === 'success') {
      const detail = await getTaskDetail(taskRes.task_id)

      if (currentSessionId.value) {
        const conversation = await getConversationDetail(currentSessionId.value)
        historyMessages.value = conversation.messages || []
        generatedImages.value = []
        currentPrompt.value = ''
      } else {
        generatedImages.value = detail.images || []
      }

      message.success('图片生成成功')
      await userStore.fetchUserInfo()
      window.dispatchEvent(new Event('history-refresh'))
      sending.value = false
    } else if (taskRes.status === 'failed') {
      generatedImages.value = []
      message.error(taskRes.error_message ? `图片生成失败，积分已退回：${taskRes.error_message}` : '图片生成失败，积分已退回')
      await userStore.fetchUserInfo()
      window.dispatchEvent(new Event('history-refresh'))
      sending.value = false
    } else {
      // 异步任务，开始轮询
      message.info('任务已提交，正在生成中...')
      startPolling(taskRes.task_id)
    }

    inputText.value = ''
    clearReferenceImages()
  } catch (error: unknown) {
    const errorMessage =
      error &&
      typeof error === 'object' &&
      'message' in error
        ? String(error.message)
        : '发送失败'

    message.error(errorMessage)
    sending.value = false
  } finally {
    isCreatingSession.value = false
  }
}

// ======================== 轮询逻辑 ========================
function startPolling(taskId: string) {
  clearPolling()

  pollTimer.value = setInterval(async () => {
    try {
      const detail = await getTaskDetail(taskId)

      if (detail.status === 'success') {
        if (currentSessionId.value) {
          const conversation = await getConversationDetail(currentSessionId.value)
          historyMessages.value = conversation.messages || []
          generatedImages.value = []
          currentPrompt.value = ''
        } else {
          generatedImages.value = detail.images || []
        }

        message.success('图片生成成功')
        await userStore.fetchUserInfo()
        window.dispatchEvent(new Event('history-refresh'))
        clearPolling()
        sending.value = false
        return
      }

      if (detail.status === 'failed') {
        generatedImages.value = []

        if (currentSessionId.value) {
          const conversation = await getConversationDetail(currentSessionId.value)
          historyMessages.value = conversation.messages || []
        }

        message.error(
          detail.error_message
            ? `图片生成失败，积分已退回：${detail.error_message}`
            : '图片生成失败，积分已退回'
        )
        await userStore.fetchUserInfo()
        window.dispatchEvent(new Event('history-refresh'))
        clearPolling()
        sending.value = false
      }
    } catch (error) {
      console.error('查询任务状态失败:', error)
    }
  }, 2000)
}

function clearPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = undefined
  }
}

onUnmounted(() => {
  clearPolling()
  revokeReferencePreviews()
})

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

  if (selectedMode.value !== 'edit') {
    clearReferenceImages()
  }

  loadModelPrices()
}

function addReferenceFiles(fileList: File[] | FileList) {
  const files = Array.from(fileList)
  if (!files.length) return

  const remainingSlots = 2 - selectedReferenceImages.value.length
  if (remainingSlots <= 0) {
    message.warning('最多只能上传 2 张参考图')
    return
  }

  const validFiles: File[] = []

  for (const file of files) {
    if (!file.type.startsWith('image/')) {
      message.warning('请选择图片文件')
      continue
    }

    if (file.size > 10 * 1024 * 1024) {
      message.warning('图片不能超过 10MB')
      continue
    }

    validFiles.push(file)

    if (validFiles.length >= remainingSlots) {
      break
    }
  }

  for (const file of validFiles) {
    selectedReferenceImages.value.push({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      file,
      preview: URL.createObjectURL(file),
    })
  }

  if (selectedReferenceImages.value.length > 0) {
    selectedMode.value = 'edit'
    loadModelPrices()
  }
}

function handleReferenceFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  addReferenceFiles(input.files || [])
  input.value = ''
}

function handleReferenceDragEnter(event: DragEvent) {
  if (event.dataTransfer?.types.includes('Files')) {
    isDraggingReferenceImage.value = true
  }
}

function handleReferenceDragLeave(event: DragEvent) {
  if (event.currentTarget === event.target) {
    isDraggingReferenceImage.value = false
  }
}

function handleReferenceDrop(event: DragEvent) {
  isDraggingReferenceImage.value = false
  const files = event.dataTransfer?.files
  if (!files?.length) return

  addReferenceFiles(files)
}

function handleReferencePaste(event: ClipboardEvent) {
  const items = Array.from(event.clipboardData?.items || [])
  const imageFiles = items
    .filter(item => item.kind === 'file')
    .map(item => item.getAsFile())
    .filter((file): file is File => !!file && file.type.startsWith('image/'))

  if (!imageFiles.length) return

  event.preventDefault()
  addReferenceFiles(imageFiles)
}

function removeReferenceImage(id: string) {
  const target = selectedReferenceImages.value.find(item => item.id === id)
  if (target) {
    URL.revokeObjectURL(target.preview)
  }

  selectedReferenceImages.value = selectedReferenceImages.value.filter(item => item.id !== id)

  if (selectedReferenceImages.value.length === 0 && selectedMode.value === 'edit') {
    selectedMode.value = 'image'
    loadModelPrices()
  }
}

// ======================== 后端动态配置 ========================
const priceConfigs = ref<ModelPriceItem[]>([])

// 从配置中派生模型列表（去重）
const modelItems = computed(() => {
  const map = new Map<string, string>()
  priceConfigs.value.forEach(item => map.set(item.model_key, item.model_name))
  return Array.from(map.entries()).map(([key, label]) => ({ key, label }))
})

const selectedModel = ref('')
const modelOpen = ref(false)
function handleModelMenu({ key }: { key: string | number }) {
  selectedModel.value = key as string
  // 切换模型后重置分辨率、宽高比和数量
  selectedResolution.value = availableResolutions.value[0] || ''
  selectedAspectRatio.value = availableAspectRatios.value[0] || ''
  selectedCount.value = String(availableCounts.value[0] || 1)
  modelOpen.value = false
}

// 根据当前模型联动可用分辨率
const availableResolutions = computed(() => {
  const sizes = priceConfigs.value
    .filter(item => item.model_key === selectedModel.value)
    .map(item => item.image_size)
    .filter((s): s is string => !!s)
  return [...new Set(sizes)]
})

const selectedResolution = ref('')
const resolutionOpen = ref(false)
function handleResolutionMenu({ key }: { key: string | number }) {
  selectedResolution.value = key as string
  // 重置宽高比和数量
  selectedAspectRatio.value = availableAspectRatios.value[0] || ''
  selectedCount.value = String(availableCounts.value[0] || 1)
  resolutionOpen.value = false
}

// 根据当前模型和分辨率联动可用宽高比
const availableAspectRatios = computed(() => {
  const ratios = priceConfigs.value
    .filter(item => item.model_key === selectedModel.value && item.image_size === selectedResolution.value)
    .map(item => item.aspect_ratio)
    .filter((r): r is string => !!r)
  return [...new Set(ratios)]
})

const selectedAspectRatio = ref('')
const aspectRatioOpen = ref(false)
function handleAspectRatioMenu({ key }: { key: string | number }) {
  selectedAspectRatio.value = key as string
  selectedCount.value = String(availableCounts.value[0] || 1)
  aspectRatioOpen.value = false
}

// 根据当前模型、分辨率和宽高比联动可用数量
const availableCounts = computed(() => {
  const counts = priceConfigs.value
    .filter(item =>
      item.model_key === selectedModel.value &&
      item.image_size === selectedResolution.value &&
      (item.aspect_ratio || '') === selectedAspectRatio.value
    )
    .map(item => item.image_count)
    .filter((c): c is number => !!c)
  return [...new Set(counts)].sort((a, b) => a - b)
})

const selectedCount = ref('1')
const countOpen = ref(false)
function handleCountMenu({ key }: { key: string | number }) {
  selectedCount.value = key as string
  countOpen.value = false
}

// 当前选中的价格配置
const selectedPriceConfig = computed(() =>
  priceConfigs.value.find(item =>
    item.model_key === selectedModel.value &&
    item.image_size === selectedResolution.value &&
    (item.aspect_ratio || '') === selectedAspectRatio.value &&
    Number(item.image_count) === Number(selectedCount.value)
  )
)

// 加载模型价格配置
async function loadModelPrices() {
  try {
    const res = await getModelPrices(selectedMode.value === 'edit' ? 'image_edit' : 'image')
    priceConfigs.value = res.items || []
    // 默认选中第一个
    const first = priceConfigs.value.at(0)
    if (first) {
      selectedModel.value = first.model_key
      selectedResolution.value = first.image_size || ''
      selectedAspectRatio.value = first.aspect_ratio || ''
      selectedCount.value = String(first.image_count || 1)
    }
  } catch {
    // 静默处理
  }
}

onMounted(() => {
  loadModelPrices()
})
</script>

<template>
  <div
    :class="[
    'chat-page',
    { 'has-chat': currentPrompt || generatedImages.length || sending || historyMessages.length }
  ]"
  >
    <h1
      v-if="!currentPrompt && !generatedImages.length && !sending && !historyMessages.length"
      class="main-greeting"
    >
      你好，想创作什么？
    </h1>

    <div v-if="currentPrompt || sending || generatedImages.length || historyMessages.length" class="chat-thread">
      <!-- 历史消息渲染 -->
      <template v-for="msg in historyMessages" :key="msg.message_id">
        <div v-if="msg.role === 'user'" class="user-row">
          <div class="user-bubble-wrap">
            <button
              v-for="url in (msg.metadata_json?.reference_image_urls || (msg.metadata_json?.reference_image_url ? [msg.metadata_json.reference_image_url] : []))"
              :key="url"
              class="reference-history-btn"
              type="button"
              @click="openImagePreview(url)"
            >
              <img
                :src="url"
                class="reference-history-image"
                alt="参考图"
              />
            </button>

            <div
              class="user-bubble"
              :class="{ expanded: isHistoryMessageExpanded(msg.message_id) }"
            >
              {{ msg.content_text }}
            </div>

            <div class="prompt-actions">
              <button
                class="prompt-action-btn"
                type="button"
                title="复制"
                @click="copyPrompt(msg.content_text || '')"
              >
                <CopyOutlined />
              </button>

              <button
                v-if="(msg.content_text || '').length > 80"
                class="prompt-toggle-btn"
                type="button"
                @click="toggleHistoryMessageExpanded(msg.message_id)"
              >
                {{ isHistoryMessageExpanded(msg.message_id) ? '收起' : '展开' }}
              </button>

              <button
                class="prompt-action-btn"
                type="button"
                title="编辑"
                @click="editPrompt(msg.content_text || '')"
              >
                <EditOutlined />
              </button>
            </div>
          </div>
        </div>
        <div v-else-if="msg.role === 'assistant'" class="assistant-row">
          <div v-if="msg.content_type === 'image' && msg.status === 'success' && msg.assets?.length" class="image-result-card">
            <div v-for="asset in msg.assets" :key="asset.asset_id" class="image-thumb-wrap">
              <button class="image-thumb-btn" type="button" @click="openImagePreview(asset.url)">
                <img :src="asset.url" class="chat-result-image" alt="历史图片" />
              </button>
              <div class="image-action-row">
                <button class="image-action-btn" type="button" title="下载" @click.stop="downloadImage(asset.url)">
                  <DownloadOutlined />
                </button>
                <button
                  class="image-action-btn"
                  type="button"
                  title="重新生成"
                  :disabled="sending"
                  @click.stop="regenerateHistoryResult(msg)"
                >
                  <ReloadOutlined />
                  <span>重新生成</span>
                </button>
              </div>
            </div>
          </div>
          <div v-else-if="msg.content_type === 'image' && msg.status === 'running'" class="generation-card">
            <div class="generation-title">正在生成图片...</div>
            <div class="dot-field">
              <span
                v-for="dot in loadingDots"
                :key="dot.id"
                class="loading-dot"
                :style="{ animationDelay: dot.delay, opacity: dot.opacity }"
              ></span>
            </div>
          </div>
          <div v-else-if="msg.content_type === 'image' && msg.status === 'failed'" class="generation-card" style="color: #ff4d4f;">
            <div class="generation-title">图片生成失败</div>
            <div>{{ msg.content_text }}</div>
          </div>
          <div v-else-if="msg.content_type === 'text'" class="user-bubble-wrap" style="align-items: flex-start;">
            <div class="user-bubble" style="background: #f2f3f5;">
              {{ msg.content_text }}
            </div>
          </div>
        </div>
      </template>

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
              @click="copyPrompt()"
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
              @click="editPrompt()"
            >
              <EditOutlined />
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="sending && !historyMessages.some(msg => msg.content_type === 'image' && msg.status === 'running')"
        class="assistant-row"
      >
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

            <div class="image-action-row">
              <button
                class="image-action-btn"
                type="button"
                title="下载"
                @click.stop="downloadImage(image)"
              >
                <DownloadOutlined />
              </button>
              <button
                class="image-action-btn"
                type="button"
                title="重新生成"
                :disabled="sending"
                @click.stop="regenerateCurrentResult"
              >
                <ReloadOutlined />
                <span>重新生成</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      class="input-card"
      :class="{ dragging: isDraggingReferenceImage }"
      @dragenter.prevent="handleReferenceDragEnter"
      @dragover.prevent
      @dragleave.prevent="handleReferenceDragLeave"
      @drop.prevent="handleReferenceDrop"
      @paste="handleReferencePaste"
    >
      <div class="input-area">
        <div
          class="reference-stack"
          :class="{ expanded: selectedReferenceImages.length > 0 }"
        >
          <div
            v-for="(item, index) in selectedReferenceImages"
            :key="item.id"
            class="reference-card"
            :style="{ '--i': index }"
          >
            <img :src="item.preview" alt="参考图" />
            <button
              type="button"
              class="reference-remove"
              @click.stop="removeReferenceImage(item.id)"
            >
              ×
            </button>
          </div>

          <label
            v-if="selectedReferenceImages.length < 2"
            class="reference-add-card"
            :style="{ '--i': selectedReferenceImages.length }"
          >
            <PlusOutlined />
            <input
              class="upload-input"
              type="file"
              accept="image/*"
              multiple
              @change="handleReferenceFileChange"
              @click="($event.target as HTMLInputElement).value = ''"
            />
          </label>
        </div>

        <textarea
          v-model="inputText"
          class="input-text"
          placeholder="输入想法、脚本， “/” 使用技能， @ 添加主体，和Agent一起创作"
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
              <a-menu-item v-for="item in availableResolutions" :key="item" @click="handleResolutionMenu({ key: item })">
                {{ item }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <a-dropdown v-model:open="aspectRatioOpen" :trigger="['click']">
          <button class="toolbar-btn">
            {{ selectedAspectRatio || '宽高比' }}
          </button>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="item in availableAspectRatios" :key="item" @click="handleAspectRatioMenu({ key: item })">
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
              <a-menu-item v-for="item in availableCounts" :key="item" @click="handleCountMenu({ key: item })">
                {{ item }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <span v-if="selectedPriceConfig" class="toolbar-points">
          ✦ {{ selectedPriceConfig.points }} 积分
        </span>

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
  min-height: 100vh;
  padding: 72px 24px 32px;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  z-index: 0;
}

.chat-page.has-chat {
  justify-content: flex-start;
  min-height: 100vh;
  padding-top: 32px;
  padding-bottom: 300px;
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

.input-card.dragging {
  outline: 2px dashed #1677ff;
  outline-offset: 4px;
  background: #f8fbff;
}
.chat-page.has-chat .input-card {
  position: fixed;
  left: calc(50% + 160px);
  bottom: 24px;
  transform: translateX(-50%);
  width: min(800px, calc(100vw - 360px));
  max-width: 800px;
  z-index: 100;
  margin-top: 0;
}

[data-theme='dark'] .input-card {
  background: #1f1f1f;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .input-card.dragging {
  background: rgba(22, 119, 255, 0.08);
}


.input-area {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}



.reference-history-btn {
  width: 96px;
  height: 96px;
  padding: 0;
  border: none;
  border-radius: 10px;
  overflow: hidden;
  cursor: zoom-in;
  background: transparent;
}

.reference-history-image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.upload-input {
  display: none;
}

.reference-stack {
  position: relative;
  width: 72px;
  height: 86px;
  flex: 0 0 72px;
  margin-right: 8px;
}

.reference-card,
.reference-add-card {
  --i: 0;
  position: absolute;
  left: calc(var(--i) * 9px);
  top: calc(var(--i) * 4px);
  width: 58px;
  height: 78px;
  border-radius: 4px;
  transform: rotate(calc(-8deg + var(--i) * 10deg));
  transform-origin: center bottom;
  transition:
    transform 0.2s ease,
    left 0.2s ease,
    top 0.2s ease,
    box-shadow 0.2s ease;
}

.reference-card {
  z-index: calc(2 + var(--i));
  overflow: visible;
  background: #f5f5f5;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
}

.reference-card img {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 4px;
  object-fit: cover;
}

.reference-add-card {
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #8a96a3;
  font-size: 20px;
  background: #f5f6f8;
  border: 1px solid #e5e8ef;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
}

.reference-stack.expanded:hover {
  width: 152px;
  flex-basis: 152px;
}

.reference-stack.expanded:hover .reference-card,
.reference-stack.expanded:hover .reference-add-card {
  left: calc(var(--i) * 62px);
  top: 0;
  transform: rotate(calc(-5deg + var(--i) * 5deg));
}

.reference-stack.expanded:hover .reference-card:hover {
  z-index: 10;
  transform: translateY(-4px) rotate(0deg) scale(1.04);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.18);
}

.reference-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: rgba(28, 34, 42, 0.92);
  color: #fff;
  cursor: pointer;
  line-height: 18px;
  padding: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.reference-card:hover .reference-remove {
  opacity: 1;
}

.reference-add-card:hover {
  color: #1677ff;
  border-color: #b8d8ff;
  background: #f8fbff;
}

[data-theme='dark'] .reference-card,
[data-theme='dark'] .reference-add-card {
  background: #2a2a2a;
  border-color: #424242;
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

.toolbar-points {
  font-size: 12px;
  color: #1677ff;
  font-weight: 500;
  white-space: nowrap;
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
  margin-top: 0;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-top: 8px;
  padding-bottom: 280px;
  box-sizing: border-box;
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
  display: block;
  object-fit: contain;
  border-radius: 28px;
  background: #f5f5f5;
  max-height: 600px;
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

.image-action-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  padding: 8px 0 0;
}

.image-action-btn {
  height: 30px;
  padding: 0 10px;
  border: none;
  border-radius: 15px;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.68);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  font-size: 13px;
}

.image-action-btn:hover {
  background: rgba(0, 0, 0, 0.14);
  color: rgba(0, 0, 0, 0.88);
}

.image-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

[data-theme='dark'] .image-action-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.78);
}

[data-theme='dark'] .image-action-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}
</style>
