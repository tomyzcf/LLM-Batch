// API服务类
class ApiService {
  constructor() {
    this.baseURL = 'http://localhost:3001'
    this.ws = null
    this.eventListeners = {}
  }

  // 事件监听器
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = []
    }
    this.eventListeners[event].push(callback)
  }

  // 触发事件
  emit(event, data) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(callback => callback(data))
    }
  }

  // WebSocket连接
  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket('ws://localhost:3001/ws')
        
        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.emit(data.type, data)
          } catch (e) {
            console.error('WebSocket消息解析失败:', e)
          }
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          reject(error)
        }
        
        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭')
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  // 文件上传
  async uploadFile(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${this.baseURL}/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const result = await response.json()
        return { success: true, file: result }
      } else {
        throw new Error('上传失败')
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  // 生成配置文件
  async generateConfig(apiConfig, promptConfig) {
    try {
      const response = await fetch(`${this.baseURL}/generate-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ apiConfig, promptConfig })
      })
      
      if (response.ok) {
        const result = await response.json()
        return { success: true, ...result }
      } else {
        throw new Error('配置生成失败')
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  // 执行任务
  async executeTask(taskParams) {
    try {
      const response = await fetch(`${this.baseURL}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskParams)
      })
      
      if (response.ok) {
        const result = await response.json()
        return { success: true, ...result }
      } else {
        throw new Error('任务执行失败')
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  // 下载结果
  downloadResult(filename) {
    const link = document.createElement('a')
    link.href = `${this.baseURL}/download/${filename}`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 测试API连接
  async testConnection(apiConfig) {
    try {
      const response = await fetch(`${this.baseURL}/test-api`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiConfig)
      })
      
      if (response.ok) {
        const result = await response.json()
        return { success: true, ...result }
      } else {
        throw new Error('API测试失败')
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
}

// 创建单例实例
const apiService = new ApiService()

export default apiService 