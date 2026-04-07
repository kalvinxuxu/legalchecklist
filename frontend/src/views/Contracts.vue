<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useContracts, useDeleteContract } from '@/composables/useContracts'
import { useToast } from '@/composables/useToast'
import { Upload, Trash2, FileSearch } from 'lucide-vue-next'
import { formatDate, CONTRACT_TYPE_MAP, REVIEW_STATUS_MAP, RISK_LEVEL_MAP } from '@/lib/utils'

const router = useRouter()
const { data: contracts = [], isLoading } = useContracts()
const deleteContract = useDeleteContract()
const { toast } = useToast()
const deletingId = ref<string | null>(null)

async function handleDelete(id: string) {
  if (!confirm('确定要删除这份合同吗？')) return
  deletingId.value = id
  try {
    await deleteContract.mutateAsync(id)
    toast({ title: '删除成功', variant: 'success' })
  } catch {
    toast({ title: '删除失败', variant: 'destructive' })
  } finally {
    deletingId.value = null
  }
}

function getTypeVariant(type: string) {
  return (CONTRACT_TYPE_MAP[type]?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}

function getStatusVariant(status: string) {
  return (REVIEW_STATUS_MAP[status]?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 bg-card border-b border-border">
      <h1 class="text-lg font-semibold">合同列表</h1>
      <UiButton @click="router.push('/workspace/upload')">
        <Upload class="w-4 h-4" />
        上传合同
      </UiButton>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <UiCard v-if="isLoading">
        <UiCardContent class="p-0">
          <div class="p-4 space-y-3">
            <div v-for="i in 5" :key="i" class="h-16 bg-muted rounded-md animate-pulse" />
          </div>
        </UiCardContent>
      </UiCard>

      <UiCard v-else-if="contracts.length === 0">
        <UiCardContent class="py-16 text-center">
          <FileSearch class="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
          <p class="text-muted-foreground mb-4">暂无合同，点击右上角上传合同</p>
          <UiButton @click="router.push('/workspace/upload')">上传合同</UiButton>
        </UiCardContent>
      </UiCard>

      <UiCard v-else>
        <UiCardContent class="p-0">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">合同名称</th>
                  <th class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">类型</th>
                  <th class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">状态</th>
                  <th class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">风险</th>
                  <th class="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">上传时间</th>
                  <th class="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border">
                <tr v-for="contract in contracts" :key="contract.id" class="hover:bg-accent/50 transition-colors">
                  <td class="px-4 py-3 text-sm font-medium max-w-[200px] truncate">{{ contract.file_name }}</td>
                  <td class="px-4 py-3">
                    <UiBadge :variant="getTypeVariant(contract.contract_type)">
                      {{ CONTRACT_TYPE_MAP[contract.contract_type]?.label || contract.contract_type }}
                    </UiBadge>
                  </td>
                  <td class="px-4 py-3">
                    <UiBadge :variant="getStatusVariant(contract.review_status)">
                      {{ REVIEW_STATUS_MAP[contract.review_status]?.label || contract.review_status }}
                    </UiBadge>
                  </td>
                  <td class="px-4 py-3">
                    <span
                      v-if="contract.risk_level"
                      class="text-sm font-medium"
                      :style="{ color: RISK_LEVEL_MAP[contract.risk_level]?.color }"
                    >
                      {{ RISK_LEVEL_MAP[contract.risk_level]?.label }}
                    </span>
                    <span v-else class="text-sm text-muted-foreground">-</span>
                  </td>
                  <td class="px-4 py-3 text-sm text-muted-foreground">{{ formatDate(contract.created_at) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-2">
                      <UiButton
                        size="sm"
                        :variant="contract.review_status === 'completed' ? 'default' : 'outline'"
                        @click="router.push(`/workspace/review/${contract.id}`)"
                      >
                        {{ contract.review_status === 'completed' ? '查看报告' : '查看进度' }}
                      </UiButton>
                      <UiButton
                        size="icon"
                        variant="ghost"
                        @click="handleDelete(contract.id)"
                        :disabled="deletingId === contract.id"
                      >
                        <Trash2 class="w-4 h-4 text-muted-foreground hover:text-danger-500" />
                      </UiButton>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </UiCardContent>
      </UiCard>
    </div>
  </div>
</template>
