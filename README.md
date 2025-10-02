# Multi-Agent Software Development System

一个基于本地 LLM（Ollama）的多智能体软件开发系统，能够自动完成从需求分析到产品发布的完整开发流程。

## 系统架构

系统由三个专门的智能体协作完成开发任务：

1. **Architect Agent（架构师）** - 需求分析、系统设计
2. **Developer Agent（开发者）** - 代码实现、单元测试
3. **QA Agent（测试工程师）** - 测试执行、代码审查、产品打包

工作流程：用户需求 → 架构师 → 开发者 → QA工程师 → 产品交付

## 运行环境

- **硬件**: MacBook Air M4, 24GB RAM
- **软件**: Python 3.10+, Ollama
- **模型**: qwen2.5:3b

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Ollama 和模型

```bash
# 安装 Ollama (如果还没安装)
# 访问 https://ollama.ai 下载安装

# 拉取模型
ollama pull qwen2.5:3b
```

### 3. 启动 Ollama 实例

```bash
# 启动3个 Ollama 实例用于并行处理
bash scripts/setup_ollama.sh
```

### 4. 运行开发流程

#### 命令行方式

```bash
python -m src.main --requirement "创建一个命令行计算器，支持加减乘除"
```

#### Web UI 方式

```bash
streamlit run web_ui/app.py
```

然后在浏览器中打开 http://localhost:8501

## 使用示例

### Python API

```python
import asyncio
from src.orchestrator import DevOrchestrator

async def main():
    # 加载配置
    config = DevOrchestrator.load_config('config.yaml')

    # 创建协调器
    orchestrator = DevOrchestrator(config)

    # 运行开发流程
    result = await orchestrator.run(
        "创建一个待办事项管理应用，支持添加、删除、标记完成功能"
    )

    if result['status'] == 'success':
        print(f"✅ 开发完成！产品位置: {result['package']}")
    else:
        print(f"❌ 开发失败: {result['reason']}")

if __name__ == '__main__':
    asyncio.run(main())
```

## 配置说明

编辑 `config.yaml` 来调整系统配置：

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
  max_iterations: 3      # 最大重试次数
  timeout_seconds: 300   # 单个Agent超时时间
  auto_fix: true        # 自动修复bug
```

## 项目结构

```
multi-agent/
├── config.yaml           # 配置文件
├── requirements.txt      # 依赖列表
├── scripts/
│   └── setup_ollama.sh  # Ollama启动脚本
├── src/
│   ├── agents/          # 三个Agent实现
│   ├── core/            # 核心组件（SharedMemory）
│   ├── llm/             # Prompt模板
│   ├── orchestrator.py  # 主协调器
│   └── main.py          # CLI入口
├── web_ui/
│   └── app.py           # Streamlit界面
└── workspace/           # 工作区（自动生成）
    ├── requirements/    # 需求文档
    ├── design/          # 设计文档
    ├── code/            # 生成的代码
    ├── tests/           # 测试文件
    └── releases/        # 发布包
```

## 工作流程详解

1. **需求分析** - Architect Agent 分析用户需求，生成需求文档
2. **架构设计** - Architect Agent 设计系统架构，规划模块
3. **代码实现** - Developer Agent 根据设计实现代码
4. **编写测试** - Developer Agent 为代码编写单元测试
5. **测试执行** - QA Agent 运行测试，验证功能
6. **问题修复** - 如果测试失败，Developer Agent 修复问题（最多3次）
7. **产品打包** - QA Agent 打包代码为发布包

## 已知限制

- qwen2.5:3b 模型能力有限，复杂项目可能需要人工介入
- 本地运行速度受硬件限制
- 生成的代码需要人工审查后再用于生产环境
- 目前主要支持 Python 项目

## 未来扩展

- [ ] 支持更多编程语言
- [ ] 集成 Git 版本控制
- [ ] 添加代码质量检查（pylint, black）
- [ ] 支持增量开发和迭代
- [ ] 接入云端 LLM（可选）
- [ ] 团队协作模式

## License

MIT License