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

## 🚧 开发进展记录

### ✅ 阶段1：项目基础搭建（已完成）
**完成时间：** 2025年6月

#### 项目结构创建
- ✅ 在项目根目录创建`frontend/`目录，未破坏原有项目结构
- ✅ 手动搭建React+Vite项目结构（解决npm create vite交互模式问题）
- ✅ 创建完整的项目目录结构：
  ```
  frontend/
  ├── src/
  │   ├── components/    # 通用组件
  │   ├── pages/        # 页面组件
  │   ├── stores/       # Zustand状态管理
  │   ├── utils/        # 工具函数
  │   ├── hooks/        # 自定义Hooks
  │   ├── templates/    # 提示词模板
  │   └── styles/       # 样式文件
  ├── public/           # 静态资源
  ├── server/          # Node.js后端服务
  └── package.json
  ```

#### 核心配置文件
- ✅ **package.json** - 包含所需依赖：React 18、Vite、Ant Design、Zustand、Papa Parse、SheetJS等
- ✅ **main.jsx** - React应用入口
- ✅ **App.jsx** - 主应用组件，5步向导导航
- ✅ **styles/index.css** - 全局样式，响应式设计
- ✅ **stores/appStore.js** - Zustand状态管理，完整状态结构

#### 依赖安装成功
- ✅ 所有NPM依赖包安装完成
- ✅ 开发服务器可正常启动

### ✅ 阶段2：核心组件开发（已完成）
**完成时间：** 2025年6月

#### 1. API配置页面（`pages/ApiConfig.jsx`）
- ✅ **API类型选择**：支持通用LLM和阿里百炼Agent两种类型
- ✅ **预设提供商**：OpenAI、DeepSeek、阿里云、百度等主流AI服务商
- ✅ **动态表单**：根据选择的API类型显示对应配置字段
- ✅ **表单验证**：必填字段检查、URL格式验证、API密钥格式验证
- ✅ **连接测试**：模拟API连接测试功能
- ✅ **配置持久化**：配置数据保存到Zustand store

#### 2. 数据上传页面（`pages/DataUpload.jsx`）
- ✅ **文件上传组件**：拖拽上传、点击上传、进度显示
- ✅ **格式支持**：CSV、Excel (.xlsx/.xls)、JSON
- ✅ **文件大小限制**：50MB上限，超出时友好提示
- ✅ **实时解析预览**：上传后立即解析并预览前10行数据
- ✅ **文件信息展示**：文件名、大小、行数、列数统计
- ✅ **错误处理**：不支持格式、解析失败等错误提示

#### 3. 文件解析工具（`utils/fileParser.js`）
- ✅ **CSV解析**：使用Papa Parse，支持编码自动检测
- ✅ **Excel解析**：使用SheetJS，支持.xlsx和.xls格式
- ✅ **JSON解析**：原生JSON.parse处理
- ✅ **错误处理**：解析失败时返回详细错误信息
- ✅ **性能优化**：大文件只预览前部分数据

#### 4. 字段选择页面（`pages/FieldSelection.jsx`）
- ✅ **可视化字段选择**：表格形式展示所有字段
- ✅ **选择模式**：单选、多选、全选支持
- ✅ **字段预览**：显示每个字段的示例数据
- ✅ **范围设置**：起始行、结束行数字输入
- ✅ **状态管理**：选择状态与store同步
- ✅ **验证逻辑**：至少选择一个字段的验证

#### 5. 提示词配置页面（`pages/PromptConfig.jsx`）
- ✅ **JSON格式配置**：结构化提示词配置（system、task、output、variables、examples）
- ✅ **预设模板系统**：数据提取、内容生成、分类三种模板
- ✅ **实时验证**：JSON语法验证和格式检查
- ✅ **一键应用模板**：点击模板卡片快速应用
- ✅ **配置预览**：模态框预览最终的提示词内容
- ✅ **复制功能**：复制JSON配置到剪贴板

#### 6. 任务执行页面（`pages/TaskExecution.jsx`）
- ✅ 页面文件存在，包含Node.js后端服务器代码
- 🟝 **待详细检查和完善**

#### 7. 结果展示页面（`pages/Results.jsx`）
- ✅ **处理统计**：成功率、失败数、处理速度等关键指标
- ✅ **结果预览**：模态框预览处理结果表格
- ✅ **文件下载**：支持下载完整的处理结果文件
- ✅ **性能分析**：效率评估和优化建议
- ✅ **任务信息**：完整的任务配置摘要
- ✅ **错误日志**：失败记录和错误分析
- ✅ **重新开始**：清除当前配置，重新开始流程

#### 后端集成准备
- ✅ **server/index.js** - Express服务器，处理前端API请求
- ✅ **server/pythonRunner.js** - Python脚本调用封装
- ✅ 前后端接口设计完成

### 🔧 技术实现亮点

#### 状态管理优化
- ✅ 使用Zustand统一管理复杂应用状态
- ✅ 修复各页面与store的兼容性问题
- ✅ 实现页面间数据传递和状态持久化

#### 文件处理性能
- ✅ 大文件分页预览，避免内存溢出
- ✅ 实时上传进度显示
- ✅ 错误边界和异常处理

#### 用户体验设计
- ✅ 响应式设计，适配不同屏幕尺寸
- ✅ 友好的错误提示和加载状态
- ✅ 步骤导航和进度指示
- ✅ 一致的视觉设计和交互模式

### ⚠️ 遇到的技术问题与解决方案

#### 1. PowerShell命令兼容性
**问题：** Windows PowerShell不支持`&&`操作符
```bash
cd frontend && npm run dev  # 失败
```
**解决：** 分步执行命令
```bash
cd frontend
npm run dev
```

#### 2. npm create vite交互模式
**问题：** `npm create vite`需要交互式选择模板
**解决：** 手动创建项目结构和配置文件，确保完整性

#### 3. 状态管理兼容性
**问题：** 各页面组件与Zustand store的状态结构不一致
**解决：** 
- 统一store状态结构设计
- 重构页面组件的状态更新逻辑
- 添加状态验证和错误处理

#### 4. 文件解析性能
**问题：** 大文件解析可能导致界面卡顿
**解决：**
- 只预览前10行数据
- 使用Web Workers进行大文件处理（待实现）
- 添加处理进度提示

### 📊 当前项目状态

#### 功能完成度
- ✅ **API配置** - 100%完成
- ✅ **数据上传** - 100%完成  
- ✅ **字段选择** - 100%完成
- ✅ **提示词配置** - 100%完成
- 🟡 **任务执行** - 基础框架完成，待测试
- ✅ **结果展示** - 100%完成

#### 技术架构
- ✅ **前端框架** - React + Vite完整搭建
- ✅ **UI组件库** - Ant Design集成完成
- ✅ **状态管理** - Zustand配置完成
- ✅ **文件处理** - Papa Parse + SheetJS集成
- 🟡 **后端集成** - Node.js服务器准备就绪
- ⭕ **Electron打包** - 待开始

#### 代码质量
- ✅ **组件化程度** - 高，页面组件独立
- ✅ **错误处理** - 完善的边界处理
- ✅ **用户体验** - 友好的交互和提示
- ✅ **性能优化** - 大文件处理优化
- ✅ **响应式设计** - 适配不同屏幕

### 🎯 下一阶段计划

#### ⏳ 阶段3：Electron集成和测试（即将开始）
1. **Electron主进程配置**
   - 创建electron主进程文件
   - 配置窗口管理和菜单
   - 实现IPC通信机制

2. **Python脚本集成测试**
   - 测试Node.js调用Python脚本
   - 验证前后端数据传递
   - 实现实时进度监控

3. **功能整合测试**
   - 端到端流程测试
   - 错误处理验证
   - 性能优化调整

#### ⏳ 阶段4：打包部署（待开始）
1. **Electron Builder配置**
   - 配置打包参数
   - 添加应用图标和元数据
   - 优化包大小

2. **Python环境打包**
   - PyInstaller打包Python脚本
   - 集成到Electron应用
   - 测试离线运行

3. **安装包生成和测试**
   - 生成Windows安装包
   - 不同系统版本兼容性测试
   - 用户测试和反馈收集

### 📈 项目进度总结

**当前完成度：约75%**
- ✅ 前端界面开发：90%完成
- 🟡 后端集成：60%完成
- ⭕ Electron打包：0%完成
- ⭕ 最终测试：0%完成

**预计完成时间：**
- 阶段3（Electron集成）：1-2周
- 阶段4（打包部署）：1周
- 总计：2-3周完成MVP版本

**技术债务：**
- 需要完善任务执行页面的实时监控
- 需要添加更完善的错误恢复机制
- 需要优化大文件处理性能
- 需要添加用户使用说明文档

### ⚠️ 解决的技术难题

1. **PowerShell兼容性**：解决了Windows命令行语法问题
2. **NPM创建工具**：绕过交互模式，手动搭建完整结构
3. **状态管理兼容性**：修复了各页面与store的集成问题
4. **文件解析性能**：优化了大文件处理机制
5. **⭐ 白屏问题修复**：解决了api.js文件导入错误导致的白屏问题
6. **⭐ API配置默认值**：设置DeepSeek为默认选项，优化用户体验

**阶段4：打包部署**
- Windows安装包生成
- 离线运行测试
- 用户验收测试

---

## 🐛 问题修复记录

### 修复 #1：白屏问题（2025年6月）
**问题描述：** 前端页面打开后显示白屏，无法正常显示界面
**根本原因：** `frontend/src/utils/api.js` 文件为空，导致store中导入apiService失败
**解决方案：**
- 创建完整的API服务类，包含所有必需方法
- 实现WebSocket连接、文件上传、任务执行等功能
- 添加适当的错误处理机制

### 修复 #2：API配置默认值缺失（2025年6月）
**问题描述：** API配置页面默认值没有正确设置，用户需要手动选择所有选项
**根本原因：** Store初始状态和页面组件期望的字段结构不匹配
**解决方案：**
- 修复store中的初始API配置结构
- 设置DeepSeek为默认提供商
- 设置通用LLM为默认API类型
- 更新验证函数以匹配新的字段结构
- 优化页面初始化逻辑

**修复详情：**
```javascript
// 修复前的初始配置
apiConfig: {
  api_type: 'llm_compatible',
  api_url: '',
  api_key: '',
  model: '',
  app_id: ''
}

// 修复后的初始配置
apiConfig: {
  api_type: 'llm', // 默认选择LLM类型
  provider: 'deepseek', // 默认选择DeepSeek
  api_url: 'https://api.deepseek.com/v1/chat/completions',
  api_key: '',
  model: 'deepseek-chat', // 默认选择V3模型
  app_id: ''
}
```

**用户体验优化：**
- ✅ 页面加载后自动选中"通用LLM API"
- ✅ 默认选择DeepSeek提供商
- ✅ 预设DeepSeek API URL
- ✅ 默认选择deepseek-chat（V3）模型
- ✅ 表单验证逻辑正确工作

---

此方案专注于MVP阶段的快速实现，在保证核心功能完整的同时，为后续扩展留有充分空间。

*最后更新：2025年6月4日* 