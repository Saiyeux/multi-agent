# 🚀 开始使用 - 新架构

## ✅ 实现完成！

新架构已完整实现，准备验证功能。

## 📋 启动步骤

### 1. 确保 Ollama 运行

```bash
# 启动3个Ollama实例
bash scripts/setup_ollama.sh
```

保持这个终端窗口运行。

### 2. 选择运行方式

#### 方式A: Web UI（推荐，方便查看）

```bash
streamlit run web_ui/app.py
```

然后浏览器打开 http://localhost:8501

#### 方式B: CLI

```bash
# 基础使用
python -m src.main --requirement "创建一个简单的计算器，支持加减乘除"

# Debug模式（无限迭代，适合调试）
python -m src.main --requirement "创建一个定积分计算器" --debug
```

#### 方式C: 快速测试

```bash
# 运行简单测试验证系统
python test_quick.py
```

## 🎯 测试建议

### 简单需求（验证基础功能）
```
创建一个Python函数，实现两个数字相加
```

### 中等需求（验证完整流程）
```
创建一个命令行计算器，支持加减乘除四则运算
```

### 复杂需求（验证错误修复）
```
创建一个定积分计算器，支持输入函数和积分上下限
```

## 📊 新架构特点

1. **自动错误分析**
   - QA Agent 会分析测试失败的根本原因
   - Developer Agent 根据分析结果精准修复

2. **无限迭代（Debug模式）**
   - 不再限制3次重试
   - 直到问题解决或手动停止

3. **清晰的输出**
   - 每个阶段状态清晰
   - 成功/失败标记明显（✓ ✗）

4. **健壮的架构**
   - 基于接口设计
   - 符合SOLID原则
   - 易于扩展

## 🔍 监控输出

运行时你会看到：

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
Package: ./workspace/releases/release_xxx.zip
Duration: 45.23s
Iterations: 1
```

## 📁 查看生成的文件

```bash
# 需求文档
cat workspace/requirements/requirement.md

# 架构设计
cat workspace/design/architecture.md

# 生成的代码
ls -la workspace/code/

# 测试文件
ls -la workspace/tests/

# 发布包
ls -la workspace/releases/
```

## 🐛 如果遇到问题

1. **确认 Ollama 运行**: `curl http://localhost:11434/api/tags`
2. **查看详细错误**: 使用 `--debug` 模式
3. **检查配置**: 确认 `config.yaml` 正确
4. **清理workspace**: `rm -rf workspace/code/* workspace/tests/*`

## 🎉 祝您使用愉快！

新架构已经准备好，可以开始验证了！