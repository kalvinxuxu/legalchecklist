<template>
  <div class="dashboard">
    <el-card>
      <h2>欢迎使用法务 AI 合同审查系统</h2>
      <p class="description">
        上传您的合同文件，AI 将在 30 秒内完成审查并输出专业报告
      </p>

      <el-row :gutter="24" style="margin-top: 40px">
        <el-col :span="8">
          <el-statistic title="已审查合同" :value="stats.contractCount" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="高风险条款" :value="stats.highRiskCount" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="节省时间" :value="stats.timeSaved" suffix="分钟" />
        </el-col>
      </el-row>

      <el-button type="primary" size="large" @click="$router.push('/workspace/upload')" style="margin-top: 40px">
        上传合同
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const stats = reactive({
  contractCount: 0,
  highRiskCount: 0,
  timeSaved: 0
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.description {
  color: #666;
  margin-top: 16px;
  line-height: 1.6;
}
</style>
