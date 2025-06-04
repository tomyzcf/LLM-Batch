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
    setFieldSelection 
  } = useAppStore()
  
  const [localFieldRange, setLocalFieldRange] = useState('')
  const [selectedFields, setSelectedFields] = useState([])
  const [useFieldRange, setUseFieldRange] = useState(false)
  const [startRow, setStartRow] = useState(1)
  const [endRow, setEndRow] = useState(null)

  // 初始化状态
  useEffect(() => {
    if (fieldSelection.selectedFields.length > 0) {
      setSelectedFields(fieldSelection.selectedFields)
    }
    if (fieldSelection.fieldRange) {
      setLocalFieldRange(fieldSelection.fieldRange)
      setUseFieldRange(fieldSelection.useFieldRange)
    }
    setStartRow(fieldSelection.startRow || 1)
    setEndRow(fieldSelection.endRow)
  }, [fieldSelection])

  // 处理字段选择方式变化
  const handleSelectionModeChange = (e) => {
    const useRange = e.target.value === 'range'
    setUseFieldRange(useRange)
    
    // 清除之前的选择
    if (useRange) {
      setSelectedFields([])
    } else {
      setLocalFieldRange('')
    }
    
    updateFieldSelection({ useFieldRange: useRange })
  }

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

  // 处理字段范围输入
  const handleFieldRangeChange = (value) => {
    setLocalFieldRange(value)
    updateFieldSelection({ fieldRange: value })
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
    setFieldSelection({
      ...fieldSelection,
      ...updates
    })
  }

  // 解析字段范围
  const parseFieldRange = (rangeStr) => {
    if (!rangeStr) return []
    
    try {
      const ranges = rangeStr.split(',').map(item => item.trim())
      const result = []
      
      for (const range of ranges) {
        if (range.includes('-')) {
          const [start, end] = range.split('-').map(num => parseInt(num.trim()) - 1)
          if (!isNaN(start) && !isNaN(end) && start >= 0 && end < fileData.headers.length) {
            for (let i = start; i <= end; i++) {
              if (!result.includes(i)) result.push(i)
            }
          }
        } else {
          const index = parseInt(range) - 1
          if (!isNaN(index) && index >= 0 && index < fileData.headers.length) {
            if (!result.includes(index)) result.push(index)
          }
        }
      }
      
      return result.sort((a, b) => a - b)
    } catch (error) {
      return []
    }
  }

  // 获取当前选中的字段
  const getCurrentSelectedFields = () => {
    if (useFieldRange) {
      return parseFieldRange(localFieldRange)
    }
    return selectedFields
  }

  // 生成字段表格列
  const fieldColumns = [
    {
      title: (
        <Checkbox
          checked={selectedFields.length === fileData.headers.length && fileData.headers.length > 0}
          indeterminate={selectedFields.length > 0 && selectedFields.length < fileData.headers.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
          disabled={useFieldRange}
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
          disabled={useFieldRange}
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
        const sampleData = fileData.preview
          ?.slice(0, 3)
          .map(row => row[fileData.headers[index]])
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

  // 验证字段范围格式
  const validateFieldRange = (rangeStr) => {
    if (!rangeStr) return { valid: false, message: '请输入字段范围' }
    
    const parsedFields = parseFieldRange(rangeStr)
    if (parsedFields.length === 0) {
      return { valid: false, message: '字段范围格式不正确或超出范围' }
    }
    
    return { valid: true, fields: parsedFields }
  }

  // 当前选择状态
  const currentSelectedFields = getCurrentSelectedFields()
  const isValid = currentSelectedFields.length > 0
  const totalDataRows = fileData.totalRows || 0
  const effectiveEndRow = endRow || totalDataRows

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
              选择要处理的数据字段和处理范围。您可以选择特定字段或使用字段范围表达式。
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
                <Text type="secondary">文件类型：</Text>
                <Tag color="blue">{fileData.fileType?.toUpperCase()}</Tag>
              </Col>
            </Row>
          </Card>

          {/* 字段选择方式 */}
          <Card title="选择方式">
            <Radio.Group 
              value={useFieldRange ? 'range' : 'individual'} 
              onChange={handleSelectionModeChange}
            >
              <Space direction="vertical">
                <Radio value="individual">
                  <Text strong>逐个选择字段</Text>
                  <br />
                  <Text type="secondary">从下方表格中勾选要处理的字段</Text>
                </Radio>
                <Radio value="range">
                  <Text strong>字段范围表达式</Text>
                  <br />
                  <Text type="secondary">使用范围表达式快速选择，如 "1-5" 或 "1,3,5-8"</Text>
                </Radio>
              </Space>
            </Radio.Group>

            {useFieldRange && (
              <div style={{ marginTop: 16 }}>
                <Text strong>字段范围：</Text>
                <Input
                  value={localFieldRange}
                  onChange={(e) => handleFieldRangeChange(e.target.value)}
                  placeholder="例如：1-5 或 1,3,5-8"
                  style={{ marginTop: 8 }}
                  status={localFieldRange && !validateFieldRange(localFieldRange).valid ? 'error' : ''}
                />
                {localFieldRange && !validateFieldRange(localFieldRange).valid && (
                  <Text type="danger" style={{ fontSize: 12 }}>
                    {validateFieldRange(localFieldRange).message}
                  </Text>
                )}
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    支持格式：单个数字(1)、范围(1-5)、组合(1,3,5-8)。列号从1开始计算。
                  </Text>
                </div>
              </div>
            )}
          </Card>

          {/* 字段列表 */}
          <Card 
            title={`可用字段 (${fileData.headers.length})`}
            extra={
              !useFieldRange && (
                <Space>
                  <Text type="secondary">
                    已选择 {selectedFields.length} 个字段
                  </Text>
                </Space>
              )
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
                      {currentSelectedFields.map(index => (
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
                    min={startRow}
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
                message={`将处理第 ${startRow} 到第 ${effectiveEndRow} 行，共 ${effectiveEndRow - startRow + 1} 行数据`}
                showIcon
              />
            </div>
          </Card>
        </Space>
      </Col>

      {/* 右侧配置说明 */}
      <Col span={8}>
        <Card title="配置说明" size="small" style={{ position: 'sticky', top: 24 }}>
          <Space direction="vertical" size="small">
            <div>
              <Text strong>字段选择：</Text>
              <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                <li><strong>逐个选择：</strong>从表格中勾选要处理的字段</li>
                <li><strong>范围表达式：</strong>使用简洁的表达式快速选择</li>
                <li><strong>最少要求：</strong>至少选择一个字段进行处理</li>
              </ul>
            </div>
            <div>
              <Text strong>范围表达式格式：</Text>
              <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                <li><strong>连续范围：</strong>"1-5" 表示第1到第5列</li>
                <li><strong>多个字段：</strong>"1,3,5" 表示第1、3、5列</li>
                <li><strong>混合格式：</strong>"1,3-5,8" 表示第1、3到5、第8列</li>
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
                <li>列号和行号都从1开始计算</li>
                <li>表格第一行是字段标题，不参与处理</li>
                <li>处理范围是指数据行，不包括标题行</li>
              </ul>
            </div>
            <Text type="secondary">
              💡 提示：合理设置处理范围可以避免一次性处理过多数据
            </Text>
          </Space>
        </Card>
      </Col>
    </Row>
  )
}

export default FieldSelection 