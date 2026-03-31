<template>
  <div class="landing">
    <header class="header">
      <h1>法务 AI SaaS</h1>
      <p class="subtitle">智能合同审查，让法律服务触手可及</p>
      <el-button type="primary" size="large" @click="$router.push('/login')">
        立即体验
      </el-button>
    </header>

    <section class="features">
      <el-row :gutter="24">
        <el-col :span="8" v-for="feature in features" :key="feature.title">
          <el-card class="feature-card">
            <div class="feature-icon">{{ feature.icon }}</div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </el-card>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<script setup>
const features = [
  {
    icon: '⚡',
    title: '快速审查',
    description: '30 秒内完成合同审查，输出专业报告'
  },
  {
    icon: '🔒',
    title: '可信赖',
    description: 'RAG + 引用溯源，每条建议都有法条依据'
  },
  {
    icon: '💰',
    title: '可负担',
    description: '¥299 起/月，仅为传统法律服务的 1/10'
  }
]
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 60px;
}

.header h1 {
  font-size: 48px;
  margin-bottom: 16px;
}

.subtitle {
  font-size: 20px;
  opacity: 0.9;
  margin-bottom: 32px;
}

.features {
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  text-align: center;
  padding: 40px 20px;
  margin-bottom: 24px;
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 20px;
  margin-bottom: 12px;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}
</style>
