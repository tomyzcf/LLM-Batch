# LLM批处理工具 - 前端MVP开发方案

## 📋 项目概述

为LLM批处理工具开发一个用户友好的前端界面，支持通过浏览器进行API配置、数据上传、提示词设置和任务监控。最终目标是打包成exe文件，供无代码基础用户直接使用。


## 🎯 技术选型

### 前端框架：React + Vite
- **开发效率**：Vite提供极快的开发体验和热重载
- **生态丰富**：React组件生态成熟，学习资源丰富
- **打包友好**：与Electron集成良好，易于打包成桌面应用
- **可扩展性**：支持TypeScript，便于后期功能扩展

### UI组件库：Ant Design
- **企业级组件**：提供完整的表单、表格、文件上传等组件
- **中文支持**：组件和文档都有良好的中文本地化
- **设计统一**：减少自定义样式工作量
- **功能齐全**：内置进度条、状态标签、消息提示等组件

### 状态管理：Zustand
- **轻量简洁**：相比Redux更简单，学习成本低
- **TypeScript友好**：原生支持类型安全
- **性能良好**：足够支撑MVP阶段的状态管理需求

### 文件处理库
- **Papa Parse**：CSV文件解析和预览
- **SheetJS**：Excel文件读取和处理
- **前端解析**：无需后端API，直接在浏览器中处理文件

### 桌面应用框架：Electron
- **跨平台**：支持Windows、macOS、Linux
- **Web技术栈**：复用前端开发技能
- **原生集成**：可调用系统API和本地Python脚本


🚀 前端开发分步计划
阶段1：项目基础搭建
创建前端项目目录结构
初始化React + Vite项目
配置基础依赖和工具
创建基础路由和布局
阶段2：核心组件开发
步骤指示器组件
API配置页面
数据上传预览页面
字段选择页面
阶段3：高级功能开发
提示词配置页面
任务执行监控页面
结果展示页面
阶段4：Electron集成和打包
Electron主进程配置
Python脚本调用集成
打包配置和测试


## 📱 页面结构设计

### 单页应用 - 步骤向导模式

```
主界面
├── 步骤1：API配置
│   ├── API类型选择（通用LLM / 阿里百炼Agent）
│   ├── 基础配置（URL、密钥、模型名称）
│   └── 配置验证
├── 步骤2：数据上传与预览
│   ├── 文件上传（拖拽支持，50MB限制）
│   ├── 数据预览（前10行）
│   └── 字段识别
├── 步骤3：字段选择与范围设置
│   ├── 可视化字段选择
│   ├── 字段范围设置（如2-5）
│   └── 处理范围（起始行/结束行）
├── 步骤4：提示词配置
│   ├── JSON编辑器
│   ├── 模板选择
│   └── 实时预览
├── 步骤5：任务执行与监控
│   ├── 配置摘要
│   ├── 实时进度条
│   ├── 状态显示
│   └── 错误日志展示
└── 结果页面
    ├── 结果文件下载
    ├── 处理统计
    └── 重新开始
```

## 🚀 核心功能实现

### 1. API配置页面
**组件设计：**
- Radio组件选择API类型
- 动态表单根据类型显示不同字段
- 提供常用API提供商预设（OpenAI、DeepSeek、阿里云等）

**配置字段：**
- **通用LLM**：`api_url`、`api_key`、`model`
- **阿里百炼Agent**：`api_url`、`api_key`、`app_id`

**验证规则：**
- 必填字段验证
- URL格式验证
- API密钥格式基础检查

### 2. 数据上传与预览页面
**文件上传：**
- 支持格式：CSV、Excel (.xlsx/.xls)、JSON
- 文件大小限制：50MB以内
- 拖拽上传支持，显示上传进度

**数据预览：**
- 自动解析文件内容
- 表格形式展示前10行数据
- 显示总行数和列数信息
- 编码自动检测提示

**限制提示：**
- 文件大小超限时显示友好提示
- 建议使用数据分割工具处理大文件
- 支持格式说明和示例下载

### 3. 字段选择页面
**可视化选择：**
- 表格展示所有字段，列头可勾选
- 支持全选/反选操作
- 支持字段范围输入（如"2-5"）

**处理范围：**
- 起始行数字输入（默认1）
- 结束行数字输入（默认全部）
- 支持断点续传说明

**数据验证：**
- 至少选择一个字段
- 行数范围合理性检查

### 4. 提示词配置页面
**编辑器：**
- 使用Monaco Editor或简单文本框
- JSON语法高亮和格式验证
- 实时语法错误提示

**模板系统：**
- 提供3-5个常用模板
- 数据提取、内容生成、分类标注等
- 一键应用模板

**JSON结构：**
```json
{
  "system": "系统角色描述",
  "task": "任务描述",
  "output": "输出格式定义（必须）",
  "variables": "可选：变量定义",
  "examples": "可选：示例数据"
}
```

### 5. 任务执行页面
**配置总览：**
- 卡片式展示所有配置摘要
- 支持返回修改任意步骤

**执行监控：**
- 实时进度条（已处理/总条数）
- 状态标签（处理中/成功/失败）
- 处理速度显示（条/分钟）

**日志展示：**
- 滚动式日志窗口
- 错误信息高亮显示
- 简化的错误分类（网络错误、API错误、数据格式错误）

## 🔧 技术实现方案

### 前后端交互模式
**方案：直接调用Python脚本**
1. 前端生成配置文件（config.yaml、prompt.json）到指定目录
2. Electron主进程使用child_process调用Python脚本
3. 监听Python脚本的stdout获取实时进度
4. 通过IPC在渲染进程和主进程间传递状态

### 状态管理设计
```javascript
// 使用Zustand管理全局状态
const useAppStore = create((set) => ({
  // 步骤控制
  currentStep: 1,
  
  // API配置
  apiConfig: {
    api_type: 'llm_compatible',
    api_url: '',
    api_key: '',
    model: ''
  },
  
  // 文件数据
  fileData: {
    fileName: '',
    fileSize: 0,
    totalRows: 0,
    previewData: [],
    headers: []
  },
  
  // 字段选择
  fieldSelection: {
    selectedFields: [],
    startRow: 1,
    endRow: null
  },
  
  // 提示词配置
  promptConfig: {},
  
  // 任务状态
  taskStatus: {
    isRunning: false,
    progress: 0,
    status: 'idle', // idle/running/success/error
    logs: [],
    errorLogs: []
  }
}))
```

### 文件处理实现
```javascript
// CSV处理
const parseCSV = (file) => {
  return new Promise((resolve) => {
    Papa.parse(file, {
      header: true,
      preview: 10, // 只预览前10行
      encoding: 'auto',
      complete: (results) => {
        resolve({
          headers: results.meta.fields,
          data: results.data,
          totalRows: results.data.length
        });
      }
    });
  });
};

// Excel处理
const parseExcel = async (file) => {
  const data = await file.arrayBuffer();
  const workbook = XLSX.read(data);
  const worksheet = workbook.Sheets[workbook.SheetNames[0]];
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
  
  return {
    headers: jsonData[0],
    data: jsonData.slice(1, 11), // 前10行
    totalRows: jsonData.length - 1
  };
};
```

## 🏗 项目结构

```
frontend/
├── src/
│   ├── components/              # 通用组件
│   │   ├── FileUpload/         # 文件上传组件
│   │   ├── ConfigForm/         # 配置表单组件
│   │   ├── DataPreview/        # 数据预览组件
│   │   ├── FieldSelector/      # 字段选择组件
│   │   ├── PromptEditor/       # 提示词编辑器
│   │   ├── ProgressMonitor/    # 进度监控组件
│   │   └── StepIndicator/      # 步骤指示器
│   ├── pages/                  # 页面组件
│   │   ├── ApiConfig/          # API配置页
│   │   ├── DataUpload/         # 数据上传页
│   │   ├── FieldSelection/     # 字段选择页
│   │   ├── PromptConfig/       # 提示词配置页
│   │   ├── TaskExecution/      # 任务执行页
│   │   └── Results/            # 结果页面
│   ├── stores/                 # 状态管理
│   │   └── appStore.js         # 全局状态
│   ├── utils/                  # 工具函数
│   │   ├── fileParser.js       # 文件解析
│   │   ├── configGenerator.js  # 配置生成
│   │   ├── validation.js       # 表单验证
│   │   └── constants.js        # 常量定义
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useFileUpload.js    # 文件上传Hook
│   │   └── useTaskRunner.js    # 任务执行Hook
│   ├── templates/              # 提示词模板
│   │   ├── dataExtraction.json
│   │   ├── contentGeneration.json
│   │   └── classification.json
│   └── styles/                 # 样式文件
├── electron/                   # Electron主进程
│   ├── main.js                 # 主进程入口
│   ├── preload.js             # 预加载脚本
│   └── pythonRunner.js        # Python脚本调用
├── public/                     # 静态资源
├── dist-python/               # Python脚本打包目录
└── package.json
```

## 📦 打包部署方案

### Electron Builder配置
```json
{
  "build": {
    "appId": "com.llm-batch.app",
    "productName": "LLM批处理工具",
    "directories": {
      "output": "dist-electron"
    },
    "files": [
      "dist/**/*",
      "electron/**/*",
      "dist-python/**/*"
    ],
    "extraResources": [
      {
        "from": "dist-python/",
        "to": "python/"
      }
    ],
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```

### Python环境处理
1. 使用PyInstaller将Python脚本打包成exe
2. 将Python运行时和依赖库打包到resources目录
3. 预估最终包大小：~150MB（包含Python环境）

### 安装包特性
- 单exe文件，无需用户安装Python
- 支持离线运行
- 自动创建桌面快捷方式
- 包含卸载程序

## ⚠️ MVP限制与约束

### 功能限制
1. **配置持久化**：暂不支持配置保存，每次启动需重新配置
2. **文件大小**：限制在50MB以内，超出时显示友好提示
3. **错误处理**：仅展示基础错误日志，不做复杂的错误分析
4. **并发控制**：使用默认配置，不支持界面调整

### 技术约束
1. **兼容性**：仅支持Windows 10及以上版本
2. **内存占用**：建议运行内存不低于4GB
3. **网络要求**：需要稳定的互联网连接访问API

## 🔍 后续扩展考虑

### 功能扩展
1. 配置模板保存和导入导出
2. 批量任务队列管理
3. 高级API参数配置（温度、tokens等）
4. 结果可视化图表

### 技术优化
1. 增加后端API服务，支持云端配置同步
2. 支持插件系统，允许第三方扩展
3. 多语言支持
4. 主题切换功能

---

## 📝 开发注意事项

1. **用户体验优先**：界面操作要直观，错误提示要友好
2. **性能考虑**：大文件预览要做分页或虚拟滚动
3. **兼容性测试**：在不同Windows版本上测试安装和运行
4. **文档完善**：提供详细的用户使用说明
5. **错误收集**：考虑添加匿名错误报告机制

此方案专注于MVP阶段的快速实现，在保证核心功能完整的同时，为后续扩展留有充分空间。 