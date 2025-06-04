import express from 'express'
import cors from 'cors'
import multer from 'multer'
import { WebSocketServer } from 'ws'
import { createServer } from 'http'
import path from 'path'
import fs from 'fs/promises'
import { fileURLToPath } from 'url'
import YAML from 'yaml'
import spawn from 'cross-spawn'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const server = createServer(app)
const wss = new WebSocketServer({ server })

// 中间件
app.use(cors())
app.use(express.json())
app.use(express.static('dist'))

// 文件上传配置
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../temp/uploads')
    try {
      await fs.mkdir(uploadDir, { recursive: true })
      cb(null, uploadDir)
    } catch (error) {
      cb(error)
    }
  },
  filename: (req, file, cb) => {
    // 保持原文件名，添加时间戳避免冲突
    const timestamp = Date.now()
    const ext = path.extname(file.originalname)
    const name = path.basename(file.originalname, ext)
    cb(null, `${name}_${timestamp}${ext}`)
  }
})

const upload = multer({ 
  storage,
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB限制
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['.csv', '.xlsx', '.xls', '.json']
    const ext = path.extname(file.originalname).toLowerCase()
    if (allowedTypes.includes(ext)) {
      cb(null, true)
    } else {
      cb(new Error('不支持的文件格式'))
    }
  }
})

// WebSocket连接管理
const clients = new Set()

wss.on('connection', (ws) => {
  clients.add(ws)
  console.log('WebSocket客户端连接')
  
  ws.on('close', () => {
    clients.delete(ws)
    console.log('WebSocket客户端断开')
  })
})

// 广播消息给所有客户端
function broadcast(message) {
  const data = JSON.stringify(message)
  clients.forEach(client => {
    if (client.readyState === client.OPEN) {
      client.send(data)
    }
  })
}

// API路由

// 文件上传
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: '没有上传文件' })
    }

    const fileInfo = {
      filename: req.file.filename,
      originalname: req.file.originalname,
      size: req.file.size,
      path: req.file.path,
      mimetype: req.file.mimetype
    }

    res.json({
      success: true,
      file: fileInfo
    })
  } catch (error) {
    console.error('文件上传错误:', error)
    res.status(500).json({ error: error.message })
  }
})

// 生成配置文件
app.post('/api/generate-config', async (req, res) => {
  try {
    const { apiConfig, promptConfig } = req.body

    // 创建配置目录
    const configDir = path.join(__dirname, '../../temp/config')
    await fs.mkdir(configDir, { recursive: true })

    // 生成API配置文件 (YAML格式)
    const yamlConfig = {
      default_provider: apiConfig.api_type === 'llm_compatible' ? 'openai_compatible' : 'dashscope_agent',
      providers: {}
    }

    if (apiConfig.api_type === 'llm_compatible') {
      yamlConfig.providers.openai_compatible = {
        api_url: apiConfig.api_url,
        api_key: apiConfig.api_key,
        model: apiConfig.model
      }
    } else {
      yamlConfig.providers.dashscope_agent = {
        api_url: apiConfig.api_url,
        api_key: apiConfig.api_key,
        app_id: apiConfig.app_id
      }
    }

    const configPath = path.join(configDir, 'config.yaml')
    await fs.writeFile(configPath, YAML.stringify(yamlConfig))

    // 生成提示词文件
    const promptPath = path.join(configDir, 'prompt.json')
    await fs.writeFile(promptPath, JSON.stringify(promptConfig, null, 2))

    res.json({
      success: true,
      configPath,
      promptPath
    })
  } catch (error) {
    console.error('配置生成错误:', error)
    res.status(500).json({ error: error.message })
  }
})

// 执行批处理任务
app.post('/api/execute-task', async (req, res) => {
  try {
    const { 
      inputFile, 
      configPath, 
      promptPath, 
      fields, 
      startPos, 
      endPos 
    } = req.body

    // 构建Python命令
    const pythonScript = path.join(__dirname, '../../main.py')
    const args = [
      pythonScript,
      inputFile,
      promptPath
    ]

    // 添加可选参数
    if (fields && fields.length > 0) {
      args.push('--fields', fields.join(','))
    }
    if (startPos) {
      args.push('--start-pos', startPos.toString())
    }
    if (endPos) {
      args.push('--end-pos', endPos.toString())
    }

    console.log('执行Python命令:', 'python', args.join(' '))

    // 启动Python进程
    const pythonProcess = spawn('python', args, {
      cwd: path.join(__dirname, '../..'),
      env: { ...process.env, PYTHONPATH: path.join(__dirname, '../..') }
    })

    let outputBuffer = ''
    let errorBuffer = ''

    // 处理Python输出
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString()
      outputBuffer += output
      
      // 解析进度信息并广播
      const lines = output.split('\n')
      lines.forEach(line => {
        if (line.trim()) {
          console.log('Python输出:', line)
          broadcast({
            type: 'log',
            message: line.trim(),
            timestamp: new Date().toISOString()
          })
          
          // 解析进度信息
          const progressMatch = line.match(/已处理.*?(\d+)\/(\d+)/)
          if (progressMatch) {
            const processed = parseInt(progressMatch[1])
            const total = parseInt(progressMatch[2])
            broadcast({
              type: 'progress',
              processed,
              total,
              progress: Math.round((processed / total) * 100)
            })
          }
        }
      })
    })

    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString()
      errorBuffer += error
      console.error('Python错误:', error)
      broadcast({
        type: 'error',
        message: error.trim(),
        timestamp: new Date().toISOString()
      })
    })

    pythonProcess.on('close', (code) => {
      console.log(`Python进程退出，代码: ${code}`)
      
      if (code === 0) {
        // 查找输出文件
        const outputDir = path.join(__dirname, '../../outputData')
        fs.readdir(outputDir)
          .then(files => {
            const resultFile = files
              .filter(f => f.endsWith('.xlsx') || f.endsWith('.csv'))
              .sort((a, b) => {
                // 按修改时间排序，最新的在前
                const statA = fs.statSync(path.join(outputDir, a))
                const statB = fs.statSync(path.join(outputDir, b))
                return statB.mtime - statA.mtime
              })[0]
            
            broadcast({
              type: 'completed',
              resultFile: resultFile ? path.join(outputDir, resultFile) : null,
              message: '任务执行完成'
            })
          })
          .catch(err => {
            console.error('查找结果文件错误:', err)
            broadcast({
              type: 'completed',
              resultFile: null,
              message: '任务完成，但未找到结果文件'
            })
          })
      } else {
        broadcast({
          type: 'failed',
          message: `任务执行失败，退出代码: ${code}`,
          error: errorBuffer
        })
      }
    })

    pythonProcess.on('error', (error) => {
      console.error('启动Python进程失败:', error)
      broadcast({
        type: 'failed',
        message: '启动Python进程失败: ' + error.message
      })
    })

    res.json({
      success: true,
      message: '任务已启动',
      pid: pythonProcess.pid
    })

  } catch (error) {
    console.error('任务执行错误:', error)
    res.status(500).json({ error: error.message })
  }
})

// 下载结果文件
app.get('/api/download/:filename', async (req, res) => {
  try {
    const filename = req.params.filename
    const filePath = path.join(__dirname, '../../outputData', filename)
    
    // 检查文件是否存在
    await fs.access(filePath)
    
    res.download(filePath, filename)
  } catch (error) {
    console.error('文件下载错误:', error)
    res.status(404).json({ error: '文件不存在' })
  }
})

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// 启动服务器
const PORT = process.env.PORT || 3001

server.listen(PORT, () => {
  console.log(`后端服务器启动在端口 ${PORT}`)
  console.log(`WebSocket服务器启动在端口 ${PORT}`)
})

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('收到SIGTERM信号，正在关闭服务器...')
  server.close(() => {
    console.log('服务器已关闭')
    process.exit(0)
  })
})

process.on('SIGINT', () => {
  console.log('收到SIGINT信号，正在关闭服务器...')
  server.close(() => {
    console.log('服务器已关闭')
    process.exit(0)
  })
}) 