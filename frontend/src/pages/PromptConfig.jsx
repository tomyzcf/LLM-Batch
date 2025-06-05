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
    fileData,
    setCurrentStep 
  } = useAppStore()
  
  const [jsonError, setJsonError] = useState('')
  const [previewVisible, setPreviewVisible] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  // 初始化默认值
  useEffect(() => {
    if (!promptConfig.system && !promptConfig.task) {
      setPromptConfig({
        system: '你是一个专业的AI助手，能够准确理解和处理用户的数据请求。',
        task: '请处理以下数据：\n\n{input_text}',
        output: '{"result": "处理结果", "status": "处理状态"}',
        variables: '',
        examples: ''
      })
    }
  }, [promptConfig, setPromptConfig])

  // 处理JSON内容更改
  const handleContentChange = (field, value) => {
    const newConfig = { ...promptConfig }
    newConfig[field] = value
    
    // 验证JSON格式
    if (field === 'output' || field === 'variables') {
      if (value.trim()) {
        try {
          JSON.parse(value)
          setJsonError('')
        } catch (error) {
          setJsonError(`${field === 'output' ? '输出格式' : '变量定义'}必须是有效的JSON格式`)
        }
      } else {
        setJsonError('')
      }
    }
    
    setPromptConfig(newConfig)
  }

  // 应用模板
  const handleApplyTemplate = (templateKey) => {
    const template = PROMPT_TEMPLATES[templateKey]
    if (template) {
      setPromptConfig({
        system: template.content.system,
        task: template.content.task,
        output: JSON.stringify(template.content.output, null, 2),
        variables: template.content.variables ? JSON.stringify(template.content.variables, null, 2) : '',
        examples: template.content.examples || ''
      })
      setSelectedTemplate(template.name)
      setJsonError('')
      message.success(`已应用模板：${template.name}`)
    }
  }

  // 验证提示词配置
  const validatePromptConfig = () => {
    const { system, task, output } = promptConfig
    if (!system || !task || !output) {
      return { valid: false, message: '请填写系统角色、任务描述和输出格式' }
    }
    if (jsonError) {
      return { valid: false, message: jsonError }
    }
    
    // 验证输出格式是否为有效JSON
    try {
      JSON.parse(output)
    } catch (error) {
      return { valid: false, message: '输出格式必须是有效的JSON格式' }
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
    const { system, task, variables } = promptConfig
    let preview = `System: ${system}\n\nTask: ${task}`
    
    if (variables && variables.trim()) {
      try {
        const varsObj = JSON.parse(variables)
        preview += `\n\nVariables: ${JSON.stringify(varsObj, null, 2)}`
      } catch (error) {
        preview += `\n\nVariables: ${variables}`
      }
    }
    
    // 模拟变量替换
    preview = preview.replace('{input_text}', '[这里将显示实际的数据字段内容]')
    
    return preview
  }

  const validation = validatePromptConfig()
  const isValid = validation.valid

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Row gutter={24}>
        {/* 左侧主要内容 */}
        <Col span={18}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 页面标题和说明 */}
            <div>
              <Title level={4}>
                <EditOutlined style={{ marginRight: 8 }} />
                提示词配置
              </Title>
              <Paragraph type="secondary">
                配置用于处理数据的提示词模板。使用JSON格式的结构化配置，可节省60-80%的token消耗。
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

            {/* JSON格式配置 */}
            <Card title="提示词配置" extra={
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
                  onClick={() => copyToClipboard(JSON.stringify(promptConfig, null, 2))}
                >
                  复制JSON
                </Button>
              </Space>
            }>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {/* System字段 */}
                <div>
                  <Text strong>System * <Text type="secondary">(系统角色描述)</Text></Text>
                  <TextArea
                    value={promptConfig.system || ''}
                    onChange={(e) => handleContentChange('system', e.target.value)}
                    placeholder="定义AI助手的身份和基本规则..."
                    rows={3}
                    style={{ marginTop: 8 }}
                  />
                </div>

                {/* Task字段 */}
                <div>
                  <Text strong>Task * <Text type="secondary">(任务描述)</Text></Text>
                  <TextArea
                    value={promptConfig.task || ''}
                    onChange={(e) => handleContentChange('task', e.target.value)}
                    placeholder="描述要执行的具体任务，使用 {input_text} 代表输入数据..."
                    rows={4}
                    style={{ marginTop: 8 }}
                  />
                </div>

                {/* Output字段 */}
                <div>
                  <Text strong>Output * <Text type="secondary">(输出格式定义)</Text></Text>
                  <TextArea
                    value={promptConfig.output || ''}
                    onChange={(e) => handleContentChange('output', e.target.value)}
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
                    value={promptConfig.variables || ''}
                    onChange={(e) => handleContentChange('variables', e.target.value)}
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
                    value={promptConfig.examples || ''}
                    onChange={(e) => handleContentChange('examples', e.target.value)}
                    placeholder="提供一些示例输入和输出..."
                    rows={3}
                    style={{ marginTop: 8 }}
                  />
                </div>
              </Space>
            </Card>

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
                action={
                  <Button 
                    type="primary" 
                    onClick={() => setCurrentStep(5)}
                  >
                    下一步：任务执行
                  </Button>
                }
              />
            )}
          </Space>
        </Col>

        {/* 右侧配置说明 */}
        <Col span={6}>
          <Card title="配置说明" size="small" style={{ position: 'sticky', top: 24 }}>
            <Space direction="vertical" size="small">
              <div>
                <Text strong>配置字段：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li><strong>System*：</strong>定义AI助手的身份和基本规则</li>
                  <li><strong>Task*：</strong>描述要执行的具体任务</li>
                  <li><strong>Output*：</strong>定义期望的输出JSON格式</li>
                  <li><strong>Variables：</strong>可选，定义可复用的变量</li>
                  <li><strong>Examples：</strong>可选，提供示例输入输出</li>
                </ul>
              </div>
              <div>
                <Text strong>变量使用：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li><strong>数据占位符：</strong>使用 {`{input_text}`} 代表要处理的数据</li>
                  <li><strong>自定义变量：</strong>在variables中定义，用 {`{变量名}`} 引用</li>
                  <li><strong>变量作用域：</strong>可在system和task字段中使用</li>
                </ul>
              </div>
              <div>
                <Text strong>最佳实践：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li>输出格式必须是有效的JSON对象</li>
                  <li>在task中明确指定数据处理要求</li>
                  <li>使用examples提供高质量示例</li>
                  <li>合理使用变量减少重复内容</li>
                </ul>
              </div>
              <div>
                <Text strong>预设模板：</Text>
                <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                  <li><strong>数据提取：</strong>适合结构化信息提取</li>
                  <li><strong>文本分析：</strong>适合情感分析、分类等</li>
                  <li><strong>内容生成：</strong>适合文本生成、改写等</li>
                </ul>
              </div>
              <Text type="secondary">
                💡 提示：JSON格式更适合批量处理，能显著节省token消耗
              </Text>
            </Space>
          </Card>
        </Col>

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
      </Row>
    </div>
  )
}

export default PromptConfig 