import React, { useState, useEffect } from 'react'
import { 
  Typography, 
  Card, 
  Space, 
  Radio, 
  Input, 
  Button, 
  Alert, 
  Row, 
  Col,
  Select,
  message,
  Tooltip,
  Modal
} from 'antd'
import { 
  EditOutlined, 
  FileTextOutlined, 
  BulbOutlined, 
  EyeOutlined,
  CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import useAppStore from '../stores/appStore'

// 导入模板
import dataExtractionTemplate from '../templates/dataExtraction.json'
import contentGenerationTemplate from '../templates/contentGeneration.json'
import classificationTemplate from '../templates/classification.json'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select

// 预设模板
const PROMPT_TEMPLATES = {
  dataExtraction: dataExtractionTemplate,
  contentGeneration: contentGenerationTemplate,
  classification: classificationTemplate
}

function PromptConfig() {
  const { 
    promptConfig, 
    setPromptConfig,
    fileData 
  } = useAppStore()
  
  const [jsonError, setJsonError] = useState('')
  const [previewVisible, setPreviewVisible] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  // 初始化默认值
  useEffect(() => {
    if (!promptConfig.content.system && !promptConfig.textContent) {
      setPromptConfig({
        format: 'json',
        content: {
          system: '你是一个专业的AI助手，能够准确理解和处理用户的数据请求。',
          task: '请处理以下数据：\n\n{input_text}',
          output: {
            result: '处理结果',
            status: '处理状态'
          }
        }
      })
    }
  }, [promptConfig, setPromptConfig])

  // 处理格式切换
  const handleFormatChange = (e) => {
    const format = e.target.value
    setPromptConfig({ format })
    setJsonError('')
  }

  // 处理JSON内容更改
  const handleJsonContentChange = (field, value) => {
    const newContent = { ...promptConfig.content }
    
    if (field === 'output') {
      // 处理输出格式，尝试解析为JSON
      try {
        const parsed = JSON.parse(value)
        newContent[field] = parsed
        setJsonError('')
      } catch (error) {
        newContent[field] = value
        if (value.trim()) {
          setJsonError('输出格式必须是有效的JSON格式')
        } else {
          setJsonError('')
        }
      }
    } else if (field === 'variables') {
      // 处理变量，尝试解析为JSON
      try {
        const parsed = JSON.parse(value || '{}')
        newContent[field] = parsed
        setJsonError('')
      } catch (error) {
        newContent[field] = value
        if (value.trim()) {
          setJsonError('变量定义必须是有效的JSON格式')
        } else {
          setJsonError('')
        }
      }
    } else {
      newContent[field] = value
    }
    
    setPromptConfig({ content: newContent })
  }

  // 处理文本内容更改
  const handleTextContentChange = (value) => {
    setPromptConfig({ textContent: value })
  }

  // 应用模板
  const handleApplyTemplate = (templateKey) => {
    const template = PROMPT_TEMPLATES[templateKey]
    if (template) {
      setPromptConfig({
        format: 'json',
        content: { ...template.content },
        selectedTemplate: template.name
      })
      setSelectedTemplate(template.name)
      setJsonError('')
      message.success(`已应用模板：${template.name}`)
    }
  }

  // 格式化JSON显示
  const formatJsonForDisplay = (obj) => {
    if (typeof obj === 'string') return obj
    return JSON.stringify(obj, null, 2)
  }

  // 验证提示词配置
  const validatePromptConfig = () => {
    if (promptConfig.format === 'json') {
      const { system, task, output } = promptConfig.content
      if (!system || !task || !output) {
        return { valid: false, message: 'JSON格式的提示词必须包含 system、task 和 output 字段' }
      }
      if (jsonError) {
        return { valid: false, message: jsonError }
      }
    } else {
      if (!promptConfig.textContent || !promptConfig.textContent.trim()) {
        return { valid: false, message: '请输入提示词内容' }
      }
    }
    return { valid: true }
  }

  // 复制到剪贴板
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  // 生成预览内容
  const generatePreview = () => {
    if (promptConfig.format === 'json') {
      const { system, task, variables } = promptConfig.content
      let preview = `System: ${system}\n\nTask: ${task}`
      
      if (variables && Object.keys(variables).length > 0) {
        preview += `\n\nVariables: ${JSON.stringify(variables, null, 2)}`
      }
      
      // 模拟变量替换
      preview = preview.replace('{input_text}', '[这里将显示实际的数据字段内容]')
      
      return preview
    } else {
      return promptConfig.textContent?.replace('{input_text}', '[这里将显示实际的数据字段内容]') || ''
    }
  }

  const validation = validatePromptConfig()
  const isValid = validation.valid

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题和说明 */}
        <div>
          <Title level={4}>
            <EditOutlined style={{ marginRight: 8 }} />
            提示词配置
          </Title>
          <Paragraph type="secondary">
            配置用于处理数据的提示词模板。支持JSON格式（推荐）和纯文本格式，JSON格式可节省60-80%的token消耗。
          </Paragraph>
        </div>

        {/* 数据文件信息 */}
        {fileData.fileName && (
          <Card size="small">
            <Space>
              <Text type="secondary">当前文件：</Text>
              <Text strong>{fileData.fileName}</Text>
              <Text type="secondary">({fileData.totalRows} 行数据)</Text>
            </Space>
          </Card>
        )}

        {/* 模板选择 */}
        <Card title="选择模板" extra={
          <Tooltip title="使用预设模板快速开始">
            <BulbOutlined />
          </Tooltip>
        }>
          <Row gutter={16}>
            {Object.entries(PROMPT_TEMPLATES).map(([key, template]) => (
              <Col span={8} key={key}>
                <Card 
                  size="small" 
                  hoverable
                  onClick={() => handleApplyTemplate(key)}
                  style={{ cursor: 'pointer' }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <Text strong>{template.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {template.description}
                    </Text>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
          
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Text type="secondary">点击模板卡片即可应用，或继续使用自定义配置</Text>
          </div>
        </Card>

        {/* 格式选择 */}
        <Card title="提示词格式">
          <Radio.Group value={promptConfig.format} onChange={handleFormatChange}>
            <Space direction="vertical">
              <Radio value="json">
                <Text strong>JSON格式（推荐）</Text>
                <br />
                <Text type="secondary">结构化配置，支持变量替换，节省token消耗</Text>
              </Radio>
              <Radio value="txt">
                <Text strong>纯文本格式</Text>
                <br />
                <Text type="secondary">简单直接，适合简单的提示词</Text>
              </Radio>
            </Space>
          </Radio.Group>
        </Card>

        {/* JSON格式配置 */}
        {promptConfig.format === 'json' && (
          <Card title="JSON配置" extra={
            <Space>
              <Button 
                size="small" 
                icon={<EyeOutlined />}
                onClick={() => setPreviewVisible(true)}
              >
                预览
              </Button>
              <Button 
                size="small" 
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(JSON.stringify(promptConfig.content, null, 2))}
              >
                复制
              </Button>
            </Space>
          }>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {/* System字段 */}
              <div>
                <Text strong>System * <Text type="secondary">(系统角色描述)</Text></Text>
                <TextArea
                  value={promptConfig.content.system || ''}
                  onChange={(e) => handleJsonContentChange('system', e.target.value)}
                  placeholder="定义AI助手的身份和基本规则..."
                  rows={3}
                  style={{ marginTop: 8 }}
                />
              </div>

              {/* Task字段 */}
              <div>
                <Text strong>Task * <Text type="secondary">(任务描述)</Text></Text>
                <TextArea
                  value={promptConfig.content.task || ''}
                  onChange={(e) => handleJsonContentChange('task', e.target.value)}
                  placeholder="描述要执行的具体任务，使用 {input_text} 代表输入数据..."
                  rows={4}
                  style={{ marginTop: 8 }}
                />
              </div>

              {/* Output字段 */}
              <div>
                <Text strong>Output * <Text type="secondary">(输出格式定义)</Text></Text>
                <TextArea
                  value={formatJsonForDisplay(promptConfig.content.output)}
                  onChange={(e) => handleJsonContentChange('output', e.target.value)}
                  placeholder='{"result": "处理结果", "status": "状态"}'
                  rows={6}
                  style={{ marginTop: 8 }}
                  status={jsonError && jsonError.includes('输出格式') ? 'error' : ''}
                />
              </div>

              {/* Variables字段（可选） */}
              <div>
                <Text strong>Variables <Text type="secondary">(变量定义，可选)</Text></Text>
                <TextArea
                  value={formatJsonForDisplay(promptConfig.content.variables || {})}
                  onChange={(e) => handleJsonContentChange('variables', e.target.value)}
                  placeholder='{"language": "中文", "style": "正式"}'
                  rows={3}
                  style={{ marginTop: 8 }}
                  status={jsonError && jsonError.includes('变量定义') ? 'error' : ''}
                />
              </div>

              {/* Examples字段（可选） */}
              <div>
                <Text strong>Examples <Text type="secondary">(示例数据，可选)</Text></Text>
                <TextArea
                  value={promptConfig.content.examples || ''}
                  onChange={(e) => handleJsonContentChange('examples', e.target.value)}
                  placeholder="提供一些示例输入和输出..."
                  rows={3}
                  style={{ marginTop: 8 }}
                />
              </div>
            </Space>
          </Card>
        )}

        {/* 纯文本格式配置 */}
        {promptConfig.format === 'txt' && (
          <Card title="文本配置" extra={
            <Space>
              <Button 
                size="small" 
                icon={<EyeOutlined />}
                onClick={() => setPreviewVisible(true)}
              >
                预览
              </Button>
              <Button 
                size="small" 
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(promptConfig.textContent || '')}
              >
                复制
              </Button>
            </Space>
          }>
            <TextArea
              value={promptConfig.textContent || ''}
              onChange={(e) => handleTextContentChange(e.target.value)}
              placeholder="输入您的提示词内容...&#10;&#10;使用 {input_text} 代表要处理的数据字段内容"
              rows={12}
              style={{ fontFamily: 'monospace' }}
            />
          </Card>
        )}

        {/* 错误提示 */}
        {!isValid && (
          <Alert
            type="error"
            message="配置验证失败"
            description={validation.message}
            showIcon
          />
        )}

        {/* 配置有效提示 */}
        {isValid && (
          <Alert
            type="success"
            message="提示词配置有效"
            description="配置格式正确，可以进行下一步"
            icon={<CheckCircleOutlined />}
            showIcon
          />
        )}

        {/* 配置说明 */}
        <Card title="配置说明" size="small">
          <Space direction="vertical" size="small">
            <Text>• <strong>JSON格式优势：</strong> 结构清晰，支持变量替换，相比纯文本节省60-80% token消耗</Text>
            <Text>• <strong>必填字段：</strong> system（角色）、task（任务）、output（输出格式）</Text>
            <Text>• <strong>变量替换：</strong> 在system和task中使用 {`{变量名}`} 格式，在variables中定义</Text>
            <Text>• <strong>输入占位符：</strong> 使用 {`{input_text}`} 代表要处理的数据字段内容</Text>
            <Text>• <strong>输出格式：</strong> 必须是有效的JSON对象，定义期望的返回结构</Text>
            <Text type="secondary">💡 提示：JSON格式更适合批量处理，建议优先使用</Text>
          </Space>
        </Card>

        {/* 预览模态框 */}
        <Modal
          title="提示词预览"
          open={previewVisible}
          onCancel={() => setPreviewVisible(false)}
          footer={[
            <Button key="copy" icon={<CopyOutlined />} onClick={() => {
              copyToClipboard(generatePreview())
              setPreviewVisible(false)
            }}>
              复制预览内容
            </Button>,
            <Button key="close" onClick={() => setPreviewVisible(false)}>
              关闭
            </Button>
          ]}
          width={800}
        >
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '6px',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            {generatePreview()}
          </div>
        </Modal>
      </Space>
    </div>
  )
}

export default PromptConfig 