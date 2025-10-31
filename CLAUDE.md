# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

多智能体软件开发系统，使用本地 LLM (Ollama) 实现需求分析 → 架构设计 → 代码实现 → 测试 → 发布的完整自动化流程。

**运行环境**: MacBook Air M4 24GB RAM, Python 3.10+, Ollama + qwen2.5:3b

**📖 完整文档**: 查看 [README.md](README.md) 了解详细使用说明、架构设计和使用场景

## 核心命令

### 启动系统

```bash
# 1. 启动 3 个 Ollama 实例（必须先执行）
bash scripts/setup_ollama.sh
# 保持此终端运行，进程 ID: Architect(11434), Developer(11435), QA(11436)
# 停止: pkill ollama

# 2A. Web UI（推荐）
streamlit run web_ui/app.py  # http://localhost:8501

# 2B. CLI - 基础使用
python -m src.main --requirement "创建一个命令行计算器"

# 2C. CLI - Debug 模式（无限迭代直到成功）
python -m src.main --requirement "创建一个定积分计算器" --debug
```

### 开发和测试

```bash
# 安装依赖
pip install -r requirements.txt

# 检查 Ollama 状态
curl http://localhost:11434/api/tags
curl http://localhost:11435/api/tags
curl http://localhost:11436/api/tags

# 一键清理工作区（推荐）
bash scripts/clean_workspace.sh

# 或手动清理
rm -rf workspace/code/* workspace/tests/* workspace/releases/*
```

## 架构设计

### 核心设计原则

系统完全基于 **SOLID 原则** 设计，采用 **接口驱动 + 策略模式 + 建造者模式**：

1. **接口层** (`src/core/interfaces.py`): 7 个核心接口
   - `IStage` - 工作流阶段（每个阶段独立实现）
   - `IAgent` - Agent 接口（3 个 Agent 独立配置）
   - `IAnalyzer` - 分析器接口（LLM 错误分析）
   - `IReporter` - 报告器接口（事件驱动输出）
   - `IInterventionHandler` - 人工介入接口（预留扩展）

2. **工作流引擎** (`src/core/workflow_engine.py`):
   - 协调阶段执行，处理失败重试
   - 支持 Debug 模式（无限迭代）
   - 事件驱动报告机制

3. **Agent 层** (`src/agents/`):
   - `BaseAgent` - 策略模式分发 actions，支持动态指令注入
   - `ArchitectAgent` - actions: analyze_requirement, design_architecture
   - `DeveloperAgent` - actions: implement, write_tests, fix_issues
   - `QAAgent` - actions: run_tests, review_code, package_release

4. **阶段层** (`src/stages/`):
   - 5 个独立阶段: requirement_analysis, architecture_design, coding, testing, packaging
   - `TestingStage` 特别设计：自动重试循环，集成 ErrorAnalyzer

5. **构建器** (`src/builders/workflow_builder.py`):
   - 从 `config.yaml` 构建完整工作流
   - 组装所有组件（Agents + Stages + Analyzers + Reporters）

### 工作流程

```
用户需求 (--requirement)
  ↓
[RequirementAnalysisStage] Architect → requirements/requirement.md
  ↓
[ArchitectureDesignStage] Architect → design/architecture.md
  ↓
[CodingStage] Developer → code/*.py + tests/test_*.py
  ↓
[TestingStage] QA run_tests → 通过？
  ├─ 是 → [PackagingStage] → releases/*.zip ✅
  └─ 否 → [ErrorAnalyzer] LLM 分析错误 → Developer fix_issues → 重试
           └─ 最多 max_iterations 次（Debug 模式无限）
```

### 关键实现细节

**BaseAgent 的 action 分发机制** (src/agents/base_agent.py:39-61):
```python
async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get('action')  # 必须字段
    handler = self._get_action_handler(action)  # 子类实现
    return await handler(input_data)
```

**TestingStage 的重试循环** (src/stages/testing.py:44-91):
- QA Agent 运行测试 → 失败 → ErrorAnalyzer 分析 → Developer fix_issues → 循环
- 迭代次数保存在 `context.iteration`
- Debug 模式: `max_iterations = float('inf')`

**动态指令注入** (src/agents/base_agent.py:75-84):
- `inject_instruction()` 保存指令到 `self.dynamic_instructions`
- `chat()` 自动将最近 3 条指令添加到 prompt
- 用于实现人工介入功能（预留）

**ErrorAnalyzer 使用 LLM 分析** (src/analyzers/error_analyzer.py:20-75):
- 输入: pytest 输出 + 错误信息
- 输出: JSON 格式 {error_type, location, root_cause, fix_suggestions}
- DeveloperAgent 根据分析结果修复代码

## 配置说明

`config.yaml` 核心配置:

```yaml
ollama:
  architect:
    host: "http://localhost:11434"
    model: "qwen2.5:3b"
    temperature: 0.7  # 创造性设计
  developer:
    temperature: 0.3  # 确定性代码生成
  qa:
    temperature: 0.5  # 平衡

workflow:
  max_iterations: 3  # Debug 模式下无限

project:
  workspace: "./workspace"  # 所有生成文件存储位置
```

## 扩展开发

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

# 2. 在 WorkflowBuilder 中注册
stages.insert(3, CodeReviewStage())  # 插入到 coding 之后
```

### 添加新 Agent Action

```python
# 在子类中扩展 _get_action_handler()
class DeveloperAgent(BaseAgent):
    def _get_action_handler(self, action):
        return {
            'implement': self._implement,
            'write_tests': self._write_tests,
            'fix_issues': self._fix_issues,
            'refactor': self._refactor  # 新增
        }.get(action)
```

## 项目结构

```
multi-agent/
├── config.yaml              # 系统配置
├── requirements.txt         # Python 依赖
├── README.md               # 完整文档（用户向）
├── CLAUDE.md               # 本文件（开发向）
│
├── src/
│   ├── core/               # 核心抽象层
│   │   ├── interfaces.py       # 7 个核心接口
│   │   ├── workflow_engine.py  # 工作流引擎
│   │   └── shared_memory.py    # 共享内存
│   │
│   ├── agents/             # 3 个 Agent 实现
│   │   ├── base_agent.py
│   │   ├── architect.py
│   │   ├── developer.py
│   │   └── qa_engineer.py
│   │
│   ├── stages/             # 5 个工作流阶段
│   ├── analyzers/          # 错误分析器
│   ├── reporters/          # 控制台报告器
│   ├── builders/           # 工作流构建器
│   └── main.py             # CLI 入口
│
├── web_ui/
│   └── app.py              # Streamlit Web UI
│
├── workspace/              # 工作区（生成文件）
│   ├── requirements/
│   ├── design/
│   ├── code/
│   ├── tests/
│   └── releases/
│
└── scripts/
    └── setup_ollama.sh     # Ollama 启动脚本
```

## 重要限制

- qwen2.5:3b 模型能力有限，复杂需求可能需要人工介入
- 生成代码需人工审查后再用于生产环境
- 目前主要支持 Python 项目（代码解析、测试运行基于 Python）
- 3 个 Ollama 实例同时运行对硬件有要求

## 故障排查

**Ollama 连接失败**: 检查 `bash scripts/setup_ollama.sh` 是否运行且未退出

**测试一直失败**: 使用 `--debug` 模式查看详细迭代过程，或检查 workspace/tests/ 中生成的测试文件

**导入错误**: 确认在项目根目录运行命令，使用 `python -m src.main` 而非 `python src/main.py`

## 文档索引

- **README.md** - 完整的用户文档，包含生动的使用说明、架构设计、使用场景、常见问题
- **config.yaml** - 系统配置文件，包含 Agent 参数和工作流设置
- **CLAUDE.md** - 本文件，面向 Claude Code 的技术文档
