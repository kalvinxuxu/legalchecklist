<template>
  <div class="suggestion-card" :class="'risk-' + clause.risk_level">
    <!-- 头部 -->
    <div class="card-header">
      <div class="header-left">
        <span class="clause-index">{{ index + 1 }}</span>
        <span class="clause-title">{{ clause.title || '风险条款' }}</span>
      </div>
      <el-tag :type="getRiskLevelTag(clause.risk_level)" size="small">
        {{ getRiskLevelText(clause.risk_level) }}
      </el-tag>
    </div>

    <!-- 原文 -->
    <div class="card-section original-section">
      <div class="section-label">
        <el-icon><Document /></el-icon>
        <span>原文</span>
      </div>
      <div class="section-content original-text">
        {{ clause.original_text }}
      </div>
    </div>

    <!-- 风险描述 -->
    <div class="card-section risk-section">
      <div class="section-label">
        <el-icon><Warning /></el-icon>
        <span>风险分析</span>
      </div>
      <div class="section-content risk-desc">
        {{ clause.risk_description }}
      </div>
    </div>

    <!-- 修改建议 -->
    <div v-if="suggestion" class="card-section suggestion-section">
      <div class="section-label">
        <el-icon><Edit /></el-icon>
        <span>修改建议</span>
      </div>
      <div class="section-content suggestion-text">
        {{ suggestion }}
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="card-actions">
      <el-button
        type="primary"
        size="small"
        :icon="Check"
        :disabled="accepted"
        @click="$emit('accept', clause)"
      >
        {{ accepted ? '已采纳' : '采纳建议' }}
      </el-button>
      <el-button
        size="small"
        :icon="Close"
        :disabled="rejected"
        @click="$emit('reject', clause)"
      >
        {{ rejected ? '已拒绝' : '拒绝' }}
      </el-button>
      <el-button
        size="small"
        :icon="Edit"
        @click="$emit('edit', clause)"
      >
        编辑
      </el-button>
    </div>

    <!-- 采纳状态指示 -->
    <div v-if="accepted || rejected" class="status-indicator">
      <el-tag v-if="accepted" type="success" size="small">
        <el-icon><Check /></el-icon> 已采纳
      </el-tag>
      <el-tag v-else type="info" size="small">
        <el-icon><Close /></el-icon> 已拒绝
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { Document, Warning, Edit, Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  clause: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 0
  },
  suggestion: {
    type: String,
    default: ''
  },
  accepted: {
    type: Boolean,
    default: false
  },
  rejected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['accept', 'reject', 'edit'])

const getRiskLevelTag = (level) => {
  const tagMap = { 'high': 'danger', 'medium': 'warning', 'low': 'success' }
  return tagMap[level] || ''
}

const getRiskLevelText = (level) => {
  const textMap = { 'high': '高风险', 'medium': '中风险', 'low': '低风险' }
  return textMap[level] || level
}
</script>

<style scoped>
.suggestion-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid var(--color-border);
  position: relative;
  transition: all 0.2s;
}

.suggestion-card:hover {
  box-shadow: var(--shadow-sm);
}

.suggestion-card.risk-high {
  border-left-color: var(--color-red-text);
}

.suggestion-card.risk-medium {
  border-left-color: var(--color-orange-text);
}

.suggestion-card.risk-low {
  border-left-color: var(--color-blue-text);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clause-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-light);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.clause-title {
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.card-section {
  margin-bottom: 12px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.section-label .el-icon {
  font-size: 14px;
}

.original-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.6;
  padding: 8px 12px;
  background: var(--color-bg-light);
  border-radius: var(--radius-sm);
  font-style: italic;
}

.risk-desc {
  font-size: var(--font-size-xs);
  color: var(--color-red-text);
  line-height: 1.5;
}

.suggestion-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.6;
  padding: 8px 12px;
  background: var(--color-purple-bg);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-purple-text);
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.status-indicator {
  position: absolute;
  top: 16px;
  right: 16px;
}
</style>
