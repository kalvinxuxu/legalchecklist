<template>
  <div class="upload">
    <el-card>
      <h2>上传合同</h2>

      <el-form :model="form" label-width="100px">
        <el-form-item label="工作区">
          <el-select v-model="form.workspaceId" placeholder="选择工作区" style="width: 100%">
            <el-option
              v-for="ws in workspaces"
              :key="ws.id"
              :label="ws.name"
              :value="ws.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="合同类型">
          <el-select v-model="form.contractType" placeholder="选择合同类型" style="width: 100%">
            <el-option label="NDA (保密协议)" value="NDA" />
            <el-option label="劳动合同" value="劳动合同" />
            <el-option label="采购合同" value="采购合同" />
            <el-option label="销售合同" value="销售合同" />
            <el-option label="服务合同" value="服务合同" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>

        <el-form-item label="合同文件" required>
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            accept=".pdf,.doc,.docx"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF/Word 格式，最大 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            开始审查
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const uploadRef = ref(null)
const loading = ref(false)

const form = reactive({
  workspaceId: '',
  contractType: '',
  file: null
})

const workspaces = ref([])

onMounted(async () => {
  // 获取工作区列表
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/v1/workspaces/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    workspaces.value = response.data
    if (workspaces.value.length > 0) {
      form.workspaceId = workspaces.value[0].id
    }
  } catch (error) {
    ElMessage.error('获取工作区失败')
  }
})

const handleFileChange = (file) => {
  form.file = file.raw
}

const handleSubmit = async () => {
  if (!form.file) {
    ElMessage.warning('请选择合同文件')
    return
  }

  loading.value = true

  try {
    const formData = new FormData()
    formData.append('file', form.file)
    formData.append('workspace_id', form.workspaceId)
    formData.append('contract_type', form.contractType)

    const token = localStorage.getItem('token')
    const response = await axios.post('/api/v1/contracts/upload', formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })

    ElMessage.success('上传成功，开始审查...')
    // 跳转到审查结果页
    setTimeout(() => {
      window.location.href = `/workspace/review/${response.data.id}`
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload {
  padding: 20px;
}

.el-icon--upload {
  font-size: 67px;
  color: #8c939d;
  margin: 40px 0 16px;
}
</style>
