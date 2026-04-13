<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useKnowledge } from '@/composables/useKnowledge'
import { useToast } from '@/composables/useToast'
import { Upload, Trash2, FileText, Plus, Search, X, FileUp, Shield, Scale, BookOpen } from 'lucide-vue-next'
import { formatDate } from '@/lib/utils'

const {
  knowledgeList,
  total,
  isLoading,
  fetchKnowledge,
  createKnowledge,
  uploadKnowledge,
  deleteKnowledge,
  getContentTypes,
} = useKnowledge()
const { toast } = useToast()

// 状态
const showModal = ref(false)
const showUploadModal = ref(false)
const selectedType = ref<string>('company_policy')
const searchQuery = ref('')
const isCreating = ref(false)
const isUploading = ref(false)

// 筛选状态：默认只看公司政策
const filterType = ref<string>('company_policy')

// 表单
const form = ref({
  title: '',
  content: '',
  content_type: 'company_policy',
})

// 内容类型选项
const contentTypes = ref<{ value: string; label: string; description: string }[]>([])
const filteredKnowledge = computed(() => {
  let items = knowledgeList.value

  // 按类型筛选
  if (filterType.value) {
    items = items.filter(k => k.content_type === filterType.value)
  }

  // 按关键词搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    items = items.filter(
      k => k.title.toLowerCase().includes(query) ||
           k.content.toLowerCase().includes(query)
    )
  }
  return items
})

// 筛选器选项（区分公司政策和法规）
const filterOptions = computed(() => [
  { value: 'company_policy', label: '公司政策', icon: Shield, color: 'text-primary' },
  { value: 'law', label: '法律法规', icon: Scale, color: 'text-info' },
])

onMounted(async () => {
  await loadData()
  contentTypes.value = await getContentTypes()
})

async function loadData() {
  // 加载所有类型的知识，筛选在本地进行
  await fetchKnowledge({ content_type: undefined, limit: 100 })
}

function openCreateModal() {
  form.value = { title: '', content: '', content_type: selectedType.value }
  showModal.value = true
}

function openUploadModal() {
  showUploadModal.value = true
}

async function handleCreate() {
  if (!form.value.title || !form.value.content) {
    toast({ title: '请填写标题和内容', variant: 'destructive' })
    return
  }

  isCreating.value = true
  try {
    await createKnowledge({
      title: form.value.title,
      content: form.value.content,
      content_type: form.value.content_type,
    })
    toast({ title: '创建成功', variant: 'success' })
    showModal.value = false
    await loadData()
  } catch {
    toast({ title: '创建失败', variant: 'destructive' })
  } finally {
    isCreating.value = false
  }
}

async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isUploading.value = true
  try {
    await uploadKnowledge(file, selectedType.value)
    toast({ title: '上传成功', variant: 'success' })
    showUploadModal.value = false
    await loadData()
  } catch {
    toast({ title: '上传失败', variant: 'destructive' })
  } finally {
    isUploading.value = false
    input.value = ''
  }
}

async function handleDelete(id: string) {
  if (!confirm('确定要删除这条知识吗？')) return

  try {
    await deleteKnowledge(id)
    toast({ title: '删除成功', variant: 'success' })
    await loadData()
  } catch {
    toast({ title: '删除失败', variant: 'destructive' })
  }
}

function getTypeLabel(type: string) {
  return contentTypes.value.find(t => t.value === type)?.label || type
}

function getTypeVariant(type: string) {
  switch (type) {
    case 'company_policy': return 'primary'
    case 'law': return 'info'
    case 'case': return 'warning'
    case 'template': return 'success'
    case 'rule': return 'secondary'
    default: return 'secondary'
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 bg-card border-b border-border">
      <div class="flex items-center gap-3">
        <Shield class="w-5 h-5 text-primary" />
        <h1 class="text-lg font-semibold">公司政策库</h1>
      </div>
      <div class="flex gap-2">
        <UiButton @click="openUploadModal">
          <FileUp class="w-4 h-4" />
          上传文档
        </UiButton>
        <UiButton @click="openCreateModal">
          <Plus class="w-4 h-4" />
          手动录入
        </UiButton>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="px-6 py-3 border-b border-border bg-card">
      <div class="flex items-center gap-1">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          @click="filterType = opt.value"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            filterType === opt.value
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          ]"
        >
          <component :is="opt.icon" class="w-4 h-4" :class="filterType === opt.value ? '' : opt.color" />
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="px-6 py-3 border-b border-border">
      <div class="relative max-w-md">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <UiInput
          v-model="searchQuery"
          placeholder="搜索政策..."
          class="pl-9"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-auto p-6">
      <!-- Loading -->
      <div v-if="isLoading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-24 bg-muted rounded-md animate-pulse" />
      </div>

      <!-- Empty -->
      <UiCard v-else-if="filteredKnowledge.length === 0">
        <UiCardContent class="py-16 text-center">
          <FileText class="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
          <p class="text-muted-foreground mb-4">
            {{ searchQuery ? '未找到匹配的知识' : '暂无知识，点击右上角添加' }}
          </p>
          <UiButton v-if="!searchQuery" @click="openCreateModal">添加知识</UiButton>
        </UiCardContent>
      </UiCard>

      <!-- List -->
      <div v-else class="space-y-3">
        <UiCard v-for="item in filteredKnowledge" :key="item.id">
          <UiCardContent class="p-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <h3 class="font-medium truncate">{{ item.title }}</h3>
                  <UiBadge :variant="getTypeVariant(item.content_type) as any">
                    {{ getTypeLabel(item.content_type) }}
                  </UiBadge>
                  <UiBadge v-if="item.is_public" variant="outline">公共</UiBadge>
                </div>
                <p class="text-sm text-muted-foreground line-clamp-2">
                  {{ item.content }}
                </p>
                <div class="text-xs text-muted-foreground mt-2">
                  {{ formatDate(item.created_at) }}
                </div>
              </div>
              <UiButton
                size="icon"
                variant="ghost"
                @click="handleDelete(item.id)"
              >
                <Trash2 class="w-4 h-4 text-muted-foreground hover:text-danger-500" />
              </UiButton>
            </div>
          </UiCardContent>
        </UiCard>
      </div>
    </div>

    <!-- Create Modal -->
    <UiModal v-model:open="showModal" :title="filterType === 'company_policy' ? '添加公司政策' : '添加法规'">
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">标题</label>
          <UiInput v-model="form.title" placeholder="输入政策标题" />
        </div>

        <div class="space-y-2">
          <label class="text-sm font-medium">类型</label>
          <select
            v-model="form.content_type"
            class="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
          >
            <option v-for="type in contentTypes" :key="type.value" :value="type.value">
              {{ type.label }} - {{ type.description }}
            </option>
          </select>
        </div>

        <div class="space-y-2">
          <label class="text-sm font-medium">内容</label>
          <textarea
            v-model="form.content"
            placeholder="输入政策内容..."
            rows="8"
            class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm resize-none"
          />
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <UiButton type="button" variant="outline" @click="showModal = false">
            取消
          </UiButton>
          <UiButton type="submit" :disabled="isCreating">
            {{ isCreating ? '创建中...' : '创建' }}
          </UiButton>
        </div>
      </form>
    </UiModal>

    <!-- Upload Modal -->
    <UiModal v-model:open="showUploadModal" :title="filterType === 'company_policy' ? '上传公司政策文档' : '上传法规文档'">
      <div class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">文档类型</label>
          <select
            v-model="selectedType"
            class="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
          >
            <option v-for="type in contentTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>
        </div>

        <div class="space-y-2">
          <label class="text-sm font-medium">上传文件</label>
          <div class="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
            <input
              type="file"
              accept=".pdf,.docx"
              @change="handleFileUpload"
              class="hidden"
              id="file-upload"
            />
            <label for="file-upload" class="cursor-pointer">
              <Upload class="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
              <p class="text-sm text-muted-foreground">点击选择文件或拖拽到此处</p>
              <p class="text-xs text-muted-foreground mt-1">支持 PDF、Word 文档</p>
            </label>
          </div>
        </div>

        <div class="flex justify-end pt-2">
          <UiButton variant="outline" @click="showUploadModal = false">
            取消
          </UiButton>
        </div>
      </div>
    </UiModal>
  </div>
</template>
