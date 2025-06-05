import React, { useState, useEffect, useRef } from 'react'
import { 
  Typography, 
  Card, 
  Space, 
  Button, 
  Progress, 
  Alert, 
  Row, 
  Col,
  Statistic,
  Tag,
  Descriptions,
  Modal,
  message,
  Divider,
  Table,
  Result,
  Spin
} from 'antd'
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
  EditOutlined,
  EyeOutlined,
  FileExcelOutlined,
  InfoCircleOutlined,
  RocketOutlined
} from '@ant-design/icons'
import useAppStore from '../stores/appStore'

const { Title, Text, Paragraph } = Typography

// 模拟任务执行的Hook
function useTaskRunner() {
  const { 
    taskStatus, 
    setTaskStatus, 
    addTaskLog, 
    addErrorLog,
    fieldSelection,
    fileData
  } = useAppStore()
  
  const intervalRef = useRef(null)
  const timeoutRef = useRef(null)

  // 开始任务
  const startTask = () => {
    // 计算总处理数量
    const startRow = fieldSelection.startRow || 1
    const endRow = fieldSelection.endRow || fileData.totalRows
    const totalCount = Math.max(0, endRow - startRow + 1)
    
    setTaskStatus({
      isRunning: true,
      isCompleted: false,
      currentStatus: 'running',
      startTime: new Date(),
      totalCount,
      processedCount: 0,
      progress: 0,
      successCount: 0,
      errorCount: 0,
      logs: [],
      errorLogs: []
    })
    
    addTaskLog({
      message: '任务开始执行...',
      type: 'info'
    })
    
    addTaskLog({
      message: `预计处理 ${totalCount} 条数据`,
      type: 'info'
    })
    
    // 模拟任务执行进度
    let processed = 0
    let successCount = 0
    let errorCount = 0
    
    intervalRef.current = setInterval(() => {
      // 随机处理速度（1-5条/次）
      const batchSize = Math.floor(Math.random() * 5) + 1
      processed = Math.min(processed + batchSize, totalCount)
      
      // 模拟成功/失败概率（90%成功率）
      const batchSuccess = Math.floor(batchSize * (0.85 + Math.random() * 0.1))
      const batchError = batchSize - batchSuccess
      
      successCount += batchSuccess
      errorCount += batchError
      
      const progress = Math.round((processed / totalCount) * 100)
      const speed = Math.round((processed / ((Date.now() - new Date(taskStatus.startTime || Date.now())) / 60000)) || 0)
      const estimatedTimeLeft = speed > 0 ? Math.round((totalCount - processed) / speed) : 0
      
      setTaskStatus({
        processedCount: processed,
        progress,
        successCount,
        errorCount,
        speed,
        estimatedTimeLeft: estimatedTimeLeft * 60 // 转换为秒
      })
      
      // 添加处理日志
      if (processed % 10 === 0 || processed === totalCount) {
        addTaskLog({
          message: `已处理 ${processed}/${totalCount} 条数据，成功: ${successCount}, 失败: ${errorCount}`,
          type: processed === totalCount ? 'success' : 'info'
        })
      }
      
      // 模拟错误日志
      if (batchError > 0 && Math.random() > 0.7) {
        addErrorLog({
          message: '处理失败',
          detail: `第 ${processed - batchError + 1} 行数据格式错误`,
          type: 'data_error'
        })
      }
      
      // 任务完成
      if (processed >= totalCount) {
        clearInterval(intervalRef.current)
        setTaskStatus({
          isRunning: false,
          isCompleted: true,
          currentStatus: 'completed',
          endTime: new Date(),
          resultFilePath: `/results/${fileData.fileName}_processed_${Date.now()}.xlsx`
        })
        
        addTaskLog({
          message: '任务执行完成！',
          type: 'success'
        })
        
        message.success('数据处理完成！')
      }
    }, 1000 + Math.random() * 2000) // 1-3秒间隔
  }

  // 暂停任务
  const pauseTask = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    setTaskStatus({
      isRunning: false,
      currentStatus: 'paused'
    })
    addTaskLog({
      message: '任务已暂停',
      type: 'warning'
    })
  }

  // 停止任务
  const stopTask = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setTaskStatus({
      isRunning: false,
      currentStatus: 'stopped',
      endTime: new Date()
    })
    addTaskLog({
      message: '任务已停止',
      type: 'error'
    })
  }

  // 重新开始任务
  const restartTask = () => {
    stopTask()
    setTimeout(() => {
      startTask()
    }, 1000)
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return {
    startTask,
    pauseTask,
    stopTask,
    restartTask
  }
}

function TaskExecution() {
  const { 
    taskStatus, 
    getConfigSummary,
    validateCurrentStep,
    fileData,
    fieldSelection,
    executeTask,
    initWebSocket,
    wsConnected,
    downloadResult,
    reset,
    setCurrentStep
  } = useAppStore()
  
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [resultModalVisible, setResultModalVisible] = useState(false)
  const [executing, setExecuting] = useState(false)
  
  const configSummary = getConfigSummary()
  const { startTask, pauseTask, stopTask, restartTask } = useTaskRunner()
  
  // 初始化WebSocket连接
  useEffect(() => {
    if (!wsConnected) {
      initWebSocket()
    }
  }, [wsConnected, initWebSocket])
  
  // 格式化时间
  const formatDuration = (seconds) => {
    if (!seconds) return '0秒'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    } else {
      return `${secs}秒`
    }
  }
  
  // 获取执行时间
  const getExecutionTime = () => {
    if (taskStatus.startTime) {
      const endTime = taskStatus.endTime || new Date()
      return Math.floor((endTime - new Date(taskStatus.startTime)) / 1000)
    }
    return 0
  }

  // 获取状态颜色
  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'processing'
      case 'completed': return 'success'
      case 'paused': return 'warning'
      case 'stopped': 
      case 'error': return 'error'
      default: return 'default'
    }
  }

  // 获取状态文本
  const getStatusText = (status) => {
    switch (status) {
      case 'idle': return '待执行'
      case 'running': return '执行中'
      case 'completed': return '已完成'
      case 'paused': return '已暂停'
      case 'stopped': return '已停止'
      case 'error': return '执行错误'
      default: return '未知状态'
    }
  }

  // 计算成功率
  const getSuccessRate = () => {
    if (taskStatus.processedCount === 0) return 0
    return Math.round((taskStatus.successCount / taskStatus.processedCount) * 100)
  }

  // 开始执行任务
  const handleStartTask = async () => {
    if (!validateCurrentStep()) {
      message.error('请先完成前面步骤的配置')
      return
    }

    setExecuting(true)
    try {
      // 使用模拟任务执行器
      startTask()
      message.success('任务已启动')
    } catch (error) {
      message.error(`任务启动失败: ${error.message}`)
    } finally {
      setExecuting(false)
    }
  }

  // 下载结果文件
  const handleDownload = () => {
    if (taskStatus.resultFilePath) {
      try {
      downloadResult()
      message.success('开始下载结果文件')
      } catch (error) {
        message.error('下载失败，请重试')
      }
    } else {
      message.error('没有可下载的结果文件')
    }
  }

  // 重新开始整个流程
  const handleRestart = () => {
    Modal.confirm({
      title: '确认重新开始',
      content: '这将清除当前的处理结果和配置，重新开始整个流程。确认继续吗？',
      onOk: () => {
        reset()
        setCurrentStep(1)
        message.info('已重置，请重新配置')
      }
    })
  }

  // 生成模拟结果数据
  const generateResultData = () => {
    const data = []
    for (let i = 1; i <= Math.min(taskStatus.processedCount, 50); i++) {
      const isSuccess = Math.random() > 0.15 // 85%成功率
      data.push({
        key: i,
        row: i,
        original: `原始数据第${i}行的内容...`,
        result: isSuccess ? `处理后的结果数据第${i}行...` : null,
        status: isSuccess ? 'success' : 'error',
        timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
      })
    }
    return data
  }

  // 结果预览表格列配置
  const resultColumns = [
    {
      title: '行号',
      dataIndex: 'row',
      width: 80,
      fixed: 'left'
    },
    {
      title: '原始数据',
      dataIndex: 'original',
      width: 200,
      ellipsis: true
    },
    {
      title: '处理结果',
      dataIndex: 'result',
      width: 300,
      ellipsis: true,
      render: (text, record) => (
        <div>
          {record.status === 'success' ? (
            <Text>{text}</Text>
          ) : (
            <Text type="danger">处理失败</Text>
          )}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      )
    },
    {
      title: '处理时间',
      dataIndex: 'timestamp',
      width: 120,
      render: (time) => new Date(time).toLocaleTimeString()
    }
  ]

  const resultData = generateResultData()

  // 渲染执行前内容
  const renderReadyContent = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Card title={
        <Space>
          <RocketOutlined />
          执行准备
        </Space>
      }>
          <Alert
          type="info"
          message="准备就绪"
          description={`即将处理 ${fileData.totalRows || 0} 行数据中的第 ${fieldSelection.startRow || 1} 到第 ${fieldSelection.endRow || fileData.totalRows} 行，共 ${((fieldSelection.endRow || fileData.totalRows) - (fieldSelection.startRow || 1) + 1)} 条数据。`}
            showIcon
          style={{ marginBottom: 16 }}
        />
        
        <div>
          <Text strong>执行前检查清单：</Text>
          <ul style={{ marginTop: 8, marginLeft: 20, color: '#666' }}>
            <li>✅ API配置已完成</li>
            <li>✅ 数据文件已上传</li>
            <li>✅ 处理字段已选择</li>
            <li>✅ 提示词配置已完成</li>
          </ul>
            </div>
            
        <div style={{ marginTop: 16 }}>
          <Text strong>注意事项：</Text>
          <ul style={{ marginTop: 8, marginLeft: 20, color: '#666' }}>
            <li>任务开始后将调用API进行数据处理</li>
            <li>请确保网络连接稳定</li>
            <li>大量数据处理可能需要较长时间</li>
            <li>处理过程中可以暂停或停止任务</li>
          </ul>
          </div>
        </Card>
              </Space>
  )

  // 渲染执行中内容
  const renderRunningContent = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 执行状态 */}
          <Card title="执行状态">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {/* 进度条 */}
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>处理进度</Text>
                  <Text style={{ float: 'right' }}>
                    {taskStatus.processedCount} / {taskStatus.totalCount} 
                    ({taskStatus.progress}%)
                  </Text>
                </div>
                <Progress 
                  percent={taskStatus.progress} 
                  status={taskStatus.currentStatus === 'error' ? 'exception' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>

              {/* 统计信息 */}
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic 
                    title="已处理" 
                    value={taskStatus.processedCount} 
                    suffix={`/ ${taskStatus.totalCount}`}
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="成功" 
                    value={taskStatus.successCount} 
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="失败" 
                    value={taskStatus.errorCount} 
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="处理速度" 
                    value={taskStatus.speed} 
                    suffix="条/分钟"
                  />
                </Col>
              </Row>

              {/* 时间信息 */}
              {taskStatus.startTime && (
                <Row gutter={16}>
                  <Col span={8}>
                    <Text type="secondary">开始时间: {new Date(taskStatus.startTime).toLocaleString()}</Text>
                  </Col>
                  <Col span={8}>
                    <Text type="secondary">已执行: {formatDuration(getExecutionTime())}</Text>
                  </Col>
                  {taskStatus.isRunning && taskStatus.estimatedTimeLeft > 0 && (
                    <Col span={8}>
                      <Text type="secondary">预计剩余: {formatDuration(taskStatus.estimatedTimeLeft)}</Text>
                    </Col>
                  )}
                </Row>
              )}
            </Space>
          </Card>

        {/* 执行日志 */}
        {taskStatus.logs.length > 0 && (
        <Card title="执行日志" style={{ minHeight: 300 }}>
          <div className="log-section" style={{ maxHeight: 250, overflow: 'auto' }}>
              {taskStatus.logs.map((log) => (
              <div key={log.id} className={`log-entry ${log.type}`} style={{ 
                marginBottom: 8, 
                padding: '8px 12px', 
                backgroundColor: log.type === 'success' ? '#f6ffed' : log.type === 'warning' ? '#fffbe6' : '#fafafa',
                borderRadius: 4,
                borderLeft: `3px solid ${log.type === 'success' ? '#52c41a' : log.type === 'warning' ? '#faad14' : '#1890ff'}`
              }}>
                  [{log.timestamp}] {log.message}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* 错误日志 */}
        {taskStatus.errorLogs.length > 0 && (
          <Card title="错误日志">
            <Alert
              type="warning"
              message={`检测到 ${taskStatus.errorLogs.length} 个错误`}
              description="以下是详细的错误信息，建议检查数据格式或API配置"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <div style={{ maxHeight: 200, overflow: 'auto' }}>
              {taskStatus.errorLogs.map((error) => (
                <div key={error.id} style={{ marginBottom: 8, padding: 8, background: '#fff2f0', borderRadius: 4 }}>
                  <Text type="danger">[{error.timestamp}] {error.message}</Text>
                  {error.detail && (
                    <div style={{ marginTop: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{error.detail}</Text>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
    </Space>
  )

  // 渲染完成后内容
  const renderCompletedContent = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {/* 完成提示 */}
      <Result
        status="success"
        title="数据处理完成！"
        subTitle={`成功处理 ${taskStatus.successCount} 条数据，失败 ${taskStatus.errorCount} 条，总耗时 ${formatDuration(getExecutionTime())}`}
        extra={[
          <Button 
            type="primary" 
            icon={<DownloadOutlined />} 
            onClick={handleDownload} 
            disabled={!taskStatus.resultFilePath}
          >
            下载结果文件
          </Button>,
          <Button icon={<EyeOutlined />} onClick={() => setResultModalVisible(true)}>
            预览结果
          </Button>
        ]}
      />

      {/* 处理统计 */}
      <Card title="处理统计">
        <Row gutter={24}>
          <Col span={6}>
            <Statistic 
              title="总处理数" 
              value={taskStatus.processedCount} 
              prefix={<FileExcelOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="成功数" 
              value={taskStatus.successCount} 
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="失败数" 
              value={taskStatus.errorCount} 
              valueStyle={{ color: '#cf1322' }}
              prefix={<InfoCircleOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="成功率" 
              value={getSuccessRate()} 
              suffix="%" 
              valueStyle={{ color: getSuccessRate() >= 90 ? '#3f8600' : getSuccessRate() >= 70 ? '#faad14' : '#cf1322' }}
            />
          </Col>
        </Row>
        
        <div style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary">处理速度</Text>
                <div style={{ fontSize: 20, fontWeight: 'bold', color: '#1890ff' }}>
                  {taskStatus.speed || 0} 条/分钟
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary">开始时间</Text>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {taskStatus.startTime ? new Date(taskStatus.startTime).toLocaleString() : '-'}
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary">结束时间</Text>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {taskStatus.endTime ? new Date(taskStatus.endTime).toLocaleString() : '-'}
                </div>
              </div>
            </Col>
          </Row>
        </div>
      </Card>

      {/* 错误统计 */}
      {taskStatus.errorCount > 0 && (
        <Card title="错误统计" type="inner">
          <Alert
            type="warning"
            message={`检测到 ${taskStatus.errorCount} 条数据处理失败`}
            description="建议检查数据格式或优化提示词配置以提高成功率"
            showIcon
          />
          
          {taskStatus.errorLogs.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Text strong>最新错误日志:</Text>
              <div style={{ marginTop: 8, maxHeight: 200, overflow: 'auto' }}>
                {taskStatus.errorLogs.slice(-5).map((error) => (
                  <div key={error.id} style={{ marginBottom: 8, padding: 8, background: '#fff2f0', borderRadius: 4 }}>
                    <Text type="danger">[{error.timestamp}] {error.message}</Text>
                    {error.detail && (
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>{error.detail}</Text>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* 任务信息 */}
      <Card title="任务信息">
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="开始时间">
            {taskStatus.startTime ? new Date(taskStatus.startTime).toLocaleString() : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="结束时间">
            {taskStatus.endTime ? new Date(taskStatus.endTime).toLocaleString() : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="源文件">
            {configSummary.file.name}
          </Descriptions.Item>
          <Descriptions.Item label="文件大小">
            {configSummary.file.size}
          </Descriptions.Item>
          <Descriptions.Item label="处理字段">
            {configSummary.fields.selection}
          </Descriptions.Item>
          <Descriptions.Item label="处理范围">
            第{configSummary.fields.range}行
          </Descriptions.Item>
          <Descriptions.Item label="API类型">
            {configSummary.api.type}
          </Descriptions.Item>
          <Descriptions.Item label="使用模型">
            {configSummary.api.model}
          </Descriptions.Item>
          <Descriptions.Item label="结果文件">
            {taskStatus.resultFilePath ? (
              <Text code>{taskStatus.resultFilePath.split('/').pop()}</Text>
            ) : (
              <Text type="secondary">暂无</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="总耗时">
            {formatDuration(getExecutionTime())}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  )

  // 根据任务状态确定页面阶段
  const getPagePhase = () => {
    if (taskStatus.currentStatus === 'completed') return 'completed'
    if (taskStatus.isRunning || taskStatus.currentStatus === 'running') return 'running'
    if (taskStatus.currentStatus === 'paused' || taskStatus.processedCount > 0) return 'running'
    return 'ready'
  }

  const pagePhase = getPagePhase()

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Row gutter={24}>
        {/* 左侧主内容区 */}
        <Col span={16}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 页面标题 */}
            <div>
              <Title level={4}>
                <PlayCircleOutlined style={{ marginRight: 8 }} />
                任务执行与结果
              </Title>
              <Paragraph type="secondary">
                确认配置信息后开始执行批处理任务，实时监控处理进度并查看结果。
              </Paragraph>
            </div>

            {/* WebSocket连接状态 */}
            {!wsConnected && (
              <Alert
                type="warning"
                message="实时监控连接异常"
                description="WebSocket连接失败，可能无法实时显示任务进度。请检查网络连接或刷新页面重试。"
            showIcon
                closable
              />
            )}

            {/* 配置摘要 */}
            <Card 
              title="配置摘要" 
              extra={
                <Button 
                  size="small" 
                  icon={<SettingOutlined />}
                  onClick={() => setConfigModalVisible(true)}
                >
                  查看详情
                </Button>
              }
            >
              <div className="config-summary">
                <div className="config-card">
                  <div className="config-card-title">API配置</div>
                  <div className="config-item">
                    <span className="config-label">类型:</span>
                    <span className="config-value">{configSummary.api.type}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">模型:</span>
                    <span className="config-value">{configSummary.api.model}</span>
                  </div>
                </div>
                
                <div className="config-card">
                  <div className="config-card-title">数据文件</div>
                  <div className="config-item">
                    <span className="config-label">文件:</span>
                    <span className="config-value">{configSummary.file.name}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">大小:</span>
                    <span className="config-value">{configSummary.file.size}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">数据:</span>
                    <span className="config-value">{configSummary.file.rows}行 × {configSummary.file.columns}列</span>
                  </div>
                </div>
                
                <div className="config-card">
                  <div className="config-card-title">处理配置</div>
                  <div className="config-item">
                    <span className="config-label">字段:</span>
                    <span className="config-value">{configSummary.fields.selection}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">范围:</span>
                    <span className="config-value">第{configSummary.fields.range}行</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">提示词:</span>
                    <span className="config-value">{configSummary.prompt.format}格式</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* 任务控制 */}
            <Card title="任务控制">
              <Row gutter={24}>
                <Col span={12}>
              <Space>
                    {pagePhase === 'ready' && (
                      <Button 
                        type="primary" 
                        size="large"
                        icon={<PlayCircleOutlined />}
                        onClick={handleStartTask}
                        disabled={!validateCurrentStep() || executing}
                        loading={executing}
                      >
                        {executing ? '启动中...' : '开始执行'}
                      </Button>
                    )}
                    
                    {pagePhase === 'running' && taskStatus.isRunning && (
                      <>
                        <Button 
                          size="large"
                          icon={<PauseCircleOutlined />}
                          onClick={pauseTask}
                        >
                          暂停
                        </Button>
                        <Button 
                          danger
                          size="large"
                          icon={<StopOutlined />}
                          onClick={stopTask}
                        >
                          停止
                        </Button>
                      </>
                    )}
                    
                    {(pagePhase === 'completed' || taskStatus.currentStatus === 'stopped') && (
                      <Button 
                        size="large"
                        icon={<ReloadOutlined />}
                        onClick={() => {
                          if (pagePhase === 'completed') {
                            restartTask()
                          } else {
                            handleStartTask()
                          }
                        }}
                        disabled={executing}
                        loading={executing}
                      >
                        {pagePhase === 'completed' ? '重新执行' : '继续执行'}
                      </Button>
                    )}
                  </Space>
                </Col>
                <Col span={12} style={{ textAlign: 'right' }}>
                  <Space>
                    <Tag color={getStatusColor(taskStatus.currentStatus)} style={{ fontSize: 14, padding: '4px 12px' }}>
                      {getStatusText(taskStatus.currentStatus)}
                    </Tag>
                    {pagePhase === 'completed' && taskStatus.resultFilePath && (
                      <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
                        下载结果
                      </Button>
                    )}
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* 动态内容区域 */}
            {pagePhase === 'ready' && renderReadyContent()}
            {pagePhase === 'running' && renderRunningContent()}
            {pagePhase === 'completed' && renderCompletedContent()}

            {/* 任务失败提示 */}
            {taskStatus.currentStatus === 'error' && (
              <Alert
                type="error"
                message="任务执行失败"
                description="任务执行过程中发生错误，请检查错误日志并重新配置后重试。"
                showIcon
                action={
                  <Space>
                    <Button size="small" onClick={() => setCurrentStep(1)}>重新配置</Button>
                    <Button size="small" type="primary" onClick={handleStartTask}>重新执行</Button>
                  </Space>
                }
              />
            )}
          </Space>
        </Col>

        {/* 右侧指导区 */}
        <Col span={8}>
          <Card 
            title="操作指导" 
            size="small" 
            style={{ position: 'sticky', top: 24 }}
          >
            <Space direction="vertical" size="small">
              {pagePhase === 'ready' && (
                <>
                  <div>
                    <Text strong>执行前检查：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li>确认API配置正确无误</li>
                      <li>检查数据文件格式是否正确</li>
                      <li>确认选择的字段符合预期</li>
                      <li>验证提示词配置完整</li>
                    </ul>
                  </div>
                  <div>
                    <Text strong>预期结果：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li>处理后的数据将保存为Excel文件</li>
                      <li>包含原始数据和AI处理结果</li>
                      <li>可实时查看处理进度和状态</li>
                      <li>支持暂停、停止和重新开始</li>
                    </ul>
                  </div>
                </>
              )}
              
              {pagePhase === 'running' && (
                <>
                  <div>
                    <Text strong>监控指标：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li><strong>进度：</strong>当前处理百分比</li>
                      <li><strong>速度：</strong>每分钟处理条数</li>
                      <li><strong>成功率：</strong>处理成功的比例</li>
                      <li><strong>预计时间：</strong>剩余完成时间</li>
                    </ul>
                  </div>
                  <div>
                    <Text strong>异常处理：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li>网络中断：任务会自动暂停</li>
                      <li>API错误：检查密钥和配置</li>
                      <li>数据错误：查看错误日志详情</li>
                      <li>处理缓慢：考虑简化提示词</li>
                    </ul>
                  </div>
                </>
              )}
              
              {pagePhase === 'completed' && (
                <>
                  <div>
                    <Text strong>结果文件：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li>点击"下载结果文件"获取完整结果</li>
                      <li>结果包含原始数据和处理结果</li>
                      <li>支持Excel和CSV格式</li>
                      <li>文件保存在outputData目录</li>
                    </ul>
                  </div>
                  <div>
                    <Text strong>质量评估：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li><strong>成功率 ≥ 85%：</strong>优秀</li>
                      <li><strong>成功率 70-84%：</strong>良好</li>
                      <li><strong>成功率 &lt; 70%：</strong>需要优化</li>
                    </ul>
                  </div>
                  <div>
                    <Text strong>后续操作：</Text>
                    <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                      <li>下载并查看完整结果文件</li>
                      <li>分析失败数据的原因</li>
                      <li>优化提示词配置</li>
                      <li>处理更多数据批次</li>
                    </ul>
                  </div>
                </>
              )}
              
              <Divider style={{ margin: '12px 0' }} />
              
              <Text type="secondary">
                💡 提示：{pagePhase === 'ready' ? '检查配置无误后开始执行' : 
                         pagePhase === 'running' ? '可随时暂停或停止任务' : 
                         '建议下载结果文件备份'}
              </Text>
            </Space>
          </Card>
        </Col>

        {/* 配置详情模态框 */}
        <Modal
          title="配置详情"
          open={configModalVisible}
          onCancel={() => setConfigModalVisible(false)}
          footer={[
            <Button key="edit" icon={<EditOutlined />} onClick={() => {
              setConfigModalVisible(false)
              setCurrentStep(1)
            }}>
              修改配置
            </Button>,
            <Button key="close" type="primary" onClick={() => setConfigModalVisible(false)}>
              确定
            </Button>
          ]}
          width={800}
        >
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="API类型">{configSummary.api.type}</Descriptions.Item>
            <Descriptions.Item label="API地址">{configSummary.api.url}</Descriptions.Item>
            <Descriptions.Item label="模型名称">{configSummary.api.model}</Descriptions.Item>
            <Descriptions.Item label="文件名称">{configSummary.file.name}</Descriptions.Item>
            <Descriptions.Item label="文件大小">{configSummary.file.size}</Descriptions.Item>
            <Descriptions.Item label="数据行数">{configSummary.file.rows}</Descriptions.Item>
            <Descriptions.Item label="数据列数">{configSummary.file.columns}</Descriptions.Item>
            <Descriptions.Item label="选择字段">{configSummary.fields.selection}</Descriptions.Item>
            <Descriptions.Item label="处理范围">第{configSummary.fields.range}行</Descriptions.Item>
            <Descriptions.Item label="提示词格式">{configSummary.prompt.format}</Descriptions.Item>
            <Descriptions.Item label="模板类型">{configSummary.prompt.template}</Descriptions.Item>
          </Descriptions>
        </Modal>

        {/* 结果预览模态框 */}
        <Modal
          title="结果预览"
          open={resultModalVisible}
          onCancel={() => setResultModalVisible(false)}
          width={1000}
          footer={[
            <Button key="download" type="primary" icon={<DownloadOutlined />} onClick={() => {
              setResultModalVisible(false)
              handleDownload()
            }}>
              下载完整结果
            </Button>,
            <Button key="close" onClick={() => setResultModalVisible(false)}>
              关闭
            </Button>
          ]}
        >
          <div style={{ marginBottom: 16 }}>
            <Alert
              type="info"
              message={`显示前 ${Math.min(resultData.length, 50)} 条结果，完整数据请下载文件查看`}
              showIcon
            />
          </div>
          <Table
            columns={resultColumns}
            dataSource={resultData}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 800, y: 400 }}
            size="small"
          />
        </Modal>
      </Row>
    </div>
  )
}

export default TaskExecution 