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
  Divider
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
  EditOutlined
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
    getConfigSummary,
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
    currentStep,
    setCurrentStep,
    taskStatus, 
    getConfigSummary,
    validateCurrentStep,
    fileData
  } = useAppStore()
  
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const { startTask, pauseTask, stopTask, restartTask } = useTaskRunner()
  
  const configSummary = getConfigSummary()
  
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

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div>
          <Title level={4}>
            <PlayCircleOutlined style={{ marginRight: 8 }} />
            任务执行与监控
          </Title>
          <Paragraph type="secondary">
            确认配置信息后开始执行批处理任务，实时监控处理进度和状态。
          </Paragraph>
        </div>

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
                <span className="config-value">{configSummary.api.type === 'llm_compatible' ? '通用LLM' : '阿里百炼Agent'}</span>
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
                <span className="config-value">{configSummary.prompt.format.toUpperCase()}格式</span>
              </div>
            </div>
          </div>
        </Card>

        {/* 任务控制 */}
        <Card title="任务控制">
          <Row gutter={24}>
            <Col span={12}>
              <Space>
                {!taskStatus.isRunning && taskStatus.currentStatus !== 'completed' && (
                  <Button 
                    type="primary" 
                    size="large"
                    icon={<PlayCircleOutlined />}
                    onClick={startTask}
                    disabled={!validateCurrentStep()}
                  >
                    开始执行
                  </Button>
                )}
                
                {taskStatus.isRunning && (
                  <Button 
                    size="large"
                    icon={<PauseCircleOutlined />}
                    onClick={pauseTask}
                  >
                    暂停
                  </Button>
                )}
                
                {(taskStatus.isRunning || taskStatus.currentStatus === 'paused') && (
                  <Button 
                    danger
                    size="large"
                    icon={<StopOutlined />}
                    onClick={stopTask}
                  >
                    停止
                  </Button>
                )}
                
                {(taskStatus.currentStatus === 'completed' || taskStatus.currentStatus === 'stopped') && (
                  <Button 
                    size="large"
                    icon={<ReloadOutlined />}
                    onClick={restartTask}
                  >
                    重新执行
                  </Button>
                )}
              </Space>
            </Col>
            <Col span={12} style={{ textAlign: 'right' }}>
              <Space>
                <Tag color={getStatusColor(taskStatus.currentStatus)} style={{ fontSize: 14, padding: '4px 12px' }}>
                  {getStatusText(taskStatus.currentStatus)}
                </Tag>
                {taskStatus.currentStatus === 'completed' && taskStatus.resultFilePath && (
                  <Button type="primary" icon={<DownloadOutlined />}>
                    下载结果
                  </Button>
                )}
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 执行状态 */}
        {(taskStatus.isRunning || taskStatus.processedCount > 0) && (
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
        )}

        {/* 执行日志 */}
        {taskStatus.logs.length > 0 && (
          <Card title="执行日志" style={{ minHeight: 400 }}>
            <div className="log-section">
              {taskStatus.logs.map((log) => (
                <div key={log.id} className={`log-entry ${log.type}`}>
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

        {/* 任务完成提示 */}
        {taskStatus.currentStatus === 'completed' && (
          <Alert
            type="success"
            message="任务执行完成！"
            description={
              <div>
                <p>数据处理已完成，共处理 {taskStatus.processedCount} 条数据。</p>
                <p>成功: {taskStatus.successCount} 条，失败: {taskStatus.errorCount} 条</p>
                <p>总耗时: {formatDuration(getExecutionTime())}</p>
              </div>
            }
            showIcon
            action={
              <Space>
                <Button size="small" onClick={() => setCurrentStep(6)}>查看结果</Button>
                <Button size="small" type="primary" icon={<DownloadOutlined />}>下载结果</Button>
              </Space>
            }
          />
        )}

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
            <Descriptions.Item label="提示词格式">{configSummary.prompt.format.toUpperCase()}</Descriptions.Item>
            <Descriptions.Item label="模板类型">{configSummary.prompt.template}</Descriptions.Item>
          </Descriptions>
        </Modal>
      </Space>
    </div>
  )
}

export default TaskExecution 