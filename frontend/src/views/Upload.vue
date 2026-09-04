<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUploadContract } from '@/composables/useContracts'
import { useWorkspaces } from '@/composables/useWorkspaces'
import { Upload as UploadIcon, Shield, FileText, Check } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { data: workspaces = [] } = useWorkspaces()
const upload = useUploadContract()
const { toast } = useToast()

const currentStep = ref(1) // 1: 审查立场配置, 2: 上传合同
const form = ref({
  workspaceId: '',
  contractType: '',
  file: null as File | null,
  // 审查立场配置
  partyPosition: null as string | null,
  contractAmount: null as number | null,
  riskPreference: null as string | null,
})

const CONTRACT_TYPES = [
  { value: 'NDA', label: 'NDA (保密协议)' },
  { value: '劳动合同', label: '劳动合同' },
  { value: '采购合同', label: '采购合同' },
  { value: '销售合同', label: '销售合同' },
  { value: '服务合同', label: '服务合同' },
  { value: '其他', label: '其他' },
]

const POSITION_OPTIONS = [
  {
    value: 'party_a',
    label: '甲方',
    sublabel: '买方/发包方',
    description: '严格保护甲方利益，倾向于更严格的付款条件和更高的违约金保护',
    color: 'border-[#1565C0] bg-[#E3F2FD]/30'
  },
  {
    value: 'party_b',
    label: '乙方',
    sublabel: '卖方/承包方',
    description: '平衡乙方权益，倾向于更宽松的付款条件和更低的违约金压力',
    color: 'border-[#E65100] bg-[#FFF3E0]/30'
  }
]

const RISK_OPTIONS = [
  { value: 'low', label: '低风险', sublabel: '零容忍', description: '严格保护公司利益' },
  { value: 'medium', label: '中风险', sublabel: '平衡策略', description: '在保护和机会之间寻求平衡' },
  { value: 'high', label: '高风险', sublabel: '开放策略', description: '可接受合理风险以换取商业机会' }
]

// Auto-select first workspace
watch(() => workspaces.value || [], (ws) => {
  if (ws && ws.length > 0 && !form.value.workspaceId) {
    form.value.workspaceId = ws[0].id
  }
}, { immediate: true })

function goToStep2() {
  // 第一步完成，进入第二步
  currentStep.value = 2
}

function goBackToStep1() {
  currentStep.value = 1
}

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
      // 传递审查立场配置
      partyPosition: form.value.partyPosition,
      contractAmount: form.value.contractAmount,
      riskPreference: form.value.riskPreference,
    })
    toast({ title: '上传成功', description: '合同已存档，可在详情页开始审查', variant: 'success' })
    // PDF 和 DOCX 统一进入可恢复审查详情页，避免 DOCX 落入旧版 review-word 流程。
    setTimeout(() => router.push(`/workspace/review/${response.id}`), 1500)
  } catch {}
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="px-6 py-4 bg-card border-b border-border">
      <h1 class="text-lg font-semibold">上传合同</h1>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <!-- 步骤指示器 -->
      <div class="max-w-xl mx-auto mb-6">
        <div class="flex items-center justify-center gap-4">
          <div class="flex items-center gap-2">
            <div :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
              currentStep >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            ]">
              <Shield v-if="currentStep === 1" class="w-4 h-4" />
              <Check v-else-if="currentStep > 1" class="w-4 h-4" />
              <span v-else>1</span>
            </div>
            <span :class="currentStep >= 1 ? 'text-foreground' : 'text-muted-foreground'" class="text-sm font-medium">审查立场</span>
          </div>
          <div class="w-12 h-px bg-border" />
          <div class="flex items-center gap-2">
            <div :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
              currentStep >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            ]">
              <FileText v-if="currentStep === 2" class="w-4 h-4" />
              <span v-else>2</span>
            </div>
            <span :class="currentStep >= 2 ? 'text-foreground' : 'text-muted-foreground'" class="text-sm font-medium">上传合同</span>
          </div>
        </div>
      </div>

      <UiCard class="max-w-xl mx-auto">
        <UiCardContent class="pt-6">
          <!-- 步骤1: 审查立场配置 -->
          <div v-if="currentStep === 1" class="space-y-6">
            <div class="text-center mb-6">
              <Shield class="w-10 h-10 text-primary mx-auto mb-2" />
              <h2 class="text-lg font-semibold">配置审查参数</h2>
              <p class="text-sm text-muted-foreground mt-1">选择合同类型并配置审查立场，AI 将据此进行针对性审查</p>
            </div>

            <!-- 合同类型 -->
            <div class="space-y-2">
              <UiLabel class="text-sm font-medium">合同类型</UiLabel>
              <UiSelect v-model="form.contractType" placeholder="选择合同类型">
                <UiSelectItem v-for="type in CONTRACT_TYPES" :key="type.value" :value="type.value">
                  {{ type.label }}
                </UiSelectItem>
              </UiSelect>
            </div>

            <!-- 甲乙方立场 -->
            <div class="space-y-3">
              <UiLabel class="text-sm font-medium">我的立场</UiLabel>
              <div class="grid grid-cols-2 gap-3">
                <button
                  v-for="opt in POSITION_OPTIONS"
                  :key="opt.value"
                  type="button"
                  @click="form.partyPosition = opt.value"
                  :class="[
                    'relative flex flex-col items-start p-3 rounded-lg border-2 transition-all text-left',
                    form.partyPosition === opt.value
                      ? opt.color + ' ' + 'border-current shadow-sm'
                      : 'border-border hover:border-muted-foreground/30 bg-card'
                  ]"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-semibold">{{ opt.label }}</span>
                    <span class="text-xs text-muted-foreground">{{ opt.sublabel }}</span>
                  </div>
                  <p class="text-xs text-muted-foreground leading-relaxed">
                    {{ opt.description }}
                  </p>
                  <div
                    v-if="form.partyPosition === opt.value"
                    class="absolute top-2 right-2 w-4 h-4 rounded-full bg-primary flex items-center justify-center"
                  >
                    <Check class="w-3 h-3 text-primary-foreground" />
                  </div>
                </button>
              </div>
            </div>

            <!-- 风险偏好 -->
            <div class="space-y-3">
              <UiLabel class="text-sm font-medium">风险偏好</UiLabel>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="opt in RISK_OPTIONS"
                  :key="opt.value"
                  type="button"
                  @click="form.riskPreference = opt.value"
                  :class="[
                    'relative flex flex-col items-center p-3 rounded-lg border-2 transition-all',
                    form.riskPreference === opt.value
                      ? 'border-primary bg-primary-50 shadow-sm'
                      : 'border-border hover:border-muted-foreground/30 bg-card'
                  ]"
                >
                  <span class="text-sm font-semibold">{{ opt.label }}</span>
                  <span class="text-xs text-muted-foreground">{{ opt.sublabel }}</span>
                  <p class="text-xs text-muted-foreground text-center mt-1 leading-relaxed">
                    {{ opt.description }}
                  </p>
                </button>
              </div>
            </div>

            <!-- 合同金额 -->
            <div class="space-y-2">
              <UiLabel class="text-sm font-medium">合同金额（元）- 可选</UiLabel>
              <input
                v-model.number="form.contractAmount"
                type="number"
                placeholder="请输入合同金额"
                class="w-full px-3 py-2 text-sm border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <UiButton type="button" @click="goToStep2" class="w-full">
              下一步：上传合同
            </UiButton>
          </div>

          <!-- 步骤2: 上传合同 -->
          <div v-else-if="currentStep === 2" class="space-y-6">
            <div class="text-center mb-6">
              <FileText class="w-10 h-10 text-primary mx-auto mb-2" />
              <h2 class="text-lg font-semibold">上传合同文件</h2>
              <p class="text-sm text-muted-foreground mt-1">已配置审查参数，AI 将据此进行针对性审查</p>
            </div>

            <!-- 配置摘要 -->
            <div class="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <Shield class="w-4 h-4 text-primary" />
                <span v-if="form.contractType">{{ form.contractType }}</span>
                <span v-if="form.partyPosition === 'party_a'" class="text-muted-foreground">| 甲方立场</span>
                <span v-else-if="form.partyPosition === 'party_b'" class="text-muted-foreground">| 乙方立场</span>
                <span v-if="form.riskPreference" class="text-muted-foreground">| {{ form.riskPreference === 'low' ? '低风险' : form.riskPreference === 'medium' ? '中风险' : '高风险' }}偏好</span>
                <span v-if="form.contractAmount" class="text-muted-foreground">| {{ form.contractAmount }} 元</span>
              </div>
            </div>

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

              <div class="flex gap-3">
                <UiButton type="button" variant="outline" @click="goBackToStep1" class="flex-1">
                  上一步
                </UiButton>
                <UiButton type="submit" class="flex-1" :loading="upload.isPending.value">
                  上传合同
                </UiButton>
              </div>
            </form>
          </div>
        </UiCardContent>
      </UiCard>
    </div>
  </div>
</template>
