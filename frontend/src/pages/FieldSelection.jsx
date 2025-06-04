import React, { useState, useEffect } from 'react'
import { 
  Typography, 
  Card, 
  Space, 
  Table, 
  Checkbox, 
  Radio, 
  Input, 
  InputNumber, 
  Alert, 
  Button, 
  Row, 
  Col,
  Tag,
  Divider,
  message
} from 'antd'
import { TableOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons'
import useAppStore from '../stores/appStore'

const { Title, Text, Paragraph } = Typography

function FieldSelection() {
  const { 
    fileData, 
    fieldSelection, 
    setFieldSelection,
    setCurrentStep 
  } = useAppStore()
  
  const [selectedFields, setSelectedFields] = useState([])
  const [startRow, setStartRow] = useState(1)
  const [endRow, setEndRow] = useState(null)

  // 初始化状态
  useEffect(() => {
    if (fieldSelection.selectedFields.length > 0) {
      setSelectedFields(fieldSelection.selectedFields)
    }
    setStartRow(fieldSelection.startRow || 1)
    setEndRow(fieldSelection.endRow)
  }, [fieldSelection])

  // 处理单个字段选择
  const handleFieldCheck = (fieldIndex, checked) => {
    let newSelectedFields
    if (checked) {
      newSelectedFields = [...selectedFields, fieldIndex].sort((a, b) => a - b)
    } else {
      newSelectedFields = selectedFields.filter(index => index !== fieldIndex)
    }
    
    setSelectedFields(newSelectedFields)
    updateFieldSelection({ selectedFields: newSelectedFields })
  }

  // 处理全选/取消全选
  const handleSelectAll = (checked) => {
    if (checked) {
      const allFields = fileData.headers.map((_, index) => index)
      setSelectedFields(allFields)
      updateFieldSelection({ selectedFields: allFields })
    } else {
      setSelectedFields([])
      updateFieldSelection({ selectedFields: [] })
    }
  }

  // 处理行数范围
  const handleRowRangeChange = (type, value) => {
    if (type === 'start') {
      setStartRow(value)
      updateFieldSelection({ startRow: value })
    } else {
      setEndRow(value)
      updateFieldSelection({ endRow: value })
    }
  }

  // 更新字段选择状态
  const updateFieldSelection = (updates) => {
    const selectedFieldNames = []
    if (updates.selectedFields) {
      updates.selectedFields.forEach(index => {
        if (fileData.headers[index]) {
          selectedFieldNames.push(fileData.headers[index])
        }
      })
    }
    
    setFieldSelection({
      ...fieldSelection,
      ...updates,
      selectedFieldNames
    })
  }

  // 生成字段表格列
  const fieldColumns = [
    {
      title: (
        <Checkbox
          checked={selectedFields.length === fileData.headers.length && fileData.headers.length > 0}
          indeterminate={selectedFields.length > 0 && selectedFields.length < fileData.headers.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
        >
          全选
        </Checkbox>
      ),
      dataIndex: 'selected',
      width: 80,
      render: (_, record, index) => (
        <Checkbox
          checked={selectedFields.includes(index)}
          onChange={(e) => handleFieldCheck(index, e.target.checked)}
        />
      )
    },
    {
      title: '列号',
      dataIndex: 'index',
      width: 80,
      render: (_, record, index) => (
        <Tag color="blue">{index + 1}</Tag>
      )
    },
    {
      title: '字段名',
      dataIndex: 'name',
      render: (_, record, index) => (
        <Text strong>{fileData.headers[index]}</Text>
      )
    },
    {
      title: '示例数据',
      dataIndex: 'sample',
      render: (_, record, index) => {
        const sampleData = fileData.previewData
          ?.slice(0, 3)
          .map(row => row[index])
          .filter(val => val && val.toString().trim())
          .slice(0, 2)
        
        return (
          <div>
            {sampleData?.map((data, idx) => (
              <div key={idx} style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 2 }}>
                {data.toString().length > 30 ? data.toString().substring(0, 30) + '...' : data}
              </div>
            )) || <Text type="secondary">-</Text>}
          </div>
        )
      }
    }
  ]

  // 生成字段表格数据
  const fieldTableData = fileData.headers?.map((header, index) => ({
    key: index,
    index,
    name: header
  })) || []

  // 当前选择状态
  const isValid = selectedFields.length > 0
  const totalDataRows = fileData.totalRows || 0
  const effectiveEndRow = endRow || totalDataRows
  const effectiveStartRow = Math.max(1, startRow)

  if (!fileData.fileName || fileData.headers.length === 0) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <Alert
          type="warning"
          message="请先上传数据文件"
          description="在字段选择之前，请先在上一步上传并解析数据文件"
          showIcon
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
                <TableOutlined style={{ marginRight: 8 }} />
                字段选择与范围设置
              </Title>
              <Paragraph type="secondary">
                选择要处理的数据字段和处理范围。请至少选择一个字段，合理设置处理范围。
              </Paragraph>
            </div>

            {/* 文件信息摘要 */}
            <Card size="small">
              <Row gutter={16}>
                <Col span={6}>
                  <Text type="secondary">文件名：</Text>
                  <Text strong>{fileData.fileName}</Text>
                </Col>
                <Col span={6}>
                  <Text type="secondary">总行数：</Text>
                  <Text strong>{fileData.totalRows}</Text>
                </Col>
                <Col span={6}>
                  <Text type="secondary">总列数：</Text>
                  <Text strong>{fileData.totalColumns}</Text>
                </Col>
                <Col span={6}>
                  <Text type="secondary">已选字段：</Text>
                  <Text strong>{selectedFields.length}</Text>
                </Col>
              </Row>
            </Card>

            {/* 字段列表 */}
            <Card 
              title={`可用字段 (${fileData.headers.length})`}
              extra={
                <Space>
                  <Text type="secondary">
                    已选择 {selectedFields.length} 个字段
                  </Text>
                </Space>
              }
            >
              <Table
                columns={fieldColumns}
                dataSource={fieldTableData}
                pagination={false}
                size="small"
                scroll={{ y: 300 }}
              />
            </Card>

            {/* 当前选择预览 */}
            {isValid && (
              <Card 
                title="当前选择" 
                extra={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>已选择字段：</Text>
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {selectedFields.map(index => (
                          <Tag key={index} color="blue">
                            第{index + 1}列：{fileData.headers[index]}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  </div>
                </Space>
              </Card>
            )}

            {/* 处理范围设置 */}
            <Card title="处理范围设置">
              <Row gutter={24}>
                <Col span={12}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>起始行数：</Text>
                    <InputNumber
                      value={startRow}
                      onChange={(value) => handleRowRangeChange('start', value)}
                      min={1}
                      max={totalDataRows}
                      style={{ width: '100%' }}
                      placeholder="从第几行开始处理"
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      从第几行开始处理数据（包含该行）
                    </Text>
                  </Space>
                </Col>
                <Col span={12}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>结束行数：</Text>
                    <InputNumber
                      value={endRow}
                      onChange={(value) => handleRowRangeChange('end', value)}
                      min={effectiveStartRow}
                      max={totalDataRows}
                      style={{ width: '100%' }}
                      placeholder="留空表示处理到最后一行"
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      处理到第几行结束（包含该行），留空表示处理到最后一行
                    </Text>
                  </Space>
                </Col>
              </Row>
              
              <div style={{ marginTop: 16 }}>
                <Alert
                  type="info"
                  icon={<InfoCircleOutlined />}
                  message={`将处理第 ${effectiveStartRow} 到第 ${effectiveEndRow} 行，共 ${effectiveEndRow - effectiveStartRow + 1} 行数据`}
                  showIcon
                />
              </div>
            </Card>

            {/* 配置有效提示 */}
            {isValid && (
              <Alert
                type="success"
                message="字段选择有效"
                description={`已选择 ${selectedFields.length} 个字段，处理范围为第 ${effectiveStartRow} 到第 ${effectiveEndRow} 行`}
                icon={<CheckCircleOutlined />}
                showIcon
                action={
                  <Button 
                    type="primary" 
                    onClick={() => setCurrentStep(4)}
                  >
                    下一步：提示词配置
                  </Button>
                }
              />
            )}

            {/* 无效配置提示 */}
            {!isValid && (
              <Alert
                type="warning"
                message="请选择要处理的字段"
                description="至少需要选择一个字段才能进行下一步"
                showIcon
              />
            )}
          </Space>
        </Col>

        {/* 右侧配置说明 */}
        <Col span={8}>
          <Card title="配置说明" size="small" style={{ position: 'sticky', top: 24 }}>
            <Space direction="vertical" size="small">
              <div>
                <Text strong>字段选择：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>从表格中勾选要处理的字段</li>
                  <li>支持单选、多选和全选</li>
                  <li>至少选择一个字段进行处理</li>
                  <li>字段名会自动保存到配置中</li>
                </ul>
              </div>
              <div>
                <Text strong>处理范围：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li><strong>起始行：</strong>从第几行开始处理数据</li>
                  <li><strong>结束行：</strong>处理到第几行，留空表示到最后</li>
                  <li><strong>分批处理：</strong>合理设置范围避免超时</li>
                  <li><strong>断点续传：</strong>支持从指定行继续处理</li>
                </ul>
              </div>
              <div>
                <Text strong>注意事项：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>行号从1开始计算</li>
                  <li>表格第一行是字段标题，不参与处理</li>
                  <li>处理范围是指数据行，不包括标题行</li>
                  <li>建议先用小范围测试效果</li>
                </ul>
              </div>
              <div>
                <Text strong>优化建议：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>选择包含有效文本内容的字段</li>
                  <li>避免选择空值较多的字段</li>
                  <li>大文件建议分批处理</li>
                  <li>记录成功的配置以备复用</li>
                </ul>
              </div>
              <Text type="secondary">
                💡 提示：合理设置处理范围可以避免一次性处理过多数据
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default FieldSelection 