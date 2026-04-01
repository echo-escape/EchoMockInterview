<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import { listInterviews, createInterview, deleteInterview, toggleFavorite } from '../../api/interview'
import InterviewCard from '../../components/common/InterviewCard.vue'

const router = useRouter()
const authStore = useAuthStore()

const interviews = ref<any[]>([])
const loading = ref(false)
const targetRole = ref('')
const creating = ref(false)
const resumeFile = ref<File | null>(null)
const isDragOver = ref(false)

const resumeInfo = computed(() => {
  if (!resumeFile.value) return null
  const size = resumeFile.value.size
  const sizeStr = size < 1024 * 1024
    ? `${(size / 1024).toFixed(1)} KB`
    : `${(size / 1024 / 1024).toFixed(1)} MB`
  return { name: resumeFile.value.name, size: sizeStr }
})

const fetchInterviews = async () => {
  loading.value = true
  try {
    interviews.value = await listInterviews() as any[]
  } catch (error) {
    console.error('Failed to fetch interviews:', error)
  } finally {
    loading.value = false
  }
}

const handleStartInterview = async () => {
  if (!targetRole.value.trim()) return
  
  creating.value = true
  try {
    const data: any = await createInterview(
      targetRole.value,
      resumeFile.value || undefined
    )
    router.push(`/interview/${data.id}`)
  } catch (error) {
    console.error('Failed to start interview:', error)
  } finally {
    creating.value = false
  }
}

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) {
    validateAndSetFile(input.files[0])
  }
}

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
}

const validateAndSetFile = (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'docx'].includes(ext || '')) {
    alert('仅支持 PDF 和 DOCX 格式')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('文件大小不能超过 5MB')
    return
  }
  resumeFile.value = file
}

const removeFile = () => {
  resumeFile.value = null
}

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}

const handleDelete = async (sessionId: string) => {
  try {
    await deleteInterview(sessionId)
    interviews.value = interviews.value.filter(i => i.id !== sessionId)
  } catch (error) {
    console.error('Failed to delete interview:', error)
  }
}

const handleToggleFavorite = async (sessionId: string) => {
  try {
    const updated = await toggleFavorite(sessionId)
    const index = interviews.value.findIndex(i => i.id === sessionId)
    if (index !== -1) {
      interviews.value[index].is_favorite = updated.is_favorite
    }
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}

onMounted(() => {
  fetchInterviews()
})
</script>

<template>
  <div class="dashboard-container">
    <nav class="top-nav">
      <div class="nav-brand">Echo Mock</div>
      <div class="user-info">
        <span class="username">{{ authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">退出</button>
      </div>
    </nav>

    <main class="dashboard-content">
      <!-- Start Panel -->
      <section class="start-panel glass-panel">
        <div class="section-title">发起新面试</div>
        <p class="section-desc">告诉 AI 您想挑战的职位，我们将为您量身定制面试方案。</p>
        
        <div class="start-form">
          <input 
            v-model="targetRole" 
            type="text" 
            class="input-base" 
            placeholder="例如: 后端开发工程师, 架构师, 测试..."
          />
          <button @click="handleStartInterview" class="btn-primary" :disabled="creating">
            {{ creating ? '创建中...' : '开始模拟面试' }}
          </button>
        </div>

        <!-- Resume Upload Area -->
        <div class="upload-section">
          <div 
            v-if="!resumeFile"
            class="upload-dropzone"
            :class="{ 'drag-over': isDragOver }"
            @click="($refs.fileInput as HTMLInputElement).click()"
            @dragover.prevent="isDragOver = true"
            @dragleave="isDragOver = false"
            @drop.prevent="handleDrop"
          >
            <div class="upload-icon">📄</div>
            <div class="upload-text">
              <span class="upload-main-text">上传简历（可选）</span>
              <span class="upload-hint">拖拽文件到此处，或点击选择 · 支持 PDF / DOCX · 最大 5MB</span>
            </div>
          </div>

          <div v-else class="file-preview">
            <div class="file-info">
              <span class="file-icon">📎</span>
              <div class="file-details">
                <span class="file-name">{{ resumeInfo?.name }}</span>
                <span class="file-size">{{ resumeInfo?.size }}</span>
              </div>
            </div>
            <button class="btn-remove-file" @click="removeFile" title="移除简历">✕</button>
          </div>

          <input 
            ref="fileInput"
            type="file" 
            accept=".pdf,.docx"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>
      </section>

      <!-- History List -->
      <section class="history-list">
        <div class="section-header">
          <h2 class="section-title">面试记录</h2>
          <button @click="fetchInterviews" class="btn-refresh" :disable="loading">
            <span class="refresh-icon" :class="{ 'spinning': loading }">🔄</span>
            刷新
          </button>
        </div>

        <div v-if="loading" class="loading-state">载入中...</div>
        
        <div v-else-if="interviews.length === 0" class="empty-state glass-panel">
          还没有面试记录，开始您的第一次挑战吧！
        </div>

        <div v-else class="grid-layout">
          <InterviewCard 
            v-for="item in interviews" 
            :key="item.id" 
            :item="item"
            @click="router.push(`/interview/${item.id}`)"
            @view-report="router.push(`/report/${item.id}`)"
            @continue="router.push(`/interview/${item.id}`)"
            @delete="handleDelete(item.id)"
            @toggle-favorite="handleToggleFavorite(item.id)"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-bottom: 40px;
}

.nav-brand {
  font-size: 24px;
  font-weight: 800;
  color: var(--color-accent);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-weight: 500;
  color: var(--color-text-secondary);
}

.btn-logout {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.start-panel {
  padding: 40px;
  text-align: center;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

.section-desc {
  color: var(--color-text-secondary);
  margin-bottom: 32px;
}

.start-form {
  display: flex;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

/* ===== Resume Upload ===== */
.upload-section {
  max-width: 600px;
  margin: 20px auto 0;
}

.upload-dropzone {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md, 12px);
  cursor: pointer;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.4);
}

.upload-dropzone:hover {
  border-color: var(--color-accent);
  background: rgba(61, 127, 255, 0.04);
}

.upload-dropzone.drag-over {
  border-color: var(--color-accent);
  background: rgba(61, 127, 255, 0.08);
  transform: scale(1.01);
}

.upload-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.upload-text {
  display: flex;
  flex-direction: column;
  text-align: left;
  gap: 4px;
}

.upload-main-text {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-md, 12px);
  background: rgba(61, 127, 255, 0.06);
  animation: fadeSlideIn 0.3s ease;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 20px;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
}

.file-size {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.btn-remove-file {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-remove-file:hover {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== History Section ===== */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid var(--color-border);
  padding: 8px 16px;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-refresh:hover {
  background: #fcfcfc;
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-refresh:active {
  transform: scale(0.98);
}

.refresh-icon {
  display: inline-block;
  font-size: 14px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
