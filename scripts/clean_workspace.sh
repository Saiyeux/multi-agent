#!/bin/bash
# 一键清理 workspace 生成的内容
# 保留目录结构，删除所有生成的文件

set -e  # 遇到错误立即退出

WORKSPACE_DIR="./workspace"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "🧹 开始清理 workspace..."
echo ""

# 清理函数
clean_directory() {
    local dir=$1
    local display_name=$2

    if [ -d "$dir" ]; then
        local file_count=$(find "$dir" -type f | wc -l)
        if [ "$file_count" -gt 0 ]; then
            echo "  📁 清理 $display_name..."
            rm -rf "$dir"/*
            echo "     ✓ 已删除 $file_count 个文件"
        else
            echo "  📁 $display_name 已经是空的"
        fi
    else
        echo "  📁 创建 $display_name 目录..."
        mkdir -p "$dir"
    fi
}

# 清理各个子目录
clean_directory "$WORKSPACE_DIR/requirements" "需求文档 (requirements)"
clean_directory "$WORKSPACE_DIR/design" "架构设计 (design)"
clean_directory "$WORKSPACE_DIR/code" "生成代码 (code)"
clean_directory "$WORKSPACE_DIR/tests" "测试文件 (tests)"
clean_directory "$WORKSPACE_DIR/releases" "发布包 (releases)"
clean_directory "$WORKSPACE_DIR/reports" "报告 (reports)"

echo ""
echo "✅ Workspace 清理完成！"
echo ""
echo "📊 当前状态："
du -sh "$WORKSPACE_DIR"/* 2>/dev/null || echo "  所有目录都是空的"
echo ""
echo "💡 提示：现在可以运行新的开发任务了"
echo "   python -m src.main --requirement \"你的需求\""
