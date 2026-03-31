<template>
  <div class="workspace">
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">法务 AI</div>
        <el-menu :default-active="activeMenu">
          <el-menu-item index="dashboard" @click="activeMenu = 'dashboard'">
            工作台
          </el-menu-item>
          <el-menu-item index="contracts" @click="activeMenu = 'contracts'">
            合同列表
          </el-menu-item>
          <el-menu-item index="upload" @click="activeMenu = 'upload'">
            上传合同
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <span>欢迎使用法务 AI SaaS</span>
          <el-button @click="handleLogout">退出登录</el-button>
        </el-header>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeMenu = ref('dashboard')

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.workspace {
  height: 100vh;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e0e0e0;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: #667eea;
  border-bottom: 1px solid #e0e0e0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}
</style>
