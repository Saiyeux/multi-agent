# Multi-Agent Software Development System

一个基于本地 LLM（Ollama）的多智能体软件开发系统，能够自动完成从需求分析到产品发布的完整开发流程。

## ✨ 特性

### 核心功能
- 🤖 **三智能体协作** - Architect、Developer、QA 协同工作
- 🔄 **自动化流程** - 需求 → 设计 → 编码 → 测试 → 发布
- 🔍 **智能错误分析** - LLM 分析测试失败的根本原因
- 🔁 **自动修复** - 根据分析结果自动修复代码问题
- 🐛 **Debug 模式** - 无限迭代直到问题解决

### 架构优势
- ✅ **SOLID 原则** - 完全符合，零技术债务
- 🔌 **插件化设计** - 添加新功能无需修改核心代码
- 🧪 **高可测试性** - 所有组件可独立测试
- 📦 **配置驱动** - 工作流完全由配置文件控制
- 🎯 **职责单一** - 每个组件只做一件事

## 🚀 快速开始

### 1. 环境要求

- **硬件**: MacBook Air M4, 24GB RAM（推荐）
- **软件**: Python 3.10+, Ollama
- **模型**: qwen2.5:3b

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Ollama 和模型

```bash
# 安装 Ollama (如果还没安装)
# 访问 https://ollama.ai 下载安装

# 拉取模型
ollama pull qwen2.5:3b
```

### 4. 启动 Ollama 实例

```bash
# 启动3个 Ollama 实例用于并行处理
bash scripts/setup_ollama.sh
```

保持这个终端窗口运行。

### 5. 运行系统

#### 方式 A: Web UI（推荐）

```bash
streamlit run web_ui/app.py
```

然后在浏览器打开 http://localhost:8501

#### 方式 B: 命令行

```bash
# 基础使用
python -m src.main --requirement "创建一个命令行计算器，支持加减乘除"

# Debug模式（无限迭代）
python -m src.main --requirement "创建一个定积分计算器" --debug
```

## 📁 项目结构

```
multi-agent/
├── config.yaml              # 系统配置
├── requirements.txt         # Python依赖
│
├── src/
│   ├── core/               # 核心抽象层
│   │   ├── interfaces.py       # 接口定义
│   │   ├── workflow_engine.py  # 工作流引擎
│   │   └── shared_memory.py    # 共享内存
│   │
│   ├── agents/             # Agent实现
│   │   ├── base_agent.py       # 基础Agent
│   │   ├── architect.py        # 架构师
│   │   ├── developer.py        # 开发者
│   │   └── qa_engineer.py      # QA工程师
│   │
│   ├── stages/             # 工作流阶段
│   │   ├── requirement_analysis.py
│   │   ├── architecture_design.py
│   │   ├── coding.py
│   │   ├── testing.py
│   │   └── packaging.py
│   │
│   ├── analyzers/          # 错误分析器
│   │   └── error_analyzer.py
│   │
│   ├── reporters/          # 事件报告器
│   │   └── console_reporter.py
│   │
│   ├── builders/           # 工作流构建器
│   │   └── workflow_builder.py
│   │
│   └── main.py             # CLI入口
│
├── web_ui/
│   └── app.py              # Streamlit界面
│
├── workspace/              # 工作区（自动生成）
│   ├── requirements/           # 需求文档
│   ├── design/                # 设计文档
│   ├── code/                  # 生成的代码
│   ├── tests/                 # 测试文件
│   └── releases/              # 发布包
│
└── scripts/
    └── setup_ollama.sh     # Ollama启动脚本
```

## 🏗️ 系统架构

### 工作流程

```
用户需求
   ↓
[Architect] 需求分析 → requirement.md
   ↓
[Architect] 架构设计 → architecture.md
   ↓
[Developer] 代码实现 → code/*.py
   ↓
[Developer] 编写测试 → tests/test_*.py
   ↓
[QA] 运行测试 → 通过？
   ├─ 是 → 打包发布 → releases/*.zip ✅
   └─ 否 → [QA] 分析错误
           ↓
      [Developer] 修复 → 重试（最多3次或无限）
```

### 核心组件

1. **WorkflowEngine** - 工作流引擎
   - 协调各阶段执行
   - 处理失败重试
   - 支持事件报告

2. **IStage 接口** - 工作流阶段
   - 每个阶段独立实现
   - 可条件执行
   - 可自定义失败处理

3. **IAgent 接口** - 智能体
   - 策略模式分发动作
   - 支持动态指令注入
   - 对话历史管理

4. **ErrorAnalyzer** - 错误分析器
   - 使用 LLM 分析失败原因
   - 提供详细修复建议

## ⚙️ 配置

编辑 `config.yaml` 调整系统参数：

```yaml
# Ollama配置
ollama:
  architect:
    host: "http://localhost:11434"
    model: "qwen2.5:3b"
    temperature: 0.7  # 创造性设计

  developer:
    host: "http://localhost:11435"
    model: "qwen2.5:3b"
    temperature: 0.3  # 确定性代码生成

  qa:
    host: "http://localhost:11436"
    model: "qwen2.5:3b"
    temperature: 0.5  # 平衡的测试

# 工作流配置
workflow:
  max_iterations: 3  # 最大重试次数

# 项目配置
project:
  workspace: "./workspace"

# Debug模式
debug:
  enabled: false  # 启用后无限迭代
```

## 🎯 使用示例

### 简单需求

```bash
python -m src.main -r "创建一个Python函数，实现两个数字相加"
```

### 中等需求

```bash
python -m src.main -r "创建一个命令行待办事项管理器，支持添加、删除、列表功能"
```

### 复杂需求（Debug模式）

```bash
python -m src.main -r "创建一个定积分计算器，支持输入函数表达式和积分上下限" --debug
```

## 📊 输出示例

```
[requirement_analysis] Starting...
[requirement_analysis] ✓ Completed successfully

[architecture_design] Starting...
[architecture_design] ✓ Completed successfully

[coding] Starting...
[coding] ✓ Completed successfully

[testing] Starting...
[testing] ✓ Completed successfully

[packaging] Starting...
[packaging] ✓ Completed successfully

✅ Development completed successfully!
Package: ./workspace/releases/release_20231002_152030.zip
Duration: 45.23s
Iterations: 1
```

## 🔧 扩展开发

### 添加新阶段

```python
# 1. 实现接口
from src.core.interfaces import IStage, StageResult, StageStatus

class CodeReviewStage(IStage):
    @property
    def name(self) -> str:
        return "code_review"

    async def execute(self, context):
        # 实现逻辑
        return StageResult(status=StageStatus.SUCCESS)

# 2. 在 WorkflowBuilder 中添加
stages.append(CodeReviewStage())
```

### 添加新 Agent

```python
# 1. 实现接口
from src.agents import BaseAgent

class SecurityAgent(BaseAgent):
    def _get_action_handler(self, action):
        return {'scan': self._scan_code}.get(action)

# 2. 在配置中注册
agents['security'] = SecurityAgent(config)
```

## 📝 已知限制

- qwen2.5:3b 模型能力有限，复杂项目可能需要人工介入
- 本地运行速度受硬件限制
- 生成的代码需要人工审查后再用于生产环境
- 目前主要支持 Python 项目

## 🛠️ 故障排除

### Ollama 连接失败

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 重启 Ollama 实例
pkill ollama
bash scripts/setup_ollama.sh
```

### 测试一直失败

```bash
# 使用 Debug 模式
python -m src.main -r "你的需求" --debug

# 清理 workspace
rm -rf workspace/code/* workspace/tests/*
```

### 导入错误

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

## 📚 文档

- `CLAUDE.md` - Claude Code 使用指南
- `QUICKSTART.md` - 快速开始指南
- `ARCHITECTURE_REFACTOR.md` - 架构设计文档
- `DEBUG_MODE_DESIGN.md` - Debug 模式设计
- `IMPLEMENTATION_COMPLETE.md` - 实现完成报告
- `START_HERE.md` - 启动指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Ollama](https://ollama.ai) - 本地 LLM 运行时
- [Qwen2.5](https://github.com/QwenLM/Qwen2.5) - 开源 LLM 模型
- [Streamlit](https://streamlit.io) - Web UI 框架