#!/bin/bash
# 多 Agent 协作系统 - 启动脚本 (Python 版本)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 多 Agent 协作系统 - Python 独立进程版本"
echo "===================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：需要 Python 3"
    exit 1
fi

# 检查 mcporter
if ! command -v mcporter &> /dev/null; then
    echo "❌ 错误：需要 mcporter"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 启动 Orchestrator（会自动启动所有子 Agent）
echo "📋 用法:"
echo "  ./start.sh AAPL"
echo "  ./start.sh 生成苹果财报"
echo "  ./start.sh MSFT"
echo ""
echo "正在启动..."
echo ""

python3 agents/orchestrator-multi.py "$@"
