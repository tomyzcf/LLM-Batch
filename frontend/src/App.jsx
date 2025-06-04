import React from 'react'
import { Layout, Steps, Typography, Button, Space, Tooltip, Menu } from 'antd'
import { 
  ApiOutlined, 
  CloudUploadOutlined, 
  TableOutlined, 
  EditOutlined, 
  PlayCircleOutlined,
  CheckCircleOutlined,
  HomeOutlined
} from '@ant-design/icons'
import useAppStore from './stores/appStore'

// 导入页面组件
import ApiConfig from './pages/ApiConfig'
import DataUpload from './pages/DataUpload'
import FieldSelection from './pages/FieldSelection'
import PromptConfig from './pages/PromptConfig'
import TaskExecution from './pages/TaskExecution'
import Results from './pages/Results'

const { Header, Content, Sider } = Layout
const { Title } = Typography

const STEPS = [
  {
    key: '1',
    title: 'API配置',
    icon: <ApiOutlined />,
    description: '配置API提供商和认证信息'
  },
  {
    key: '2',
    title: '数据上传',
    icon: <CloudUploadOutlined />,
    description: '上传并预览要处理的数据文件'
  },
  {
    key: '3',
    title: '字段选择',
    icon: <TableOutlined />,
    description: '选择要处理的字段和数据范围'
  },
  {
    key: '4',
    title: '提示词配置',
    icon: <EditOutlined />,
    description: '设置处理任务的提示词模板'
  },
  {
    key: '5',
    title: '任务执行',
    icon: <PlayCircleOutlined />,
    description: '执行批处理任务并监控进度'
  },
  {
    key: '6',
    title: '处理结果',
    icon: <CheckCircleOutlined />,
    description: '查看处理结果和统计信息'
  }
]

function App() {
  const { 
    currentStep, 
    setCurrentStep, 
    validateCurrentStep, 
    reset,
    taskStatus 
  } = useAppStore()

  // 渲染当前步骤的内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <ApiConfig />
      case 2:
        return <DataUpload />
      case 3:
        return <FieldSelection />
      case 4:
        return <PromptConfig />
      case 5:
        return <TaskExecution />
      case 6:
        return <Results />
      default:
        return <ApiConfig />
    }
  }

  // 处理下一步
  const handleNext = () => {
    if (validateCurrentStep()) {
      setCurrentStep(Math.min(currentStep + 1, 6))
    }
  }

  // 处理上一步
  const handlePrevious = () => {
    // 如果在结果页面，返回到任务执行页面
    if (currentStep === 6) {
      setCurrentStep(5)
    } else {
      setCurrentStep(Math.max(currentStep - 1, 1))
    }
  }

  // 处理步骤点击
  const handleStepClick = (step) => {
    const stepNum = parseInt(step)
    // 允许点击已完成的步骤，或当前步骤，或验证通过时的下一步
    if (stepNum < currentStep || stepNum === currentStep || (stepNum === currentStep + 1 && validateCurrentStep())) {
      setCurrentStep(stepNum)
    }
    // 特殊处理：如果任务完成，允许直接跳转到结果页面
    if (stepNum === 6 && taskStatus.currentStatus === 'completed') {
      setCurrentStep(6)
    }
  }

  // 重新开始
  const handleRestart = () => {
    reset()
  }

  // 获取步骤状态
  const getStepStatus = (stepIndex) => {
    if (stepIndex < currentStep) return 'finish'
    if (stepIndex === currentStep) return 'process'
    if (stepIndex === 6 && taskStatus.currentStatus === 'completed') return 'finish'
    return 'wait'
  }

  // 当前步骤是否可以继续
  const canProceed = validateCurrentStep()
  const isLastStep = currentStep === 6
  const isFirstStep = currentStep === 1
  const isResultStep = currentStep === 6

  // 生成侧边栏菜单项
  const menuItems = STEPS.map((step, index) => {
    const stepNum = index + 1
    const isClickable = stepNum < currentStep || 
                       stepNum === currentStep || 
                       (stepNum === currentStep + 1 && canProceed) ||
                       (stepNum === 6 && taskStatus.currentStatus === 'completed')
    
    const status = getStepStatus(stepNum)
    
    return {
      key: step.key,
      icon: step.icon,
      label: (
        <div className="sidebar-menu-item">
          <div className="sidebar-step-title">{step.title}</div>
          <div className="sidebar-step-desc">{step.description}</div>
        </div>
      ),
      disabled: !isClickable,
      className: `sidebar-step-${status}${stepNum === currentStep ? ' sidebar-step-current' : ''}`
    }
  })

  return (
    <Layout className="app-container">
      <Header className="app-header">
        <div style={{ padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
              LLM批处理工具
            </Title>
          </div>
          <Space>
            {(taskStatus.currentStatus === 'completed' || isResultStep) && (
              <Button 
                icon={<HomeOutlined />} 
                onClick={handleRestart}
                type="primary"
              >
                重新开始
              </Button>
            )}
          </Space>
        </div>
      </Header>

      <Layout>
        {/* 左侧导航 */}
        <Sider 
          width={300} 
          theme="light" 
          className="app-sidebar"
        >
          <div className="sidebar-container">
            <div className="sidebar-header">
              <Title level={5} style={{ margin: '16px 0', color: '#1890ff' }}>
                配置向导
              </Title>
            </div>
            <Menu
              mode="inline"
              selectedKeys={[currentStep.toString()]}
              items={menuItems}
              onClick={({ key }) => handleStepClick(key)}
              className="sidebar-menu"
            />
          </div>
        </Sider>

        {/* 主内容区 */}
        <Layout>
          <Content className="app-content">
            <div className="main-content">
              {/* 步骤内容 */}
              <div className="step-content">
                {renderStepContent()}
              </div>

              {/* 步骤操作按钮 */}
              {!isResultStep && (
                <div className="step-actions">
                  <div>
                    {!isFirstStep && (
                      <Button onClick={handlePrevious} size="large">
                        上一步
                      </Button>
                    )}
                  </div>
                  <div>
                    {currentStep < 5 && (
                      <Tooltip title={!canProceed ? '请完成当前步骤的必填项' : ''}>
                        <Button 
                          type="primary" 
                          onClick={handleNext}
                          disabled={!canProceed}
                          size="large"
                        >
                          下一步
                        </Button>
                      </Tooltip>
                    )}
                    {currentStep === 5 && taskStatus.currentStatus === 'completed' && (
                      <Button 
                        type="primary" 
                        onClick={() => setCurrentStep(6)}
                        size="large"
                      >
                        查看结果
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App 