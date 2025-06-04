import React, { useState, useEffect } from 'react'
import { 
  Typography, 
  Card, 
  Space, 
  Button, 
  Table, 
  Alert, 
  Row, 
  Col,
  Statistic,
  Tag,
  Progress,
  Result,
  message,
  Modal,
  Descriptions
} from 'antd'
import { 
  CheckCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
  EyeOutlined,
  FileExcelOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import useAppStore from '../stores/appStore'

const { Title, Text, Paragraph } = Typography

function Results() {
  const { 
    taskStatus,
    fileData,
    fieldSelection,
    getConfigSummary,
    reset,
    setCurrentStep,
    downloadResult
  } = useAppStore()
  
  const [resultModalVisible, setResultModalVisible] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  const [downloading, setDownloading] = useState(false)
  
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
    if (taskStatus.startTime && taskStatus.endTime) {
      return Math.floor((new Date(taskStatus.endTime) - new Date(taskStatus.startTime)) / 1000)
    }
    return 0
  }
  
  // 计算成功率
  const getSuccessRate = () => {
    if (taskStatus.processedCount === 0) return 0
    return Math.round((taskStatus.successCount / taskStatus.processedCount) * 100)
  }
  
  // 处理下载
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
  
  // 重新开始
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
  
  // 模拟结果数据预览
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
  
  const resultData = generateResultData()
  
  // 如果任务未完成，显示提示
  if (taskStatus.currentStatus !== 'completed') {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <Result
          status="info"
          title="任务尚未完成"
          subTitle="请先完成数据处理任务，然后查看结果"
          extra={[
            <Button type="primary" onClick={() => setCurrentStep(5)}>
              返回任务执行
            </Button>
          ]}
        />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Row gutter={24}>
        {/* 左侧主要内容 */}
        <Col span={16}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 页面标题和说明 */}
            <div>
              <Title level={4}>
                <CheckCircleOutlined style={{ marginRight: 8 }} />
                处理结果
              </Title>
              <Paragraph type="secondary">
                数据处理已完成，查看处理统计信息和结果详情。
              </Paragraph>
            </div>

            {/* 处理完成提示 */}
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
                </Button>,
                <Button icon={<ReloadOutlined />} onClick={handleRestart}>
                  重新开始
                </Button>
              ]}
            />

            {/* 处理统计 */}
            <Card title={
              <Space>
                <BarChartOutlined />
                处理统计
              </Space>
            }>
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

            {/* 错误信息 */}
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

            {/* 性能分析 */}
            <Card title="性能分析">
              <Row gutter={16}>
                <Col span={12}>
                  <div className="performance-item">
                    <div className="performance-title">处理效率</div>
                    <div className={`performance-status ${getSuccessRate() >= 85 ? 'excellent' : getSuccessRate() >= 70 ? 'good' : 'poor'}`}>
                      {getSuccessRate() >= 85 ? '🎉 优秀' : getSuccessRate() >= 70 ? '✅ 良好' : '⚠️ 需要优化'}
                    </div>
                  </div>
                </Col>
                <Col span={12}>
                  <div className="performance-item">
                    <div className="performance-title">处理速度</div>
                    <div className={`performance-status ${taskStatus.speed >= 30 ? 'excellent' : taskStatus.speed >= 15 ? 'good' : 'poor'}`}>
                      {taskStatus.speed >= 30 ? '🚀 很快' : taskStatus.speed >= 15 ? '⏱️ 适中' : '🐌 较慢'}
                    </div>
                  </div>
                </Col>
              </Row>
              
              <div style={{ marginTop: 16 }}>
                <Text strong>优化建议：</Text>
                <ul style={{ marginTop: 8, marginLeft: 20, color: '#666' }}>
                  {getSuccessRate() < 70 && <li>成功率较低，建议优化提示词配置或检查数据格式</li>}
                  {taskStatus.speed < 15 && <li>处理速度较慢，建议简化提示词或检查API性能</li>}
                  {taskStatus.errorCount > taskStatus.successCount * 0.3 && <li>错误率较高，建议检查数据质量和API配置</li>}
                  {getSuccessRate() >= 85 && taskStatus.speed >= 30 && <li>处理效果很好，可以继续使用当前配置</li>}
                </ul>
              </div>
            </Card>

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
        </Col>

        {/* 右侧操作说明 */}
        <Col span={8}>
          <Card title="操作指南" size="small" style={{ position: 'sticky', top: 24 }}>
            <Space direction="vertical" size="small">
              <div>
                <Text strong>结果文件：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>点击"下载结果文件"获取完整的处理结果</li>
                  <li>结果文件包含原始数据和处理后的数据</li>
                  <li>支持Excel和CSV格式导出</li>
                  <li>文件会保存到outputData目录下</li>
                </ul>
              </div>
              <div>
                <Text strong>快捷操作：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>点击"预览结果"查看数据样本</li>
                  <li>点击"下载结果文件"获取完整数据</li>
                  <li>点击"重新开始"配置新的处理任务</li>
                </ul>
              </div>
              <div>
                <Text strong>质量评估：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li><strong>成功率 ≥ 85%：</strong>优秀，配置合理</li>
                  <li><strong>成功率 70-84%：</strong>良好，可以继续使用</li>
                  <li><strong>成功率 &lt; 70%：</strong>需要优化提示词</li>
                </ul>
              </div>
              <Text type="secondary">
                💡 提示：成功率低于70%时，建议优化提示词配置
              </Text>
            </Space>
          </Card>
        </Col>

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

export default Results 