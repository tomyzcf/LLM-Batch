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
    setCurrentStep
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
  
  // 模拟下载功能
  const handleDownload = () => {
    setDownloading(true)
    setDownloadProgress(0)
    
    // 模拟下载进度
    const interval = setInterval(() => {
      setDownloadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setDownloading(false)
          message.success('文件下载完成！')
          return 100
        }
        return prev + 10
      })
    }, 200)
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
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
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
          subTitle={`成功处理 ${taskStatus.successCount} 条数据，失败 ${taskStatus.errorCount} 条`}
          extra={[
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload} loading={downloading}>
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

        {/* 下载进度 */}
        {downloading && (
          <Card size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>正在生成下载文件...</Text>
              <Progress percent={downloadProgress} status="active" />
            </Space>
          </Card>
        )}

        {/* 处理统计 */}
        <Card title="处理统计" icon={<BarChartOutlined />}>
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
          
          <Row gutter={24} style={{ marginTop: 24 }}>
            <Col span={8}>
              <Text type="secondary">处理速度: </Text>
              <Text strong>{taskStatus.speed || 0} 条/分钟</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">总耗时: </Text>
              <Text strong>{formatDuration(getExecutionTime())}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">平均耗时: </Text>
              <Text strong>
                {taskStatus.processedCount > 0 
                  ? (getExecutionTime() / taskStatus.processedCount).toFixed(2) 
                  : 0} 秒/条
              </Text>
            </Col>
          </Row>
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
              {configSummary.api.type === 'llm_compatible' ? '通用LLM' : '阿里百炼Agent'}
            </Descriptions.Item>
            <Descriptions.Item label="使用模型">
              {configSummary.api.model}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 结果文件信息 */}
        <Card title="结果文件">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>文件路径: </Text>
              <Text code>{taskStatus.resultFilePath}</Text>
            </div>
            <div>
              <Text strong>文件格式: </Text>
              <Tag color="blue">Excel (.xlsx)</Tag>
            </div>
            <div>
              <Text strong>包含内容: </Text>
              <Text>原始数据 + 处理结果 + 状态信息</Text>
            </div>
            
            <Alert
              type="info"
              message="文件下载说明"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>结果文件包含所有原始数据和处理结果</li>
                  <li>失败的数据行会标注具体错误原因</li>
                  <li>文件支持Excel格式，可直接使用办公软件打开</li>
                  <li>建议及时下载保存，避免数据丢失</li>
                </ul>
              }
              showIcon
            />
          </Space>
        </Card>

        {/* 操作建议 */}
        <Card title="后续操作建议" size="small">
          <Space direction="vertical" size="small">
            <Text>• <strong>质量检查：</strong> 下载结果文件后，建议抽样检查处理质量</Text>
            <Text>• <strong>错误处理：</strong> 对于失败的数据，可以调整提示词后重新处理</Text>
            <Text>• <strong>批量处理：</strong> 如需处理更多数据，可以重新开始配置新任务</Text>
            <Text>• <strong>配置保存：</strong> 如果处理效果良好，建议记录当前配置参数</Text>
            <Text type="secondary">💡 提示：成功率低于70%时，建议优化提示词配置</Text>
          </Space>
        </Card>

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
      </Space>
    </div>
  )
}

export default Results 