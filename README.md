# 🤖 多智能体开发系统 - 让 AI 帮你写代码

> **想象一下**：你是 CEO，只需要说出需求，三个 AI 员工就开始忙碌起来——架构师设计方案、开发者写代码、QA 测试修 bug，全程自动化，直到交付可运行的软件包！

基于本地 LLM 的多智能体协作系统，在你的 MacBook 上就能运行。

## 🎬 它是如何工作的？

```
你: "帮我做个命令行计算器"
   ↓
🧠 Architect（架构师）: "好的，让我分析需求...设计系统架构..."
   → 输出: requirements.md + architecture.md
   ↓
💻 Developer（开发者）: "收到设计，开始编码...顺便写测试..."
   → 输出: calculator.py + test_calculator.py
   ↓
🔍 QA（测试工程师）: "让我跑一下测试..."
   ├─ ✅ 测试通过 → 打包发布！→ calculator_v1.0.zip
   └─ ❌ 测试失败 → "Developer，这里有 bug，麻烦修一下"
          ↓
      💻 Developer: "好的，让我看看错误分析..."（修复代码）
          ↓
      🔍 QA: "再测一次..."
          ↓
      （循环直到成功，或达到重试上限）
```

### 🎯 核心特性

- **🤝 三智能体协作** - Architect、Developer、QA 各司其职，像真实团队一样工作
- **🔄 自动错误修复** - 测试失败？QA 用 LLM 分析错误原因，Developer 根据分析精准修复
- **🐛 Debug 模式** - 复杂需求搞不定？开启无限迭代模式，不达目的不罢休
- **🏗️ SOLID 架构** - 基于接口设计，想扩展新功能？写个插件就行
- **💾 本地运行** - 数据不出本地，使用 Ollama + qwen2.5:3b，完全免费

## 🚀 60秒快速启动

### 第一步：安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Ollama（如果还没装）
# 访问 https://ollama.ai 下载安装包

# 拉取模型（只需一次，约 2GB）
ollama pull qwen2.5:3b
```

### 第二步：启动 AI 团队

在一个终端窗口运行：

```bash
bash scripts/setup_ollama.sh
```

你会看到：

```
启动 Architect Agent (端口 11434)...
启动 Developer Agent (端口 11435)...
启动 QA Agent (端口 11436)...
预加载模型...
✅ 所有Agent已就绪！
进程ID: Architect=12345, Developer=12346, QA=12347
```

**⚠️ 重要**：保持这个终端运行！这三个进程就是你的 AI 团队。

### 第三步：发布任务

#### 方式 A：Web UI（推荐，直观）

```bash
streamlit run web_ui/app.py
```

浏览器打开 http://localhost:8501，在界面输入需求，点击"开始开发"，坐等收货。

#### 方式 B：命令行（极客风格）

```bash
# 简单需求
python -m src.main --requirement "创建一个命令行计算器，支持加减乘除"

# 复杂需求（无限重试）
python -m src.main --requirement "创建一个定积分计算器，支持数学表达式解析" --debug
```

### 第四步：查看成果

```bash
# 需求文档
cat workspace/requirements/requirement.md

# 架构设计
cat workspace/design/architecture.md

# 生成的代码
ls -la workspace/code/

# 测试文件
ls -la workspace/tests/

# 最终交付物（zip 压缩包）
ls -la workspace/releases/
```