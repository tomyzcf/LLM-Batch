import React from 'react'
import { Layout, Steps, Typography, Button, Space, Tooltip } from 'antd'
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

const { Header, Content } = Layout
const { Title } = Typography

const STEPS = [
  {
    title: 'API配置',
    icon: <ApiOutlined />,
    description: '配置API提供商和认证信息'
  },
  {
    title: '数据上传',
    icon: <CloudUploadOutlined />,
    description: '上传并预览要处理的数据文件'
  },
  {
    title: '字段选择',
    icon: <TableOutlined />,
    description: '选择要处理的字段和数据范围'
  },
  {
    title: '提示词配置',
    icon: <EditOutlined />,
    description: '设置处理任务的提示词模板'
  },
  {
    title: '任务执行',
    icon: <PlayCircleOutlined />,
    description: '执行批处理任务并监控进度'
  },
  {
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
    // 允许点击已完成的步骤，或当前步骤，或验证通过时的下一步
    if (step < currentStep || step === currentStep || (step === currentStep + 1 && validateCurrentStep())) {
      setCurrentStep(step)
    }
    // 特殊处理：如果任务完成，允许直接跳转到结果页面
    if (step === 6 && taskStatus.currentStatus === 'completed') {
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

      <Content className="app-content">
        <div className="step-container">
          {/* 步骤指示器 */}
          <div style={{ padding: '24px 24px 0' }}>
            <Steps
              current={currentStep - 1}
              items={STEPS.map((step, index) => {
                const stepNum = index + 1
                const isClickable = stepNum < currentStep || 
                                   stepNum === currentStep || 
                                   (stepNum === currentStep + 1 && canProceed) ||
                                   (stepNum === 6 && taskStatus.currentStatus === 'completed')
                
                return {
                  ...step,
                  status: getStepStatus(stepNum),
                  onClick: isClickable ? () => handleStepClick(stepNum) : undefined,
                  style: { 
                    cursor: isClickable ? 'pointer' : 'default'
                  }
                }
              })}
              type="navigation"
              size="small"
            />
          </div>

          {/* 步骤内容 */}
          <div className="step-content">
            {renderStepContent()}
          </div>

          {/* 步骤操作按钮 */}
          {!isResultStep && (
            <div className="step-actions">
              <div>
                {!isFirstStep && (
                  <Button onClick={handlePrevious}>
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
                    >
                      下一步
                    </Button>
                  </Tooltip>
                )}
                {currentStep === 5 && taskStatus.currentStatus === 'completed' && (
                  <Button 
                    type="primary" 
                    onClick={() => setCurrentStep(6)}
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
  )
}

export default App 