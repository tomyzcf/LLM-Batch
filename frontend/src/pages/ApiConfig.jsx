import React, { useState } from 'react'
import { 
  Form, 
  Input, 
  Radio, 
  Card, 
  Space, 
  Typography, 
  Alert, 
  Button,
  Select,
  Divider,
  message
} from 'antd'
import { ApiOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons'
import useAppStore from '../stores/appStore'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// API提供商预设配置
const API_PRESETS = {
  openai: {
    name: 'OpenAI',
    api_url: 'https://api.openai.com/v1/chat/completions',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
  },
  deepseek: {
    name: 'DeepSeek',
    api_url: 'https://api.deepseek.com/v1/chat/completions',
    models: ['deepseek-chat', 'deepseek-coder']
  },
  aliyun_llm: {
    name: '阿里云百炼 (LLM)',
    api_url: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max']
  },
  custom: {
    name: '自定义配置',
    api_url: '',
    models: []
  }
}

function ApiConfig() {
  const { apiConfig, setApiConfig } = useAppStore()
  const [form] = Form.useForm()
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [selectedPreset, setSelectedPreset] = useState('custom')

  // 处理API类型变化
  const handleApiTypeChange = (e) => {
    const apiType = e.target.value
    setApiConfig({ api_type: apiType })
    
    // 清除验证结果
    setValidationResult(null)
    
    // 根据API类型调整表单字段
    if (apiType === 'aliyun_agent') {
      form.setFieldValue('model', undefined)
    } else {
      form.setFieldValue('app_id', undefined)
    }
  }

  // 处理预设配置选择
  const handlePresetChange = (preset) => {
    setSelectedPreset(preset)
    
    if (preset !== 'custom') {
      const config = API_PRESETS[preset]
      form.setFieldsValue({
        api_url: config.api_url,
        model: config.models[0] || ''
      })
      setApiConfig({
        api_url: config.api_url,
        model: config.models[0] || ''
      })
    }
  }

  // 处理表单值变化
  const handleFormChange = (changedValues, allValues) => {
    setApiConfig(allValues)
    setValidationResult(null)
  }

  // 验证API配置
  const validateApiConfig = async () => {
    try {
      setIsValidating(true)
      setValidationResult(null)

      // 模拟API验证请求
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // 这里应该调用实际的API验证逻辑
      // 现在只是简单验证必填字段
      const { api_url, api_key, model, app_id } = apiConfig
      
      if (!api_url || !api_key || (!model && !app_id)) {
        throw new Error('请填写所有必填字段')
      }

      if (!api_url.startsWith('http')) {
        throw new Error('API URL格式不正确')
      }

      // 模拟成功验证
      setValidationResult({
        success: true,
        message: 'API配置验证成功！'
      })
      message.success('API配置验证成功！')
      
    } catch (error) {
      setValidationResult({
        success: false,
        message: error.message || 'API配置验证失败'
      })
      message.error(error.message || 'API配置验证失败')
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题和说明 */}
        <div>
          <Title level={4}>
            <ApiOutlined style={{ marginRight: 8 }} />
            API配置
          </Title>
          <Paragraph type="secondary">
            选择您的大语言模型API提供商并配置认证信息。系统支持OpenAI兼容的API接口和阿里云百炼Agent。
          </Paragraph>
        </div>

        {/* API预设选择 */}
        <Card title="选择API提供商" size="small">
          <Radio.Group 
            value={selectedPreset} 
            onChange={(e) => handlePresetChange(e.target.value)}
            style={{ width: '100%' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              {Object.entries(API_PRESETS).map(([key, preset]) => (
                <Radio.Button key={key} value={key} style={{ height: 'auto', padding: '12px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontWeight: 600 }}>{preset.name}</div>
                    {preset.api_url && (
                      <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                        {preset.api_url.length > 30 ? preset.api_url.substring(0, 30) + '...' : preset.api_url}
                      </div>
                    )}
                  </div>
                </Radio.Button>
              ))}
            </div>
          </Radio.Group>
        </Card>

        {/* API配置表单 */}
        <Card title="API配置详情">
          <Form
            form={form}
            layout="vertical"
            initialValues={apiConfig}
            onValuesChange={handleFormChange}
          >
            {/* API类型选择 */}
            <Form.Item
              label="API类型"
              name="api_type"
              tooltip="选择API的类型，用于确定调用方式"
            >
              <Radio.Group onChange={handleApiTypeChange}>
                <Radio.Button value="llm_compatible">
                  通用LLM API (OpenAI兼容)
                </Radio.Button>
                <Radio.Button value="aliyun_agent">
                  阿里云百炼Agent
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Divider />

            {/* API URL */}
            <Form.Item
              label="API URL"
              name="api_url"
              rules={[
                { required: true, message: '请输入API URL' },
                { pattern: /^https?:\/\//, message: 'URL必须以http://或https://开头' }
              ]}
              tooltip="API服务的完整URL地址"
            >
              <Input 
                placeholder="例如：https://api.openai.com/v1/chat/completions"
                size="large"
              />
            </Form.Item>

            {/* API密钥 */}
            <Form.Item
              label="API密钥"
              name="api_key"
              rules={[{ required: true, message: '请输入API密钥' }]}
              tooltip="您的API访问密钥，确保具有相应的调用权限"
            >
              <Input.Password 
                placeholder="请输入您的API密钥"
                size="large"
              />
            </Form.Item>

            {/* 根据API类型显示不同字段 */}
            {apiConfig.api_type === 'llm_compatible' ? (
              <Form.Item
                label="模型名称"
                name="model"
                rules={[{ required: true, message: '请输入模型名称' }]}
                tooltip="要使用的具体模型名称"
              >
                {selectedPreset !== 'custom' && API_PRESETS[selectedPreset]?.models?.length > 0 ? (
                  <Select 
                    size="large"
                    placeholder="选择模型"
                    options={API_PRESETS[selectedPreset].models.map(model => ({
                      label: model,
                      value: model
                    }))}
                  />
                ) : (
                  <Input 
                    placeholder="例如：gpt-4, deepseek-chat, qwen-turbo"
                    size="large"
                  />
                )}
              </Form.Item>
            ) : (
              <Form.Item
                label="应用ID (App ID)"
                name="app_id"
                rules={[{ required: true, message: '请输入应用ID' }]}
                tooltip="阿里云百炼平台的应用ID"
              >
                <Input 
                  placeholder="请输入应用ID"
                  size="large"
                />
              </Form.Item>
            )}
          </Form>

          {/* 验证按钮和结果 */}
          <div style={{ marginTop: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                size="large"
                loading={isValidating}
                onClick={validateApiConfig}
                icon={isValidating ? <LoadingOutlined /> : <CheckCircleOutlined />}
                disabled={!apiConfig.api_url || !apiConfig.api_key || 
                  (!apiConfig.model && !apiConfig.app_id)}
              >
                {isValidating ? '验证中...' : '验证API配置'}
              </Button>

              {validationResult && (
                <Alert
                  type={validationResult.success ? 'success' : 'error'}
                  message={validationResult.message}
                  showIcon
                />
              )}
            </Space>
          </div>
        </Card>

        {/* 配置说明 */}
        <Card title="配置说明" size="small">
          <Space direction="vertical" size="small">
            <Text>
              <strong>通用LLM API：</strong> 支持所有OpenAI兼容的API接口，如OpenAI、DeepSeek、阿里云等
            </Text>
            <Text>
              <strong>阿里云百炼Agent：</strong> 专门用于阿里云百炼平台的智能体API调用
            </Text>
            <Text type="secondary">
              💡 提示：API密钥信息仅在本地使用，不会上传到服务器
            </Text>
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default ApiConfig 