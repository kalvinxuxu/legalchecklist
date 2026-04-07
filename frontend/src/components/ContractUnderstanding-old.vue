<template>
  <div class="contract-understanding">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
      <p class="loading-tip">正在分析合同结构...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-result icon="error" title="理解分析失败" :sub-title="errorMessage">
        <template #extra>
          <el-button type="primary" @click="loadUnderstanding">
            重新分析
          </el-button>
        </template>
      </el-result>
    </div>

    <!-- 内容展示 -->
    <div v-else-if="understanding" class="understanding-content">
      <!-- 快速理解卡片 -->
      <div v-if="understanding.quick_cards" class="quick-cards">
        <h3 class="section-title">
          <el-icon><magic-stick /></el-icon>
          快速理解
        </h3>
        <div class="cards-grid">
          <!-- 合同用途 -->
          <el-card v-if="understanding.quick_cards.contract_purpose" class="quick-card">
            <template #header>
              <div class="card-header">
                <el-icon><document /></el-icon>
                <span>合同用途</span>
              </div>
            </template>
            <p class="card-text">{{ understanding.quick_cards.contract_purpose }}</p>
          </el-card>

          <!-- 关键日期 -->
          <el-card v-if="understanding.quick_cards.key_dates?.length" class="quick-card">
            <template #header>
              <div class="card-header">
                <el-icon><calendar /></el-icon>
                <span>关键日期</span>
              </div>
            </template>
            <ul class="date-list">
              <li v-for="(date, idx) in understanding.quick_cards.key_dates" :key="idx">
                {{ date }}
              </li>
            </ul>
          </el-card>

          <!-- 支付条款 -->
          <el-card v-if="understanding.quick_cards.payment_summary" class="quick-card payment">
            <template #header>
              <div class="card-header">
                <el-icon><money /></el-icon>
                <span>支付条款</span>
              </div>
            </template>
            <p class="card-text">{{ understanding.quick_cards.payment_summary }}</p>
            <div v-if="understanding.summary?.payment_terms" class="payment-details">
              <span v-if="understanding.summary.payment_terms.amount">
                金额: {{ understanding.summary.payment_terms.amount }}
              </span>
              <span v-if="understanding.summary.payment_terms.payment_method">
                方式: {{ understanding.summary.payment_terms.payment_method }}
              </span>
            </div>
          </el-card>

          <!-- 违约责任 -->
          <el-card v-if="understanding.quick_cards.breach_summary" class="quick-card breach">
            <template #header>
              <div class="card-header">
                <el-icon><warning /></el-icon>
                <span>违约责任</span>
              </div>
            </template>
            <p class="card-text">{{ understanding.quick_cards.breach_summary }}</p>
            <div v-if="understanding.summary?.breach_liability" class="breach-details">
              <p v-if="understanding.summary.breach_liability.compensation_range">
                赔偿范围: {{ understanding.summary.breach_liability.compensation_range }}
              </p>
            </div>
          </el-card>

          <!-- 核心义务 -->
          <el-card
            v-if="understanding.quick_cards.core_obligations?.length"
            class="quick-card obligations"
          >
            <template #header>
              <div class="card-header">
                <el-icon><list /></el-icon>
                <span>双方核心义务</span>
              </div>
            </template>
            <ul class="obligation-list">
              <li v-for="(ob, idx) in understanding.quick_cards.core_obligations" :key="idx">
                {{ ob }}
              </li>
            </ul>
          </el-card>
        </div>
      </div>

      <!-- 合同结构 -->
      <div v-if="understanding.structure?.sections?.length" class="structure-section">
        <h3 class="section-title">
          <el-icon><folder /></el-icon>
          合同结构
        </h3>
        <div class="structure-summary">
          {{ understanding.structure.structure_summary }}
        </div>
        <el-timeline class="structure-timeline">
          <el-timeline-item
            v-for="(section, idx) in understanding.structure.sections"
            :key="idx"
            :color="getSectionColor(section.title)"
            :hollow="true"
          >
            <div class="timeline-item">
              <span class="section-title-text">{{ section.title }}</span>
              <span class="section-content-preview">{{ section.content }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 关键条款摘要 -->
      <div v-if="understanding.summary?.key_clauses?.length" class="key-clauses-section">
        <h3 class="section-title">
          <el-icon><reading /></el-icon>
          重要条款摘要
        </h3>
        <div class="clauses-list">
          <el-card
            v-for="(clause, idx) in understanding.summary.key_clauses"
            :key="idx"
            class="clause-card"
            :class="'clause-' + clause.risk_benefit"
          >
            <div class="clause-header">
              <span class="clause-title">{{ clause.title }}</span>
              <el-tag
                :type="getRiskBenefitTag(clause.risk_benefit)"
                size="small"
              >
                {{ getRiskBenefitText(clause.risk_benefit) }}
              </el-tag>
            </div>
            <p class="clause-summary">{{ clause.summary }}</p>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-else class="empty-container">
      <el-result icon="info" title="暂无理解分析结果">
        <template #extra>
          <el-button type="primary" @click="loadUnderstanding">
            立即分析
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import {
  MagicStick,
  Document,
  Calendar,
  Money,
  Warning,
  List,
  Folder,
  Reading
} from '@element-plus/icons-vue'
import { contractsApi } from '@/api/contracts'
import { ElMessage } from 'element-plus'

const props = defineProps({
  contractId: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')
const understanding = ref(null)

const loadUnderstanding = async () => {
  if (!props.contractId) return

  loading.value = true
  error.value = false

  try {
    const data = await contractsApi.getUnderstanding(props.contractId)
    understanding.value = data
  } catch (err) {
    error.value = true
    errorMessage.value = err.response?.data?.detail || '加载失败'
    console.error('理解分析加载失败:', err)
  } finally {
    loading.value = false
  }
}

const getRiskBenefitTag = (type) => {
  const map = {
    'risk': 'danger',
    'benefit': 'success',
    'neutral': 'info'
  }
  return map[type] || 'info'
}

const getRiskBenefitText = (type) => {
  const map = {
    'risk': '风险',
    'benefit': '利好',
    'neutral': '中性'
  }
  return map[type] || type
}

const getSectionColor = (title) => {
  const lower = title.toLowerCase()
  if (lower.includes('违约') || lower.includes('责任')) return '#F56C6C'
  if (lower.includes('保密') || lower.includes('义务')) return '#409EFF'
  if (lower.includes('支付') || lower.includes('报酬')) return '#67C23A'
  if (lower.includes('终止') || lower.includes('解除')) return '#E6A23C'
  return '#909399'
}

onMounted(() => {
  loadUnderstanding()
})

watch(() => props.contractId, () => {
  loadUnderstanding()
})
</script>

<style scoped>
.contract-understanding {
  padding: 16px;
}

.loading-container {
  padding: 24px;
}

.loading-tip {
  text-align: center;
  color: var(--color-text-secondary);
  margin-top: 16px;
}

.error-container {
  padding: 24px;
}

.understanding-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
}

.quick-cards {
  margin-bottom: 16px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.quick-card {
  background: var(--color-bg-white);
}

.quick-card.payment {
  border-left: 3px solid var(--color-green-text);
}

.quick-card.breach {
  border-left: 3px solid var(--color-red-text);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.card-text {
  color: var(--color-text-primary);
  line-height: 1.6;
  margin: 0;
}

.payment-details,
.breach-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.date-list,
.obligation-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-primary);
}

.date-list li,
.obligation-list li {
  line-height: 1.8;
}

.structure-section {
  margin-top: 16px;
}

.structure-summary {
  padding: 12px 16px;
  background: var(--color-bg-light);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  margin-bottom: 16px;
  font-size: var(--font-size-sm);
}

.structure-timeline {
  padding-left: 8px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title-text {
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-content-preview {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.clauses-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.clause-card {
  background: var(--color-bg-white);
}

.clause-card.clause-risk {
  border-left: 3px solid var(--color-red-text);
}

.clause-card.clause-benefit {
  border-left: 3px solid var(--color-green-text);
}

.clause-card.clause-neutral {
  border-left: 3px solid var(--color-blue-text);
}

.clause-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.clause-title {
  font-weight: 600;
  color: var(--color-text-primary);
}

.clause-summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.empty-container {
  padding: 48px;
}
</style>
