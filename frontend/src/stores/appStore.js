import { create } from 'zustand'

const useAppStore = create((set, get) => ({
  // 步骤控制
  currentStep: 1,
  setCurrentStep: (step) => set({ currentStep: step }),
  
  // API配置
  apiConfig: {
    api_type: 'llm',
    provider: 'deepseek',
    api_url: 'https://api.deepseek.com/v1/chat/completions',
    api_key: '',
    model: 'deepseek-chat',
    app_id: '' // 用于阿里百炼Agent
  },
  setApiConfig: (config) => set((state) => ({ 
    apiConfig: { ...state.apiConfig, ...config } 
  })),
  
  // 文件数据
  fileData: {
    fileName: '',
    fileSize: 0,
    totalRows: 0,
    totalColumns: 0,
    previewData: [],
    headers: [],
    fileType: '', // csv, excel, json
    encoding: 'utf-8'
  },
  setFileData: (data) => set((state) => ({ 
    fileData: { ...state.fileData, ...data } 
  })),
  resetFileData: () => set({
    fileData: {
      fileName: '',
      fileSize: 0,
      totalRows: 0,
      totalColumns: 0,
      previewData: [],
      headers: [],
      fileType: '',
      encoding: 'utf-8'
    }
  }),
  
  // 字段选择
  fieldSelection: {
    selectedFields: [], // 选中的字段索引数组
    fieldRange: '', // 字段范围字符串，如 "2-5"
    startRow: 1,
    endRow: null, // null表示处理到最后一行
    useFieldRange: false // 是否使用字段范围而不是单独选择
  },
  setFieldSelection: (selection) => set((state) => ({ 
    fieldSelection: { ...state.fieldSelection, ...selection } 
  })),
  
  // 提示词配置
  promptConfig: {
    format: 'json', // json 或 txt
    content: {
      system: '',
      task: '',
      output: '',
      variables: {},
      examples: ''
    },
    textContent: '', // 用于txt格式
    selectedTemplate: null
  },
  setPromptConfig: (config) => set((state) => ({ 
    promptConfig: { ...state.promptConfig, ...config } 
  })),
  
  // 任务状态
  taskStatus: {
    isRunning: false,
    isCompleted: false,
    progress: 0,
    processedCount: 0,
    totalCount: 0,
    currentStatus: 'idle', // idle, running, completed, error, paused
    startTime: null,
    endTime: null,
    speed: 0, // 处理速度（条/分钟）
    estimatedTimeLeft: 0, // 预估剩余时间（秒）
    logs: [],
    errorLogs: [],
    successCount: 0,
    errorCount: 0,
    resultFilePath: '',
    errorDetails: null
  },
  setTaskStatus: (status) => set((state) => ({ 
    taskStatus: { ...state.taskStatus, ...status } 
  })),
  addTaskLog: (log) => set((state) => ({ 
    taskStatus: { 
      ...state.taskStatus, 
      logs: [...state.taskStatus.logs, {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        message: log.message,
        type: log.type || 'info', // info, success, warning, error
        ...log
      }].slice(-1000) // 保持最新1000条日志
    } 
  })),
  addErrorLog: (error) => set((state) => ({ 
    taskStatus: { 
      ...state.taskStatus, 
      errorLogs: [...state.taskStatus.errorLogs, {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        ...error
      }].slice(-100) // 保持最新100条错误日志
    } 
  })),
  resetTaskStatus: () => set({
    taskStatus: {
      isRunning: false,
      isCompleted: false,
      progress: 0,
      processedCount: 0,
      totalCount: 0,
      currentStatus: 'idle',
      startTime: null,
      endTime: null,
      speed: 0,
      estimatedTimeLeft: 0,
      logs: [],
      errorLogs: [],
      successCount: 0,
      errorCount: 0,
      resultFilePath: '',
      errorDetails: null
    }
  }),
  
  // 全局设置
  settings: {
    theme: 'light',
    language: 'zh-CN',
    autoSave: true,
    maxFileSize: 50 * 1024 * 1024, // 50MB
    concurrentLimit: 5,
    retryTimes: 3
  },
  setSettings: (settings) => set((state) => ({ 
    settings: { ...state.settings, ...settings } 
  })),
  
  // 通用操作
  reset: () => set({
    currentStep: 1,
    apiConfig: {
      api_type: 'llm',
      provider: 'deepseek',
      api_url: 'https://api.deepseek.com/v1/chat/completions',
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
      fileType: '',
      encoding: 'utf-8'
    },
    fieldSelection: {
      selectedFields: [],
      fieldRange: '',
      startRow: 1,
      endRow: null,
      useFieldRange: false
    },
    promptConfig: {
      format: 'json',
      content: {
        system: '',
        task: '',
        output: '',
        variables: {},
        examples: ''
      },
      textContent: '',
      selectedTemplate: null
    },
    taskStatus: {
      isRunning: false,
      isCompleted: false,
      progress: 0,
      processedCount: 0,
      totalCount: 0,
      currentStatus: 'idle',
      startTime: null,
      endTime: null,
      speed: 0,
      estimatedTimeLeft: 0,
      logs: [],
      errorLogs: [],
      successCount: 0,
      errorCount: 0,
      resultFilePath: '',
      errorDetails: null
    }
  }),
  
  // 验证方法
  validateCurrentStep: () => {
    const state = get()
    switch (state.currentStep) {
      case 1: // API配置验证
        return !!(state.apiConfig.api_url && state.apiConfig.api_key && 
          (state.apiConfig.model || state.apiConfig.app_id))
      case 2: // 文件数据验证
        return !!(state.fileData.fileName && state.fileData.headers.length > 0)
      case 3: // 字段选择验证
        if (state.fieldSelection.useFieldRange) {
          // 使用字段范围时验证范围格式
          return !!state.fieldSelection.fieldRange && state.fieldSelection.fieldRange.trim().length > 0
        } else {
          // 使用单独选择时验证是否选择了字段
          return state.fieldSelection.selectedFields.length > 0
        }
      case 4: // 提示词验证
        return state.promptConfig.format === 'json'
          ? !!(state.promptConfig.content.system && state.promptConfig.content.task && state.promptConfig.content.output)
          : !!state.promptConfig.textContent
      default:
        return true
    }
  },
  
  // 获取处理配置摘要
  getConfigSummary: () => {
    const state = get()
    return {
      api: {
        type: state.apiConfig.api_type,
        url: state.apiConfig.api_url,
        model: state.apiConfig.model || state.apiConfig.app_id
      },
      file: {
        name: state.fileData.fileName,
        size: `${(state.fileData.fileSize / (1024 * 1024)).toFixed(2)} MB`,
        rows: state.fileData.totalRows,
        columns: state.fileData.totalColumns
      },
      fields: {
        selection: state.fieldSelection.useFieldRange 
          ? state.fieldSelection.fieldRange 
          : state.fieldSelection.selectedFields.join(', '),
        range: `${state.fieldSelection.startRow} - ${state.fieldSelection.endRow || '最后一行'}`
      },
      prompt: {
        format: state.promptConfig.format,
        template: state.promptConfig.selectedTemplate || '自定义'
      }
    }
  }
}))

export default useAppStore 