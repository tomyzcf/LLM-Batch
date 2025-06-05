import { create } from 'zustand'
import apiService from '../utils/api'

const useAppStore = create((set, get) => ({
  // 当前步骤
  currentStep: 1,
  
  // API配置
  apiConfig: {
    api_type: 'llm', // 默认选择LLM类型
    provider: 'deepseek', // 默认选择DeepSeek
    api_url: 'https://api.deepseek.com',
    api_key: '',
    model: 'deepseek-chat', // 默认选择V3模型
    app_id: '' // 阿里百炼Agent专用
  },
  
  // 文件数据
  fileData: {
    fileName: '',
    fileSize: 0,
    totalRows: 0,
    totalColumns: 0,
    previewData: [],
    headers: [],
    uploadedFile: null // 后端返回的文件信息
  },
  
  // 字段选择
  fieldSelection: {
    selectedFields: [],
    selectedFieldNames: [],
    startRow: 1,
    endRow: null
  },
  
  // 提示词配置
  promptConfig: {
    system: '',
    task: '',
    output: '',
    variables: '',
    examples: ''
  },
  
  // 任务状态
  taskStatus: {
    isRunning: false,
    isCompleted: false,
    currentStatus: 'idle', // idle/running/completed/paused/stopped/error
    startTime: null,
    endTime: null,
    totalCount: 0,
    processedCount: 0,
    successCount: 0,
    errorCount: 0,
    progress: 0,
    speed: 0,
    estimatedTimeLeft: 0,
    logs: [],
    errorLogs: [],
    resultFilePath: null
  },

  // WebSocket连接状态
  wsConnected: false,

  // Actions
  setCurrentStep: (step) => {
    set({ currentStep: Math.max(1, Math.min(step, 4)) })
  },
  
  setApiConfig: (config) => set((state) => ({
    apiConfig: { ...state.apiConfig, ...config }
  })),
  
  setFileData: (data) => set((state) => ({
    fileData: { ...state.fileData, ...data }
  })),
  
  setFieldSelection: (selection) => set((state) => ({
    fieldSelection: { ...state.fieldSelection, ...selection }
  })),
  
  setPromptConfig: (config) => set((state) => ({
    promptConfig: { ...state.promptConfig, ...config }
  })),
  
  setTaskStatus: (status) => set((state) => ({
    taskStatus: { ...state.taskStatus, ...status }
  })),

  // 添加任务日志
  addTaskLog: (log) => set((state) => ({
    taskStatus: {
      ...state.taskStatus,
      logs: [...state.taskStatus.logs, {
        id: Date.now() + Math.random(),
        timestamp: new Date().toLocaleTimeString(),
        ...log
      }]
    }
  })),

  // 添加错误日志
  addErrorLog: (error) => set((state) => ({
    taskStatus: {
      ...state.taskStatus,
      errorLogs: [...state.taskStatus.errorLogs, {
        id: Date.now() + Math.random(),
        timestamp: new Date().toLocaleTimeString(),
        ...error
      }]
    }
  })),

  // 初始化WebSocket连接
  initWebSocket: async () => {
    try {
      await apiService.connectWebSocket()
      set({ wsConnected: true })

      // 监听WebSocket事件
      apiService.on('log', (data) => {
        get().addTaskLog({
          message: data.message,
          type: 'info'
        })
      })

      apiService.on('error', (data) => {
        get().addErrorLog({
          message: data.message,
          type: 'error'
        })
      })

      apiService.on('progress', (data) => {
        set((state) => ({
          taskStatus: {
            ...state.taskStatus,
            processedCount: data.processed,
            totalCount: data.total,
            progress: data.progress
          }
        }))
      })

      apiService.on('completed', (data) => {
        set((state) => ({
          taskStatus: {
            ...state.taskStatus,
            isRunning: false,
            isCompleted: true,
            currentStatus: 'completed',
            endTime: new Date(),
            resultFilePath: data.resultFile
          }
        }))
        
        get().addTaskLog({
          message: data.message,
          type: 'success'
        })
      })

      apiService.on('failed', (data) => {
        set((state) => ({
          taskStatus: {
            ...state.taskStatus,
            isRunning: false,
            currentStatus: 'error',
            endTime: new Date()
          }
        }))
        
        get().addErrorLog({
          message: data.message,
          type: 'error'
        })
      })

    } catch (error) {
      console.error('WebSocket连接失败:', error)
      set({ wsConnected: false })
    }
  },

  // 上传文件
  uploadFile: async (file) => {
    try {
      const result = await apiService.uploadFile(file)
      
      if (result.success) {
        set((state) => ({
          fileData: {
            ...state.fileData,
            uploadedFile: result.file
          }
        }))
        return result.file
      } else {
        throw new Error(result.error || '上传失败')
      }
    } catch (error) {
      console.error('文件上传失败:', error)
      throw error
    }
  },

  // 执行批处理任务
  executeTask: async () => {
    const state = get()
    
    try {
      // 确保WebSocket连接
      if (!state.wsConnected) {
        await state.initWebSocket()
      }

      // 生成配置文件
      const configResult = await apiService.generateConfig(
        state.apiConfig,
        state.promptConfig
      )

      if (!configResult.success) {
        throw new Error('配置文件生成失败')
      }

      // 准备任务参数
      const taskParams = {
        inputFile: state.fileData.uploadedFile.path,
        configPath: configResult.configPath,
        promptPath: configResult.promptPath,
        fields: state.fieldSelection.selectedFields,
        startPos: state.fieldSelection.startRow,
        endPos: state.fieldSelection.endRow
      }

      // 启动任务
      const taskResult = await apiService.executeTask(taskParams)

      if (taskResult.success) {
        // 更新任务状态
        set((state) => ({
          taskStatus: {
            ...state.taskStatus,
            isRunning: true,
            isCompleted: false,
            currentStatus: 'running',
            startTime: new Date(),
            totalCount: state.fieldSelection.endRow - state.fieldSelection.startRow + 1,
            processedCount: 0,
            progress: 0,
            logs: [],
            errorLogs: []
          }
        }))

        get().addTaskLog({
          message: '任务已启动，正在处理数据...',
          type: 'info'
        })

        return taskResult
      } else {
        throw new Error(taskResult.error || '任务启动失败')
      }
    } catch (error) {
      console.error('任务执行失败:', error)
      
      set((state) => ({
        taskStatus: {
          ...state.taskStatus,
          isRunning: false,
          currentStatus: 'error'
        }
      }))

      get().addErrorLog({
        message: `任务执行失败: ${error.message}`,
        type: 'error'
      })

      throw error
    }
  },

  // 下载结果文件
  downloadResult: () => {
    const state = get()
    if (state.taskStatus.resultFilePath) {
      const filename = state.taskStatus.resultFilePath.split('/').pop()
      apiService.downloadResult(filename)
    }
  },
  
  // 验证当前步骤
  validateCurrentStep: () => {
    const state = get()
    const { currentStep } = state
    
    const stepValidations = {
      1: () => {
        // API配置验证
        return state.apiConfig.provider && 
               state.apiConfig.api_url && 
               state.apiConfig.api_key
      },
      2: () => {
        // 数据准备验证（文件上传 + 字段选择）
        return state.fileData.fileName && 
               state.fieldSelection.selectedFields.length > 0 &&
               state.fieldSelection.startRow &&
               state.fieldSelection.endRow
      },
      3: () => {
        // 提示词配置验证
        return state.promptConfig.template && 
               state.promptConfig.format
      },
      4: () => {
        // 任务执行与结果验证（始终返回true，因为是最后一步）
        return true
      }
    }
    
    return stepValidations[currentStep] ? stepValidations[currentStep]() : false
  },
  
  // 获取配置摘要
  getConfigSummary: () => {
    const state = get()
    
    return {
      api: {
        type: state.apiConfig.api_type === 'llm' ? '通用LLM' : '阿里百炼Agent',
        url: state.apiConfig.api_url,
        model: state.apiConfig.model || state.apiConfig.app_id
      },
      file: {
        name: state.fileData.fileName,
        size: state.fileData.fileSize > 1024 * 1024 
          ? `${(state.fileData.fileSize / 1024 / 1024).toFixed(1)}MB`
          : `${(state.fileData.fileSize / 1024).toFixed(1)}KB`,
        rows: state.fileData.totalRows,
        columns: state.fileData.totalColumns
      },
      fields: {
        selection: state.fieldSelection.selectedFieldNames.length > 0 
          ? state.fieldSelection.selectedFieldNames.join(', ')
          : `第${state.fieldSelection.selectedFields.join(', ')}列`,
        range: state.fieldSelection.endRow 
          ? `${state.fieldSelection.startRow}-${state.fieldSelection.endRow}`
          : `${state.fieldSelection.startRow}-${state.fileData.totalRows}`
      },
      prompt: {
        format: 'JSON',
        template: state.promptConfig.system ? '自定义模板' : '默认模板'
      }
    }
  },
  
  // 重置所有状态
  reset: () => set({
    currentStep: 1,
    apiConfig: {
      api_type: 'llm',
      provider: 'deepseek',
      api_url: 'https://api.deepseek.com',
      api_key: '',
      model: 'deepseek-chat',
      app_id: ''
    },
    fileData: {
      fileName: '',
      fileSize: 0,
      totalRows: 0,
      totalColumns: 0,
      previewData: [],
      headers: [],
      uploadedFile: null
    },
    fieldSelection: {
      selectedFields: [],
      selectedFieldNames: [],
      startRow: 1,
      endRow: null
    },
    promptConfig: {
      system: '',
      task: '',
      output: '',
      variables: '',
      examples: ''
    },
    taskStatus: {
      isRunning: false,
      isCompleted: false,
      currentStatus: 'idle',
      startTime: null,
      endTime: null,
      totalCount: 0,
      processedCount: 0,
      successCount: 0,
      errorCount: 0,
      progress: 0,
      speed: 0,
      estimatedTimeLeft: 0,
      logs: [],
      errorLogs: [],
      resultFilePath: null
    }
  })
}))

export default useAppStore 