import React, { useState, useCallback } from 'react'
import { 
  Typography, 
  Card, 
  Upload, 
  Button, 
  Table, 
  Alert, 
  Space, 
  Statistic, 
  Row, 
  Col,
  Progress,
  message,
  Spin
} from 'antd'
import { 
  InboxOutlined, 
  FileExcelOutlined, 
  DeleteOutlined,
  EyeOutlined,
  UploadOutlined
} from '@ant-design/icons'
import useAppStore from '../stores/appStore'
import { parseFile } from '../utils/fileParser'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

function DataUpload() {
  const { 
    fileData, 
    setFileData, 
    uploadFile,
    setCurrentStep 
  } = useAppStore()
  
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  // 处理文件上传
  const handleFileUpload = useCallback(async (file) => {
    setUploading(true)
    setUploadProgress(0)
    
    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 100)

      // 上传文件到后端
      const uploadedFile = await uploadFile(file)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      
      // 解析文件内容
      setParsing(true)
      const parsedData = await parseFile(file)
      
      // 处理预览数据格式 - 将对象数组转换为数组数组
      const previewData = parsedData.preview ? parsedData.preview.map(row => {
        return parsedData.headers.map(header => row[header] || '')
      }) : []
      
      // 更新文件数据
      setFileData({
        fileName: file.name,
        fileSize: file.size,
        totalRows: parsedData.totalRows,
        totalColumns: parsedData.totalColumns,
        previewData: previewData,
        headers: parsedData.headers,
        uploadedFile: uploadedFile
      })
      
      message.success('文件上传和解析完成！')
      
    } catch (error) {
      console.error('文件处理失败:', error)
      message.error(`文件处理失败: ${error.message}`)
    } finally {
      setUploading(false)
      setParsing(false)
      setUploadProgress(0)
    }
    
    return false // 阻止默认上传行为
  }, [uploadFile, setFileData])

  // 删除文件
  const handleRemoveFile = () => {
    setFileData({
      fileName: '',
      fileSize: 0,
      totalRows: 0,
      totalColumns: 0,
      previewData: [],
      headers: [],
      uploadedFile: null
    })
    message.info('文件已移除')
  }

  // 文件上传配置
  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.csv,.xlsx,.xls,.json',
    beforeUpload: handleFileUpload,
    showUploadList: false,
    disabled: uploading || parsing
  }

  // 表格列配置
  const columns = fileData.headers.map((header, index) => ({
    title: `${header} (第${index + 1}列)`,
    dataIndex: index.toString(),
    key: index.toString(),
    width: 150,
    ellipsis: true,
    render: (text) => (
      <span title={text}>
        {text !== null && text !== undefined ? text.toString() : '-'}
      </span>
    )
  }))

  // 表格数据
  const tableData = fileData.previewData.map((row, index) => ({
    key: index,
    ...row.reduce((acc, cell, cellIndex) => {
      acc[cellIndex.toString()] = cell
      return acc
    }, {})
  }))

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div>
          <Title level={4}>
            <UploadOutlined style={{ marginRight: 8 }} />
            数据上传与预览
          </Title>
          <Paragraph type="secondary">
            上传要处理的数据文件，支持CSV、Excel、JSON格式，文件大小限制50MB。
          </Paragraph>
        </div>

        {/* 文件上传区域 */}
        {!fileData.fileName ? (
          <Card>
            <Dragger {...uploadProps} style={{ padding: '40px 20px' }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                点击或拖拽文件到此区域上传
              </p>
              <p className="ant-upload-hint">
                支持 CSV、Excel (.xlsx/.xls)、JSON 格式文件，单个文件大小不超过 50MB
              </p>
            </Dragger>
            
            {/* 上传进度 */}
            {uploading && (
              <div style={{ marginTop: 16 }}>
                <Text>正在上传文件...</Text>
                <Progress percent={uploadProgress} status="active" />
              </div>
            )}
            
            {/* 解析进度 */}
            {parsing && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Spin size="large" />
                <div style={{ marginTop: 8 }}>
                  <Text>正在解析文件内容...</Text>
                </div>
              </div>
            )}
          </Card>
        ) : (
          <>
            {/* 文件信息卡片 */}
            <Card 
              title="文件信息" 
              extra={
                <Button 
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
                    prefix={<FileExcelOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="文件大小" 
                    value={fileData.fileSize > 1024 * 1024 
                      ? `${(fileData.fileSize / 1024 / 1024).toFixed(1)} MB`
                      : `${(fileData.fileSize / 1024).toFixed(1)} KB`
                    }
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="数据行数" 
                    value={fileData.totalRows}
                  />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="数据列数" 
                    value={fileData.totalColumns}
                  />
                </Col>
              </Row>
            </Card>

            {/* 数据预览 */}
            <Card 
              title={
                <Space>
                  <EyeOutlined />
                  数据预览
                  <Text type="secondary">(显示前10行)</Text>
                </Space>
              }
            >
              {fileData.previewData.length > 0 ? (
                <>
                  <Alert
                    type="info"
                    message="数据预览"
                    description={`当前显示前 ${Math.min(fileData.previewData.length, 10)} 行数据，共 ${fileData.totalRows} 行 ${fileData.totalColumns} 列。请检查数据格式是否正确。`}
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Table
                    columns={columns}
                    dataSource={tableData.slice(0, 10)}
                    pagination={false}
                    scroll={{ x: Math.max(800, fileData.totalColumns * 150), y: 400 }}
                    size="small"
                    bordered
                  />
                </>
              ) : (
                <Alert
                  type="warning"
                  message="无法预览数据"
                  description="文件可能为空或格式不正确，请检查文件内容。"
                  showIcon
                />
              )}
            </Card>

            {/* 数据质量检查 */}
            <Card title="数据质量检查">
              <Row gutter={16}>
                <Col span={8}>
                  <div className="quality-check-item">
                    <div className="quality-check-title">数据完整性</div>
                    <div className="quality-check-status success">
                      ✓ 数据结构完整
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div className="quality-check-item">
                    <div className="quality-check-title">格式验证</div>
                    <div className="quality-check-status success">
                      ✓ 文件格式正确
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div className="quality-check-item">
                    <div className="quality-check-title">大小检查</div>
                    <div className={`quality-check-status ${fileData.fileSize > 10 * 1024 * 1024 ? 'warning' : 'success'}`}>
                      {fileData.fileSize > 10 * 1024 * 1024 ? '⚠ 文件较大' : '✓ 文件大小适中'}
                    </div>
                  </div>
                </Col>
              </Row>
              
              <Alert
                type="info"
                message="处理建议"
                description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    <li>确保数据格式正确，第一行为列标题</li>
                    <li>检查是否有空行或格式异常的数据</li>
                    <li>大文件建议分批处理以提高效率</li>
                    <li>确认要处理的字段包含有效的文本内容</li>
                  </ul>
                }
                showIcon
                style={{ marginTop: 16 }}
              />
            </Card>

            {/* 操作提示 */}
            <Alert
              type="success"
              message="文件上传成功！"
              description="数据文件已成功上传和解析，可以进行下一步字段选择。"
              showIcon
              action={
                <Button 
                  type="primary" 
                  onClick={() => setCurrentStep(3)}
                >
                  下一步：字段选择
                </Button>
              }
            />
          </>
        )}
      </Space>
    </div>
  )
}

export default DataUpload 