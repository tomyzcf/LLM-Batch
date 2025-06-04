import React, { useState, useCallback } from 'react'
import { 
  Typography, 
  Card, 
  Upload, 
  Table, 
  Alert, 
  Space, 
  Statistic, 
  Row, 
  Col,
  Progress,
  Button,
  Tag,
  message
} from 'antd'
import { 
  CloudUploadOutlined, 
  FileTextOutlined, 
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons'
import useAppStore from '../stores/appStore'
import { parseFile, formatFileSize } from '../utils/fileParser'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

function DataUpload() {
  const { fileData, setFileData, resetFileData } = useAppStore()
  const [uploading, setUploading] = useState(false)
  const [parseProgress, setParseProgress] = useState(0)

  // 处理文件上传
  const handleFileUpload = useCallback(async (file) => {
    setUploading(true)
    setParseProgress(0)

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setParseProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // 解析文件
      const result = await parseFile(file, { preview: 10 })
      
      clearInterval(progressInterval)
      setParseProgress(100)

      // 更新文件数据到store
      setFileData(result)
      
      message.success(`文件 "${file.name}" 上传成功！`)
      
    } catch (error) {
      message.error(`文件上传失败: ${error.message}`)
      console.error('文件上传错误:', error)
    } finally {
      setUploading(false)
      setTimeout(() => setParseProgress(0), 1000)
    }

    // 阻止默认上传行为
    return false
  }, [setFileData])

  // 删除文件
  const handleRemoveFile = () => {
    resetFileData()
    message.info('文件已移除')
  }

  // 生成表格列配置
  const generateTableColumns = () => {
    if (!fileData.headers || fileData.headers.length === 0) {
      return []
    }

    return fileData.headers.map((header, index) => ({
      title: (
        <div>
          <Text strong>{header}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            列 {index + 1}
          </Text>
        </div>
      ),
      dataIndex: header,
      key: header,
      width: 150,
      ellipsis: true,
      render: (text) => (
        <div style={{ wordBreak: 'break-word' }}>
          {text || <Text type="secondary">-</Text>}
        </div>
      )
    }))
  }

  // 生成表格数据
  const generateTableData = () => {
    if (!fileData.preview) return []
    
    return fileData.preview.map((row, index) => ({
      key: index,
      ...row
    }))
  }

  // 获取文件类型标签颜色
  const getFileTypeColor = (fileType) => {
    switch (fileType) {
      case 'csv': return 'blue'
      case 'excel': return 'green'
      case 'json': return 'orange'
      default: return 'default'
    }
  }

  // 上传配置
  const uploadProps = {
    name: 'file',
    multiple: false,
    beforeUpload: handleFileUpload,
    showUploadList: false,
    accept: '.csv,.xlsx,.xls,.json',
    disabled: uploading
  }

  const hasFileData = fileData.fileName && fileData.headers.length > 0

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题和说明 */}
        <div>
          <Title level={4}>
            <CloudUploadOutlined style={{ marginRight: 8 }} />
            数据上传与预览
          </Title>
          <Paragraph type="secondary">
            上传您要处理的数据文件。支持 CSV、Excel（.xlsx/.xls）和 JSON 格式，文件大小限制为 50MB。
          </Paragraph>
        </div>

        {/* 文件上传区域 */}
        {!hasFileData ? (
          <Card>
            <Dragger {...uploadProps} style={{ padding: '20px 0' }}>
              <p className="ant-upload-drag-icon">
                <CloudUploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                点击或拖拽文件到此区域上传
              </p>
              <p className="ant-upload-hint">
                支持 CSV、Excel（.xlsx/.xls）、JSON 格式文件，最大 50MB
              </p>
            </Dragger>

            {uploading && (
              <div style={{ marginTop: 16 }}>
                <Progress 
                  percent={parseProgress} 
                  status="active"
                  strokeColor="#1890ff"
                />
                <Text type="secondary">正在解析文件...</Text>
              </div>
            )}
          </Card>
        ) : (
          /* 文件信息展示 */
          <Card 
            title="已上传文件"
            extra={
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />}
                onClick={handleRemoveFile}
              >
                移除文件
              </Button>
            }
          >
            <Row gutter={24}>
              <Col span={6}>
                <Statistic
                  title="文件名"
                  value={fileData.fileName}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="文件大小"
                  value={formatFileSize(fileData.fileSize)}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="数据行数"
                  value={fileData.totalRows}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="数据列数"
                  value={fileData.totalColumns}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
            </Row>
            
            <div style={{ marginTop: 16 }}>
              <Space>
                <Tag color={getFileTypeColor(fileData.fileType)}>
                  {fileData.fileType?.toUpperCase()}
                </Tag>
                <Tag>{fileData.encoding}</Tag>
                {fileData.parseInfo && (
                  <Text type="secondary">
                    {fileData.fileType === 'excel' && `工作表: ${fileData.parseInfo.sheetName}`}
                    {fileData.fileType === 'csv' && `分隔符: ${fileData.parseInfo.delimiter}`}
                    {fileData.fileType === 'json' && `类型: ${fileData.parseInfo.originalType}`}
                  </Text>
                )}
              </Space>
            </div>
          </Card>
        )}

        {/* 数据预览 */}
        {hasFileData && (
          <Card 
            title={
              <Space>
                <EyeOutlined />
                数据预览
                <Text type="secondary">（显示前 10 行）</Text>
              </Space>
            }
          >
            {fileData.totalRows === 0 ? (
              <Alert
                type="warning"
                message="文件中没有找到有效数据"
                description="请检查文件格式或内容是否正确"
                showIcon
              />
            ) : (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Alert
                    type="info"
                    message={`共找到 ${fileData.totalRows} 行数据，${fileData.totalColumns} 列字段`}
                    showIcon
                  />
                </div>
                
                <div className="data-preview">
                  <Table
                    columns={generateTableColumns()}
                    dataSource={generateTableData()}
                    scroll={{ x: true, y: 400 }}
                    pagination={false}
                    size="small"
                    bordered
                  />
                </div>

                {fileData.totalRows > 10 && (
                  <div style={{ marginTop: 8, textAlign: 'center' }}>
                    <Text type="secondary">
                      仅显示前 10 行数据，完整数据共 {fileData.totalRows} 行
                    </Text>
                  </div>
                )}
              </>
            )}
          </Card>
        )}

        {/* 字段信息 */}
        {hasFileData && fileData.headers.length > 0 && (
          <Card title="字段信息">
            <Row gutter={[16, 8]}>
              {fileData.headers.map((header, index) => (
                <Col key={index} span={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Text strong>第 {index + 1} 列</Text>
                    <br />
                    <Text>{header}</Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {/* 使用说明 */}
        <Card title="使用说明" size="small">
          <Space direction="vertical" size="small">
            <Text>• <strong>CSV文件：</strong> 确保首行为字段标题，使用UTF-8编码</Text>
            <Text>• <strong>Excel文件：</strong> 系统将读取第一个工作表，首行为字段标题</Text>
            <Text>• <strong>JSON文件：</strong> 支持对象数组格式，如 {`[{"name": "张三", "age": 25}]`}</Text>
            <Text>• <strong>文件限制：</strong> 最大50MB，如需处理更大文件请先分割</Text>
            <Text type="secondary">💡 提示：上传文件后可在下一步选择要处理的字段</Text>
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default DataUpload 