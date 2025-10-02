# 快速开始指南

## 前置要求

1. Python 3.10 或更高版本
2. Ollama 已安装（访问 https://ollama.ai 下载）
3. 至少 16GB RAM（推荐 24GB）

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 下载 Ollama 模型

```bash
ollama pull qwen2.5:3b
```

### 3. 启动 Ollama 服务

在一个新的终端窗口运行：

```bash
bash scripts/setup_ollama.sh
```

你应该看到：
```
启动 Architect Agent (端口 11434)...
启动 Developer Agent (端口 11435)...
启动 QA Agent (端口 11436)...
预加载模型...
✅ 所有Agent已就绪！
```

**重要**: 保持这个终端窗口运行！

## 使用方式

### 方式 1: 命令行

在另一个终端窗口：

```bash
python -m src.main --requirement "创建一个命令行计算器，支持加减乘除"
```

### 方式 2: 运行示例

```bash
python examples/simple_example.py
```

### 方式 3: Web 界面

```bash
streamlit run web_ui/app.py
```

然后在浏览器打开 http://localhost:8501

## 预期结果

系统会经历以下阶段：

1. **Analyzing** - 架构师分析需求
2. **Designing** - 架构师设计系统架构
3. **Coding** - 开发者实现代码
4. **Testing** - QA 运行测试
5. **Packaging** - 打包发布（如果测试通过）

最终输出：

- 📁 `workspace/requirements/` - 需求文档
- 📁 `workspace/design/` - 架构设计
- 📁 `workspace/code/` - 生成的代码
- 📁 `workspace/tests/` - 测试文件
- 📦 `workspace/releases/` - 发布包

## 故障排除

### 问题：`ollama` 命令找不到

**解决**：安装 Ollama from https://ollama.ai

### 问题：端口已被占用

**解决**：
```bash
# 停止所有 ollama 进程
pkill ollama

# 重新启动
bash scripts/setup_ollama.sh
```

### 问题：模型加载很慢

**解决**：首次运行时，模型需要加载到内存中。第二次运行会更快。

### 问题：Python 模块找不到

**解决**：
```bash
# 确保在项目根目录
cd /path/to/multi-agent

# 重新安装依赖
pip install -r requirements.txt
```

## 下一步

- 查看 `README.md` 了解详细文档
- 查看 `CLAUDE.md` 了解系统架构
- 修改 `config.yaml` 调整参数
- 尝试更复杂的需求

## 停止服务

完成后，停止 Ollama 实例：

```bash
pkill ollama
```