import spawn from 'cross-spawn'
import path from 'path'
import fs from 'fs/promises'
import YAML from 'yaml'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

class PythonRunner {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '../..')
    this.tempDir = path.join(__dirname, '../temp')
    this.configDir = path.join(this.tempDir, 'configs')
    this.promptDir = path.join(this.tempDir, 'prompts')
    this.outputDir = path.join(this.tempDir, 'outputs')
    
    this.currentProcess = null
    this.listeners = new Map()
  }

  // 初始化目录
  async initDirectories() {
    const dirs = [this.tempDir, this.configDir, this.promptDir, this.outputDir]
    for (const dir of dirs) {
      await fs.mkdir(dir, { recursive: true })
    }
  }

  // 生成API配置文件
  async generateApiConfig(apiConfig) {
    await this.initDirectories()
    
    const configData = {
      api_type: apiConfig.api_type,
      api_url: apiConfig.api_url,
      api_key: apiConfig.api_key
    }

    if (apiConfig.api_type === 'llm_compatible') {
      configData.model = apiConfig.model
    } else if (apiConfig.api_type === 'dashscope_agent') {
      configData.app_id = apiConfig.app_id
    }

    const configPath = path.join(this.configDir, 'api_config.yaml')
    const yamlContent = YAML.stringify(configData)
    
    await fs.writeFile(configPath, yamlContent, 'utf8')
    return configPath
  }

  // 生成提示词文件
  async generatePromptFile(promptConfig) {
    await this.initDirectories()
    
    const promptData = {
      system: promptConfig.system || '',
      task: promptConfig.task || '',
      output: promptConfig.output || '',
      variables: promptConfig.variables || '',
      examples: promptConfig.examples || ''
    }

    const promptPath = path.join(this.promptDir, 'prompt.json')
    await fs.writeFile(promptPath, JSON.stringify(promptData, null, 2), 'utf8')
    
    return promptPath
  }

  // 执行Python脚本
  async executeScript(params) {
    const { inputFile, configPath, promptPath, fields, startPos, endPos } = params
    
    // 构建命令参数
    const args = [
      path.join(this.projectRoot, 'main.py'),
      '--input', inputFile,
      '--config', configPath,
      '--prompt', promptPath,
      '--output', this.outputDir
    ]

    // 添加字段选择参数
    if (fields && fields.length > 0) {
      args.push('--fields', fields.join(','))
    }

    // 添加行范围参数
    if (startPos) {
      args.push('--start', startPos.toString())
    }
    if (endPos) {
      args.push('--end', endPos.toString())
    }

    return new Promise((resolve, reject) => {
      try {
        // 启动Python进程
        this.currentProcess = spawn('python', args, {
          cwd: this.projectRoot,
          stdio: ['pipe', 'pipe', 'pipe'],
          env: { ...process.env, PYTHONUNBUFFERED: '1' }
        })

        let outputBuffer = ''
        let errorBuffer = ''

        // 处理标准输出
        this.currentProcess.stdout.on('data', (data) => {
          const text = data.toString()
          outputBuffer += text
          
          // 解析进度信息
          const lines = text.split('\n')
          for (const line of lines) {
            if (line.trim()) {
              this.parseOutputLine(line.trim())
            }
          }
        })

        // 处理错误输出
        this.currentProcess.stderr.on('data', (data) => {
          const text = data.toString()
          errorBuffer += text
          
          this.emit('error', {
            message: text.trim(),
            type: 'stderr'
          })
        })

        // 处理进程退出
        this.currentProcess.on('close', (code) => {
          this.currentProcess = null
          
          if (code === 0) {
            // 查找输出文件
            this.findOutputFile()
              .then(outputFile => {
                this.emit('completed', {
                  message: '任务执行完成',
                  resultFile: outputFile
                })
                resolve({
                  success: true,
                  outputFile,
                  output: outputBuffer
                })
              })
              .catch(error => {
                this.emit('failed', {
                  message: `无法找到输出文件: ${error.message}`
                })
                reject(error)
              })
          } else {
            const errorMsg = `Python脚本执行失败，退出码: ${code}`
            this.emit('failed', {
              message: errorMsg,
              detail: errorBuffer
            })
            reject(new Error(errorMsg))
          }
        })

        // 处理进程错误
        this.currentProcess.on('error', (error) => {
          this.currentProcess = null
          this.emit('failed', {
            message: `进程启动失败: ${error.message}`
          })
          reject(error)
        })

        // 发送启动成功事件
        this.emit('log', {
          message: '任务已启动，正在处理数据...'
        })

      } catch (error) {
        reject(error)
      }
    })
  }

  // 解析输出行
  parseOutputLine(line) {
    try {
      // 尝试解析JSON格式的进度信息
      if (line.startsWith('{') && line.endsWith('}')) {
        const data = JSON.parse(line)
        
        if (data.type === 'progress') {
          this.emit('progress', {
            processed: data.processed,
            total: data.total,
            progress: Math.round((data.processed / data.total) * 100)
          })
        } else if (data.type === 'log') {
          this.emit('log', {
            message: data.message
          })
        } else if (data.type === 'error') {
          this.emit('error', {
            message: data.message,
            detail: data.detail
          })
        }
      } else {
        // 普通日志信息
        this.emit('log', {
          message: line
        })
      }
    } catch (error) {
      // 如果不是JSON格式，作为普通日志处理
      this.emit('log', {
        message: line
      })
    }
  }

  // 查找输出文件
  async findOutputFile() {
    try {
      const files = await fs.readdir(this.outputDir)
      const outputFiles = files.filter(file => 
        file.endsWith('.csv') || 
        file.endsWith('.xlsx') || 
        file.endsWith('.json')
      )
      
      if (outputFiles.length === 0) {
        throw new Error('没有找到输出文件')
      }
      
      // 返回最新的文件
      const filePaths = await Promise.all(
        outputFiles.map(async file => {
          const filePath = path.join(this.outputDir, file)
          const stats = await fs.stat(filePath)
          return { path: filePath, mtime: stats.mtime }
        })
      )
      
      filePaths.sort((a, b) => b.mtime - a.mtime)
      return filePaths[0].path
      
    } catch (error) {
      throw new Error(`查找输出文件失败: ${error.message}`)
    }
  }

  // 停止当前任务
  stopTask() {
    if (this.currentProcess) {
      this.currentProcess.kill('SIGTERM')
      this.currentProcess = null
      
      this.emit('log', {
        message: '任务已停止'
      })
      
      return true
    }
    return false
  }

  // 检查Python环境
  async checkPythonEnvironment() {
    return new Promise((resolve) => {
      const pythonProcess = spawn('python', ['--version'], {
        stdio: ['pipe', 'pipe', 'pipe']
      })

      let output = ''
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString()
      })

      pythonProcess.stderr.on('data', (data) => {
        output += data.toString()
      })

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({
            available: true,
            version: output.trim()
          })
        } else {
          resolve({
            available: false,
            error: 'Python未安装或不在PATH中'
          })
        }
      })

      pythonProcess.on('error', () => {
        resolve({
          available: false,
          error: 'Python未安装或不在PATH中'
        })
      })
    })
  }

  // 事件监听
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  // 移除事件监听
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  // 触发事件
  emit(event, data) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      callbacks.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('事件回调执行错误:', error)
        }
      })
    }
  }

  // 清理资源
  cleanup() {
    this.stopTask()
    this.listeners.clear()
  }
}

export default PythonRunner 