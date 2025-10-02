# 文件清理计划

## 分析结果

### ✅ 保留的文件（核心/文档）

**配置和依赖**
- `config.yaml` - 系统配置（需要）
- `requirements.txt` - Python依赖（需要）
- `.gitignore` - Git配置（需要）

**文档**
- `CLAUDE.md` - Claude Code指南（需要）
- `README.md` - 用户文档（需要）
- `QUICKSTART.md` - 快速开始（需要）
- `ARCHITECTURE_REFACTOR.md` - 新架构设计（需要，参考文档）
- `DEBUG_MODE_DESIGN.md` - Debug模式设计（需要，参考文档）

**脚本**
- `scripts/setup_ollama.sh` - Ollama启动脚本（需要）

### 🗑️ 需要删除的文件（旧实现/临时文件）

**旧的源代码实现（将被重构替代）**
- `src/agents/architect.py` - 旧实现，重构后替换
- `src/agents/developer.py` - 旧实现，重构后替换
- `src/agents/qa_engineer.py` - 旧实现，重构后替换
- `src/agents/base_agent.py` - 旧实现，重构后替换
- `src/orchestrator.py` - 旧实现，将被WorkflowEngine替换
- `src/main.py` - 旧CLI入口，重构后替换
- `web_ui/app.py` - 旧Web UI，重构后替换
- `examples/simple_example.py` - 基于旧架构的示例

**保留但重构的文件**
- `src/core/shared_memory.py` - 保留（基础组件，可复用）
- `src/llm/prompts.py` - 保留（提示词模板，可复用）
- `src/__init__.py`, `src/agents/__init__.py`, `src/core/__init__.py`, `src/llm/__init__.py` - 保留（包初始化）
- `src/tools/__init__.py` - 保留（为将来扩展）

**临时/生成的文件**
- `workspace/` - 保留目录结构，但清空内容（运行时生成）
  - 删除 `workspace/.pytest_cache/` - pytest缓存
  - 删除 `workspace/code/` - 测试生成的代码
  - 删除 `workspace/tests/` - 测试生成的测试文件
  - 删除 `workspace/design/` - 测试生成的设计文档
  - 删除 `workspace/requirements/` - 测试生成的需求文档
  - 保留空目录结构和 `.gitkeep`

**空目录**
- `tests/` - 项目测试目录（空，但需要保留）
- `web_ui/components/` - Web组件目录（需要创建）

### 📋 清理操作

#### 1. 删除旧的源代码实现（暂时备份）
```bash
# 创建备份目录
mkdir -p _old_implementation

# 移动旧实现（不是删除，以防需要参考）
mv src/agents/architect.py _old_implementation/
mv src/agents/developer.py _old_implementation/
mv src/agents/qa_engineer.py _old_implementation/
mv src/agents/base_agent.py _old_implementation/
mv src/orchestrator.py _old_implementation/
mv src/main.py _old_implementation/
mv web_ui/app.py _old_implementation/
mv examples/simple_example.py _old_implementation/
```

#### 2. 清理 workspace（保留结构）
```bash
# 删除生成的内容
rm -rf workspace/.pytest_cache
rm -rf workspace/code/*
rm -rf workspace/tests/*
rm -rf workspace/design/*
rm -rf workspace/requirements/*
rm -rf workspace/releases/*
rm -rf workspace/reports/*

# 确保目录存在
mkdir -p workspace/{code,tests,design,requirements,releases,reports}
```

#### 3. 清理系统文件
```bash
# 删除 macOS 系统文件
find . -name ".DS_Store" -delete

# 删除 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

### 📁 清理后的目录结构

```
multi-agent/
├── .gitignore
├── config.yaml
├── requirements.txt
│
├── CLAUDE.md               # 保留
├── README.md               # 保留
├── QUICKSTART.md           # 保留（需要更新）
├── ARCHITECTURE_REFACTOR.md # 保留（参考）
├── DEBUG_MODE_DESIGN.md     # 保留（参考）
│
├── scripts/
│   └── setup_ollama.sh
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/              # 核心抽象层（NEW）
│   │   ├── __init__.py
│   │   ├── interfaces.py    # NEW - 接口定义
│   │   ├── workflow_engine.py # NEW - 工作流引擎
│   │   └── shared_memory.py  # 保留 - 共享内存
│   │
│   ├── agents/            # Agent实现（REFACTOR）
│   │   ├── __init__.py
│   │   ├── base_agent.py    # 重构 - 实现IAgent
│   │   ├── architect.py     # 重构
│   │   ├── developer.py     # 重构
│   │   └── qa_engineer.py   # 重构
│   │
│   ├── stages/            # 工作流阶段（NEW）
│   │   ├── __init__.py
│   │   ├── requirement_analysis.py
│   │   ├── architecture_design.py
│   │   ├── coding.py
│   │   ├── testing.py
│   │   └── packaging.py
│   │
│   ├── analyzers/         # 分析器（NEW）
│   │   ├── __init__.py
│   │   └── error_analyzer.py
│   │
│   ├── reporters/         # 报告器（NEW）
│   │   ├── __init__.py
│   │   ├── console_reporter.py
│   │   └── web_reporter.py
│   │
│   ├── intervention/      # 介入处理（NEW）
│   │   ├── __init__.py
│   │   └── manual_intervention.py
│   │
│   ├── builders/          # 构建器（NEW）
│   │   ├── __init__.py
│   │   └── workflow_builder.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── prompts.py      # 保留 - 提示词模板
│   │
│   ├── tools/
│   │   └── __init__.py
│   │
│   └── main.py            # 重构 - 新的CLI入口
│
├── web_ui/                # Web界面（REFACTOR）
│   ├── app.py             # 重构 - 基于新架构
│   └── components/
│       ├── agent_console.py
│       ├── code_viewer.py
│       └── iteration_timeline.py
│
├── examples/              # 示例（UPDATE）
│   └── basic_usage.py     # 新示例
│
├── tests/                 # 单元测试（NEW）
│   ├── __init__.py
│   ├── test_workflow_engine.py
│   ├── test_stages.py
│   └── test_agents.py
│
├── workspace/             # 工作区（清空）
│   ├── .gitkeep
│   ├── code/
│   ├── tests/
│   ├── design/
│   ├── requirements/
│   ├── releases/
│   └── reports/
│
└── _old_implementation/   # 旧代码备份（临时）
    ├── architect.py
    ├── developer.py
    ├── qa_engineer.py
    ├── base_agent.py
    ├── orchestrator.py
    ├── main.py
    ├── app.py
    └── simple_example.py
```

## 执行清理

现在执行清理操作。