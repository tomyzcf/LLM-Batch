import React from 'react'
import { Layout, Steps, Typography, Button, Space, Tooltip, Menu } from 'antd'
import { 
  ApiOutlined, 
  CloudUploadOutlined, 
  EditOutlined, 
  PlayCircleOutlined,
  HomeOutlined
} from '@ant-design/icons'
import useAppStore from './stores/appStore'

// 导入页面组件
import ApiConfig from './pages/ApiConfig'
import DataPreparation from './pages/DataPreparation'
import PromptConfig from './pages/PromptConfig'
import TaskExecution from './pages/TaskExecution'

const { Header, Content, Sider } = Layout
const { Title } = Typography

const STEPS = [
  {
    key: '1',
    title: '数据准备',
    icon: <CloudUploadOutlined />,
    description: '上传数据文件并选择处理字段和范围'
  },
  {
    key: '2',
    title: 'API配置',
    icon: <ApiOutlined />,
    description: '配置API提供商和认证信息'
  },
  {
    key: '3',
    title: '提示词配置',
    icon: <EditOutlined />,
    description: '设置处理任务的提示词模板'
  },
  {
    key: '4',
    title: '任务执行与结果',
    icon: <PlayCircleOutlined />,
    description: '执行批处理任务并查看处理结果'
  }
]

function App() {
  const { 
    currentStep, 
    setCurrentStep, 
    validateCurrentStep, 
    completedSteps,
    reset,
    taskStatus 
  } = useAppStore()

  // 渲染当前步骤的内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <DataPreparation />
      case 2:
        return <ApiConfig />
      case 3:
        return <PromptConfig />
      case 4:
        return <TaskExecution />
      default:
        return <DataPreparation />
    }
  }

  // 处理下一步
  const handleNext = () => {
    if (validateCurrentStep()) {
      setCurrentStep(Math.min(currentStep + 1, 4))
    }
  }

  // 处理上一步
  const handlePrevious = () => {
    setCurrentStep(Math.max(currentStep - 1, 1))
  }

  // 处理步骤点击
  const handleStepClick = (step) => {
    const stepNum = parseInt(step)
    // 允许点击已完成的步骤、当前步骤，或者验证通过时的下一步
    const isStepCompleted = completedSteps.includes(stepNum)
    const isCurrentStep = stepNum === currentStep
    const isNextValidStep = stepNum === currentStep + 1 && validateCurrentStep()
    const isTaskCompletedStep = stepNum === 4 && taskStatus.currentStatus === 'completed'
    
    if (isStepCompleted || isCurrentStep || isNextValidStep || isTaskCompletedStep) {
      setCurrentStep(stepNum)
    }
  }

  // 重新开始
  const handleRestart = () => {
    reset()
  }

  // 获取步骤状态
  const getStepStatus = (stepIndex) => {
    if (completedSteps.includes(stepIndex) || stepIndex < currentStep) return 'finish'
    if (stepIndex === currentStep) return 'process'
    if (stepIndex === 4 && taskStatus.currentStatus === 'completed') return 'finish'
    return 'wait'
  }

  // 当前步骤是否可以继续
  const canProceed = validateCurrentStep()
  const isLastStep = currentStep === 4
  const isFirstStep = currentStep === 1
  const isExecutionStep = currentStep === 4

  // 生成侧边栏菜单项
  const menuItems = STEPS.map((step, index) => {
    const stepNum = index + 1
    const isStepCompleted = completedSteps.includes(stepNum)
    const isCurrentStep = stepNum === currentStep
    const isNextValidStep = stepNum === currentStep + 1 && canProceed
    const isTaskCompletedStep = stepNum === 4 && taskStatus.currentStatus === 'completed'
    const isPreviousValidStep = stepNum < currentStep  // 允许回到之前的步骤
    
    // 简化点击判断逻辑：当前步骤、已完成步骤、验证后的下一步、之前的步骤都可点击
    const isClickable = isCurrentStep || isStepCompleted || isNextValidStep || isTaskCompletedStep || isPreviousValidStep
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
            {(taskStatus.currentStatus === 'completed' || isExecutionStep) && (
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
              {!isExecutionStep && (
                <div className="step-actions">
                  <div>
                    {!isFirstStep && (
                      <Button onClick={handlePrevious} size="large">
                        上一步
                      </Button>
                    )}
                  </div>
                  <div>
                    {currentStep < 4 && (
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