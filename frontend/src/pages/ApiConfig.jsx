import React, { useState, useEffect } from 'react'
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
  message,
  Row,
  Col
} from 'antd'
import { ApiOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons'
import useAppStore from '../stores/appStore'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// LLM API配置
const LLM_PROVIDERS = {
  deepseek: {
    name: 'DeepSeek',
    api_url: 'https://api.deepseek.com/v1/chat/completions',
    models: [
      { label: 'deepseek-chat（V3）', value: 'deepseek-chat' },
      { label: 'deepseek-reasoner（R1）', value: 'deepseek-reasoner' }
    ],
    requiresModel: true
  },
  aliyun_llm: {
    name: '阿里云百炼 (LLM)',
    api_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: [],
    requiresModel: true,
    modelPlaceholder: '例如：qwen-turbo, qwen-plus, qwen-max'
  },
  baidu_qianfan: {
    name: '百度千帆',
    api_url: 'https://qianfan.baidubce.com/v2/chat/completions',
    models: [],
    requiresModel: true,
    modelPlaceholder: '例如：ernie-4.0-8k, ernie-3.5-8k'
  },
  custom: {
    name: '自定义配置',
    api_url: '',
    models: [],
    requiresModel: true,
    modelPlaceholder: '请输入模型名称'
  }
}

// Agent API配置
const AGENT_PROVIDERS = {
  aliyun_agent: {
    name: '阿里云百炼 (Agent)',
    api_url: 'https://dashscope.aliyuncs.com',
    requiresAppId: true
  }
}

function ApiConfig() {
  const { apiConfig, setApiConfig } = useAppStore()
  const [form] = Form.useForm()
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [apiType, setApiType] = useState(apiConfig?.api_type || 'llm') // 默认LLM类型
  const [selectedProvider, setSelectedProvider] = useState(apiConfig?.provider || 'deepseek') // 默认DeepSeek

  // 初始化表单
  useEffect(() => {
    // 确保使用store中的配置
    const currentApiType = apiConfig?.api_type || 'llm'
    const currentProvider = apiConfig?.provider || 'deepseek'
    
    setApiType(currentApiType)
    setSelectedProvider(currentProvider)
    
    // 设置表单值
    form.setFieldsValue({
      api_type: currentApiType,
      provider: currentProvider,
      api_url: apiConfig?.api_url || 'https://api.deepseek.com/v1/chat/completions',
      api_key: apiConfig?.api_key || '',
      model: apiConfig?.model || 'deepseek-chat',
      app_id: apiConfig?.app_id || ''
    })
  }, [apiConfig, form])

  // 处理API类型变化
  const handleApiTypeChange = (e) => {
    const newApiType = e.target.value
    setApiType(newApiType)
    
    // 重置相关字段
    if (newApiType === 'llm') {
      const defaultProvider = 'deepseek'
      setSelectedProvider(defaultProvider)
      const config = {
        api_type: newApiType,
        provider: defaultProvider,
        api_url: LLM_PROVIDERS[defaultProvider].api_url,
        api_key: apiConfig?.api_key || '',
        model: 'deepseek-chat', // 设置DeepSeek默认模型
        app_id: ''
      }
      setApiConfig(config)
      form.setFieldsValue(config)
    } else {
      const defaultProvider = 'aliyun_agent'
      setSelectedProvider(defaultProvider)
      const config = {
        api_type: newApiType,
        provider: defaultProvider,
        api_url: AGENT_PROVIDERS[defaultProvider].api_url,
        api_key: apiConfig?.api_key || '',
        model: '',
        app_id: ''
      }
      setApiConfig(config)
      form.setFieldsValue(config)
    }
    
    setValidationResult(null)
  }

  // 处理提供商选择变化
  const handleProviderChange = (provider) => {
    setSelectedProvider(provider)
    
    let config = { ...apiConfig, provider }
    
    if (apiType === 'llm') {
      const providerConfig = LLM_PROVIDERS[provider]
      config.api_url = providerConfig.api_url
      config.model = provider === 'deepseek' ? 'deepseek-chat' : '' // 设置DeepSeek默认模型
      config.app_id = ''
    } else {
      const providerConfig = AGENT_PROVIDERS[provider]
      config.api_url = providerConfig.api_url
      config.model = ''
      config.app_id = ''
    }
    
    setApiConfig(config)
    form.setFieldsValue(config)
    setValidationResult(null)
  }

  // 处理表单值变化
  const handleFormChange = (changedValues, allValues) => {
    setApiConfig({ ...apiConfig, ...allValues })
    setValidationResult(null)
  }

  // 验证API配置
  const validateApiConfig = async () => {
    try {
      setIsValidating(true)
      setValidationResult(null)

      // 模拟API验证请求
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // 验证必填字段
      const { api_url, api_key, model, app_id } = apiConfig
      
      if (!api_url || !api_key) {
        throw new Error('请填写API URL和API密钥')
      }

      if (apiType === 'llm' && !model) {
        throw new Error('请填写模型名称')
      }

      if (apiType === 'agent' && !app_id) {
        throw new Error('请填写应用ID')
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

  // 获取当前提供商配置
  const getCurrentProviderConfig = () => {
    if (apiType === 'llm') {
      return LLM_PROVIDERS[selectedProvider]
    } else {
      return AGENT_PROVIDERS[selectedProvider]
    }
  }

  const currentProvider = getCurrentProviderConfig()

  return (
    <Row gutter={24}>
      {/* 左侧主要内容 */}
      <Col span={16}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 页面标题和说明 */}
          <div>
            <Title level={4}>
              <ApiOutlined style={{ marginRight: 8 }} />
              API配置
            </Title>
            <Paragraph type="secondary">
              选择您的大语言模型API类型和提供商，并配置相应的认证信息。
            </Paragraph>
          </div>

          {/* API类型选择 */}
          <Card title="选择API类型" size="small">
            <Radio.Group value={apiType} onChange={handleApiTypeChange} size="large">
              <Space direction="vertical" size="middle">
                <Radio value="llm">
                  <div>
                    <div style={{ fontWeight: 600 }}>通用LLM API</div>
                    <div style={{ fontSize: 13, color: '#8c8c8c' }}>
                      支持OpenAI兼容的聊天接口，包括DeepSeek、阿里云百炼、百度千帆等
                    </div>
                  </div>
                </Radio>
                <Radio value="agent">
                  <div>
                    <div style={{ fontWeight: 600 }}>Agent API</div>
                    <div style={{ fontSize: 13, color: '#8c8c8c' }}>
                      专门的智能体接口，目前支持阿里云百炼Agent
                    </div>
                  </div>
                </Radio>
              </Space>
            </Radio.Group>
          </Card>

          {/* 提供商选择 */}
          <Card title={`选择${apiType === 'llm' ? 'LLM' : 'Agent'}提供商`} size="small">
            <Radio.Group 
              value={selectedProvider} 
              onChange={(e) => handleProviderChange(e.target.value)}
              style={{ width: '100%' }}
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
                {Object.entries(apiType === 'llm' ? LLM_PROVIDERS : AGENT_PROVIDERS).map(([key, provider]) => (
                  <Radio.Button key={key} value={key} style={{ height: 'auto', padding: '16px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontWeight: 600, marginBottom: 6 }}>{provider.name}</div>
                      {provider.api_url && (
                        <div style={{ fontSize: 12, color: '#8c8c8c', wordBreak: 'break-all' }}>
                          {provider.api_url.length > 35 ? provider.api_url.substring(0, 35) + '...' : provider.api_url}
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
              onValuesChange={handleFormChange}
              size="large"
            >
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
                  placeholder="API服务地址"
                  disabled={selectedProvider !== 'custom'}
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
                />
              </Form.Item>

              {/* 模型名称 - 仅LLM类型显示 */}
              {apiType === 'llm' && (
                <Form.Item
                  label="模型名称"
                  name="model"
                  rules={[{ required: true, message: '请输入模型名称' }]}
                  tooltip="要使用的具体模型名称"
                >
                  {currentProvider?.models && currentProvider.models.length > 0 ? (
                    <Select 
                      placeholder="选择模型"
                      options={currentProvider.models}
                      allowClear
                    />
                  ) : (
                    <Input 
                      placeholder={currentProvider?.modelPlaceholder || '请输入模型名称'}
                    />
                  )}
                </Form.Item>
              )}

              {/* 应用ID - 仅Agent类型显示 */}
              {apiType === 'agent' && (
                <Form.Item
                  label="应用ID (App ID)"
                  name="app_id"
                  rules={[{ required: true, message: '请输入应用ID' }]}
                  tooltip="阿里云百炼平台的应用ID"
                >
                  <Input 
                    placeholder="请输入应用ID"
                  />
                </Form.Item>
              )}
            </Form>

            {/* 验证按钮和结果 */}
            <div style={{ marginTop: 32 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  size="large"
                  loading={isValidating}
                  onClick={validateApiConfig}
                  icon={isValidating ? <LoadingOutlined /> : <CheckCircleOutlined />}
                  disabled={!apiConfig.api_url || !apiConfig.api_key || 
                    (apiType === 'llm' && !apiConfig.model) ||
                    (apiType === 'agent' && !apiConfig.app_id)}
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
        </Space>
      </Col>

      {/* 右侧配置说明 */}
      <Col span={8}>
        <Card title="配置说明" size="small" style={{ position: 'sticky', top: 24 }}>
          <Space direction="vertical" size="small">
            <div>
              <Text strong>通用LLM API：</Text>
              <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                <li><strong>DeepSeek：</strong>支持 deepseek-chat（V3）和 deepseek-reasoner（R1）模型</li>
                <li><strong>阿里云百炼：</strong>需要手动输入模型名称，如 qwen-turbo、qwen-plus、qwen-max</li>
                <li><strong>百度千帆：</strong>需要手动输入模型名称，如 ernie-4.0-8k、ernie-3.5-8k</li>
                <li><strong>自定义配置：</strong>支持任何OpenAI兼容的API接口</li>
              </ul>
            </div>
            <div>
              <Text strong>Agent API：</Text>
              <ul style={{ marginTop: 8, marginLeft: 16, color: '#666' }}>
                <li><strong>阿里云百炼Agent：</strong>使用智能体应用，需要提供App ID</li>
              </ul>
            </div>
            <Text type="secondary">
              💡 提示：API密钥信息仅在本地使用，不会上传到服务器
            </Text>
          </Space>
        </Card>
      </Col>
    </Row>
  )
}

export default ApiConfig 