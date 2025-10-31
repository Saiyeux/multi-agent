#!/bin/bash
# 诊断多智能体系统问题

echo "🔍 Multi-Agent System Diagnostics"
echo "=================================="
echo ""

# 检查 Ollama 连接
echo "1. 检查 Ollama 服务状态..."
echo ""

for port in 11434 11435 11436; do
    echo -n "   端口 $port: "
    if curl -s --connect-timeout 2 "http://localhost:$port/api/tags" > /dev/null 2>&1; then
        echo "✅ 连接成功"
    else
        echo "❌ 连接失败"
    fi
done

echo ""

# 检查模型
echo "2. 检查 qwen2.5:3b 模型..."
echo ""
if ollama list 2>/dev/null | grep -q "qwen2.5:3b"; then
    echo "   ✅ 模型已安装"
else
    echo "   ❌ 模型未安装"
    echo "   建议运行: ollama pull qwen2.5:3b"
fi

echo ""

# 检查工作区
echo "3. 检查 workspace 目录结构..."
echo ""

cd "$(dirname "$0")/.."

for dir in requirements design code tests reports releases; do
    workspace_dir="workspace/$dir"
    file_count=$(find "$workspace_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo -n "   $dir/: "
    if [ "$file_count" -gt 0 ]; then
        echo "✅ $file_count 个文件"
    else
        echo "⚠️  空目录"
    fi
done

echo ""

# 检查最近的迭代日志
echo "4. 检查迭代日志..."
echo ""

if [ -f "workspace/reports/iteration_log.jsonl" ]; then
    line_count=$(wc -l < workspace/reports/iteration_log.jsonl)
    echo "   ✅ 找到日志文件 ($line_count 次迭代)"
    echo ""
    echo "   最后一次迭代:"
    python3 scripts/view_iteration_log.py --latest 2>/dev/null || \
        tail -1 workspace/reports/iteration_log.jsonl
else
    echo "   ⚠️  没有找到迭代日志"
fi

echo ""
echo "=================================="
echo ""

# 建议
echo "💡 建议："
echo ""

# 检查 Ollama 状态并给建议
ollama_issues=0
for port in 11434 11435 11436; do
    if ! curl -s --connect-timeout 2 "http://localhost:$port/api/tags" > /dev/null 2>&1; then
        ((ollama_issues++))
    fi
done

if [ $ollama_issues -gt 0 ]; then
    echo "1. Ollama 服务未完全启动，请运行："
    echo "   bash scripts/setup_ollama.sh"
    echo ""
fi

# 检查 workspace 是否为空
if [ ! -f "workspace/requirements/requirement.md" ]; then
    echo "2. workspace 为空，说明workflow从头就失败了"
    echo "   可能原因："
    echo "   - Ollama 连接失败"
    echo "   - LLM 响应超时"
    echo "   - 模型未正确加载"
    echo ""
    echo "   建议执行完整测试："
    echo "   python -m src.main -r \"创建一个简单的加法函数\" --debug"
    echo ""
fi

echo "3. 如需帮助，请提供以下信息："
echo "   - 运行的完整命令"
echo "   - 完整的控制台输出（包括错误信息）"
echo "   - 此诊断脚本的输出"
echo ""
