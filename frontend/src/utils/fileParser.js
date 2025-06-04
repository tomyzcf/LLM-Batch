import Papa from 'papaparse'
import * as XLSX from 'xlsx'

// 文件大小限制 (50MB)
const MAX_FILE_SIZE = 50 * 1024 * 1024

// 支持的文件类型
const SUPPORTED_TYPES = {
  'text/csv': 'csv',
  'application/vnd.ms-excel': 'excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel',
  'application/json': 'json'
}

// 获取文件扩展名
const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase()
}

// 验证文件
export const validateFile = (file) => {
  const errors = []
  
  // 检查文件大小
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`文件大小超出限制（最大 ${MAX_FILE_SIZE / (1024 * 1024)}MB）`)
  }
  
  // 检查文件类型
  const extension = getFileExtension(file.name)
  const mimeType = file.type
  
  const isValidExtension = ['csv', 'xlsx', 'xls', 'json'].includes(extension)
  const isValidMimeType = Object.keys(SUPPORTED_TYPES).includes(mimeType)
  
  if (!isValidExtension && !isValidMimeType) {
    errors.push('不支持的文件格式。请上传 CSV、Excel 或 JSON 文件')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    fileType: determineFileType(file),
    fileSize: file.size,
    fileName: file.name
  }
}

// 确定文件类型
const determineFileType = (file) => {
  const extension = getFileExtension(file.name)
  const mimeType = file.type
  
  if (extension === 'csv' || mimeType === 'text/csv') {
    return 'csv'
  } else if (['xlsx', 'xls'].includes(extension) || 
             ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(mimeType)) {
    return 'excel'
  } else if (extension === 'json' || mimeType === 'application/json') {
    return 'json'
  }
  
  return 'unknown'
}

// 解析CSV文件
export const parseCSV = (file, options = {}) => {
  return new Promise((resolve, reject) => {
    const config = {
      header: true,
      preview: options.preview || 10, // 预览行数
      encoding: 'utf-8',
      skipEmptyLines: true,
      transformHeader: (header, index) => {
        // 处理空标题
        return header.trim() || `列_${index + 1}`
      },
      complete: (results) => {
        try {
          if (results.errors.length > 0) {
            console.warn('CSV解析警告:', results.errors)
          }
          
          const headers = results.meta.fields || []
          const data = results.data || []
          
          // 过滤掉完全空的行
          const filteredData = data.filter(row => 
            Object.values(row).some(value => value && value.toString().trim())
          )
          
          resolve({
            headers,
            data: filteredData,
            totalRows: filteredData.length,
            totalColumns: headers.length,
            preview: filteredData.slice(0, options.preview || 10),
            parseInfo: {
              delimiter: results.meta.delimiter,
              linebreak: results.meta.linebreak,
              truncated: results.meta.truncated
            },
            errors: results.errors
          })
        } catch (error) {
          reject(new Error(`CSV解析失败: ${error.message}`))
        }
      },
      error: (error) => {
        reject(new Error(`CSV解析错误: ${error.message}`))
      }
    }
    
    Papa.parse(file, config)
  })
}

// 解析Excel文件
export const parseExcel = async (file, options = {}) => {
  try {
    const data = await file.arrayBuffer()
    const workbook = XLSX.read(data, { type: 'array' })
    
    // 获取第一个工作表
    const sheetName = workbook.SheetNames[0]
    const worksheet = workbook.Sheets[sheetName]
    
    if (!worksheet) {
      throw new Error('Excel文件中没有找到工作表')
    }
    
    // 转换为JSON数组
    const jsonData = XLSX.utils.sheet_to_json(worksheet, {
      header: 1, // 使用数组形式
      defval: '', // 空值默认为空字符串
      blankrows: false // 跳过空行
    })
    
    if (jsonData.length === 0) {
      throw new Error('Excel文件为空或没有数据')
    }
    
    // 处理标题行
    const headers = jsonData[0].map((header, index) => {
      return header && header.toString().trim() || `列_${index + 1}`
    })
    
    // 处理数据行
    const dataRows = jsonData.slice(1).map(row => {
      const rowObj = {}
      headers.forEach((header, index) => {
        rowObj[header] = row[index] !== undefined ? row[index].toString() : ''
      })
      return rowObj
    })
    
    // 过滤掉完全空的行
    const filteredData = dataRows.filter(row => 
      Object.values(row).some(value => value && value.toString().trim())
    )
    
    return {
      headers,
      data: filteredData,
      totalRows: filteredData.length,
      totalColumns: headers.length,
      preview: filteredData.slice(0, options.preview || 10),
      parseInfo: {
        sheetName,
        totalSheets: workbook.SheetNames.length,
        sheetNames: workbook.SheetNames
      },
      errors: []
    }
  } catch (error) {
    throw new Error(`Excel解析失败: ${error.message}`)
  }
}

// 解析JSON文件
export const parseJSON = async (file, options = {}) => {
  try {
    const text = await file.text()
    const jsonData = JSON.parse(text)
    
    // 处理不同的JSON结构
    let data = []
    let headers = []
    
    if (Array.isArray(jsonData)) {
      if (jsonData.length === 0) {
        throw new Error('JSON数组为空')
      }
      
      // 从第一个对象提取字段名作为标题
      const firstItem = jsonData[0]
      if (typeof firstItem === 'object' && firstItem !== null) {
        headers = Object.keys(firstItem)
        data = jsonData
      } else {
        // 如果是基本类型数组，创建单列数据
        headers = ['value']
        data = jsonData.map(item => ({ value: item }))
      }
    } else if (typeof jsonData === 'object' && jsonData !== null) {
      // 如果是单个对象，转换为数组
      headers = Object.keys(jsonData)
      data = [jsonData]
    } else {
      throw new Error('不支持的JSON格式')
    }
    
    // 过滤掉无效数据
    const filteredData = data.filter(row => 
      row && typeof row === 'object'
    )
    
    return {
      headers,
      data: filteredData,
      totalRows: filteredData.length,
      totalColumns: headers.length,
      preview: filteredData.slice(0, options.preview || 10),
      parseInfo: {
        originalType: Array.isArray(jsonData) ? 'array' : 'object',
        originalLength: Array.isArray(jsonData) ? jsonData.length : 1
      },
      errors: []
    }
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`JSON格式错误: ${error.message}`)
    }
    throw new Error(`JSON解析失败: ${error.message}`)
  }
}

// 通用文件解析器
export const parseFile = async (file, options = {}) => {
  // 验证文件
  const validation = validateFile(file)
  if (!validation.isValid) {
    throw new Error(validation.errors.join('; '))
  }
  
  const fileType = validation.fileType
  
  try {
    let result
    
    switch (fileType) {
      case 'csv':
        result = await parseCSV(file, options)
        break
      case 'excel':
        result = await parseExcel(file, options)
        break
      case 'json':
        result = await parseJSON(file, options)
        break
      default:
        throw new Error(`不支持的文件类型: ${fileType}`)
    }
    
    return {
      ...result,
      fileType,
      fileName: file.name,
      fileSize: file.size,
      encoding: 'utf-8' // 默认编码
    }
  } catch (error) {
    throw new Error(`文件解析失败: ${error.message}`)
  }
}

// 格式化文件大小
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

// 生成数据摘要
export const generateDataSummary = (data) => {
  if (!data || !data.headers || !Array.isArray(data.data)) {
    return null
  }
  
  const summary = {
    totalRows: data.totalRows,
    totalColumns: data.totalColumns,
    fileSize: formatFileSize(data.fileSize),
    fileName: data.fileName,
    fileType: data.fileType,
    headers: data.headers,
    preview: data.preview,
    hasData: data.totalRows > 0,
    encoding: data.encoding || 'utf-8'
  }
  
  return summary
} 