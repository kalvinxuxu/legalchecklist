<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUploadContract } from '@/composables/useContracts'
import { useWorkspaces } from '@/composables/useWorkspaces'
import { Upload as UploadIcon } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { data: workspaces = [] } = useWorkspaces()
const upload = useUploadContract()
const { toast } = useToast()

const form = ref({
  workspaceId: '',
  contractType: '',
  file: null as File | null,
})

const CONTRACT_TYPES = [
  { value: 'NDA', label: 'NDA (保密协议)' },
  { value: '劳动合同', label: '劳动合同' },
  { value: '采购合同', label: '采购合同' },
  { value: '销售合同', label: '销售合同' },
  { value: '服务合同', label: '服务合同' },
  { value: '其他', label: '其他' },
]

// Auto-select first workspace
watch(() => workspaces.value || [], (ws) => {
  if (ws && ws.length > 0 && !form.value.workspaceId) {
    form.value.workspaceId = ws[0].id
  }
}, { immediate: true })

async function handleSubmit() {
  if (!form.value.file) {
    toast({ title: '请选择合同文件', variant: 'destructive' })
    return
  }
  if (!form.value.workspaceId) {
    toast({ title: '请选择工作区', variant: 'destructive' })
    return
  }

  try {
    const response = await upload.mutateAsync({
      file: form.value.file,
      workspaceId: form.value.workspaceId,
      contractType: form.value.contractType,
    })
    toast({ title: '上传成功，开始审查...', variant: 'success' })
    const isWord = form.value.file.name.toLowerCase().endsWith('.docx')
    const path = isWord ? `/workspace/review-word/${response.id}` : `/workspace/review/${response.id}`
    setTimeout(() => router.push(path), 1000)
  } catch {}
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="px-6 py-4 bg-card border-b border-border">
      <h1 class="text-lg font-semibold">上传合同</h1>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <UiCard class="max-w-xl mx-auto">
        <UiCardContent class="pt-6">
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- Workspace -->
            <div class="space-y-2">
              <UiLabel>工作区</UiLabel>
              <UiSelect v-model="form.workspaceId" placeholder="选择工作区">
                <UiSelectItem v-for="ws in workspaces" :key="ws.id" :value="ws.id">
                  {{ ws.name }}
                </UiSelectItem>
              </UiSelect>
            </div>

            <!-- Contract Type -->
            <div class="space-y-2">
              <UiLabel>合同类型</UiLabel>
              <UiSelect v-model="form.contractType" placeholder="选择合同类型">
                <UiSelectItem v-for="type in CONTRACT_TYPES" :key="type.value" :value="type.value">
                  {{ type.label }}
                </UiSelectItem>
              </UiSelect>
            </div>

            <!-- File Upload -->
            <div class="space-y-2">
              <UiLabel>合同文件</UiLabel>
              <div class="border-2 border-dashed border-input rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
                <UploadIcon class="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                <p class="text-sm text-muted-foreground mb-2">
                  拖拽文件到此处或
                  <label class="text-primary-600 hover:underline cursor-pointer ml-1">
                    点击上传
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      class="sr-only"
                      @change="form.file = ($event.target as HTMLInputElement).files?.[0] || null"
                    />
                  </label>
                </p>
                <p class="text-xs text-muted-foreground">支持 PDF 或 .docx 格式，最大 10MB</p>
                <p v-if="form.file" class="mt-3 text-sm text-primary-600 font-medium">
                  已选择: {{ form.file.name }}
                </p>
              </div>
            </div>

            <UiButton type="submit" class="w-full" :loading="upload.isPending.value">
              开始审查
            </UiButton>
          </form>
        </UiCardContent>
      </UiCard>
    </div>
  </div>
</template>
