#!/bin/bash
#
# 多 Agent 协作系统 - 启动脚本
#
# 用法:
#   ./start-agents.sh start    - 启动所有 Agent
#   ./start-agents.sh stop     - 停止所有 Agent
#   ./start-agents.sh restart  - 重启所有 Agent
#   ./start-agents.sh status   - 查看状态
#   ./start-agents.sh logs     - 查看日志
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="/tmp/agent-pids"
LOG_DIR="/tmp/agent-logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

AGENTS=(
    "datafetcher:data_fetcher_agent.py"
    "analyst:analyst_agent.py"
    "reporter:reporter_agent.py"
    "reviewer:reviewer_agent.py"
    "orchestrator:orchestrator_daemon.py"
)

start_agent() {
    local name=$1
    local script=$2
    
    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if ps -p $pid > /dev/null 2>&1; then
            echo "[$name] 已在运行 (PID: $pid)"
            return 0
        fi
    fi
    
    echo "[$name] 启动..."
    python3 "$SCRIPT_DIR/$script" > "$LOG_DIR/$name.log" 2>&1 &
    echo $! > "$PID_DIR/$name.pid"
    echo "[$name] 已启动 (PID: $!)"
}

stop_agent() {
    local name=$1
    
    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if ps -p $pid > /dev/null 2>&1; then
            echo "[$name] 停止 (PID: $pid)..."
            kill $pid
            sleep 1
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid
            fi
            rm -f "$PID_DIR/$name.pid"
            echo "[$name] 已停止"
        else
            echo "[$name] 未运行"
            rm -f "$PID_DIR/$name.pid"
        fi
    else
        echo "[$name] 无 PID 文件"
    fi
}

status_agent() {
    local name=$1
    
    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if ps -p $pid > /dev/null 2>&1; then
            echo "[$name] 运行中 (PID: $pid)"
            return 0
        else
            echo "[$name] 未运行 (stale PID file)"
            return 1
        fi
    else
        echo "[$name] 未启动"
        return 1
    fi
}

case "$1" in
    start)
        echo "=== 启动多 Agent 协作系统 ==="
        for agent in "${AGENTS[@]}"; do
            IFS=':' read -r name script <<< "$agent"
            start_agent "$name" "$script"
        done
        echo "=== 启动完成 ==="
        ;;
    
    stop)
        echo "=== 停止多 Agent 协作系统 ==="
        for agent in "${AGENTS[@]}"; do
            IFS=':' read -r name script <<< "$agent"
            stop_agent "$name"
        done
        echo "=== 停止完成 ==="
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "=== 多 Agent 协作系统状态 ==="
        for agent in "${AGENTS[@]}"; do
            IFS=':' read -r name script <<< "$agent"
            status_agent "$name"
        done
        echo "=== 状态完成 ==="
        ;;
    
    logs)
        local agent=$2
        if [ -n "$agent" ]; then
            tail -f "$LOG_DIR/$agent.log"
        else
            echo "用法：$0 logs <agent-name>"
            echo "可用：datafetcher, analyst, reporter, reviewer, orchestrator"
        fi
        ;;
    
    clean)
        echo "清理 PID 文件、日志和队列..."
        rm -f "$PID_DIR"/*.pid
        rm -f "$LOG_DIR"/*.log
        rm -f /tmp/agent-queues/*.jsonl
        rm -f /tmp/agent-queues/*.lock
        rm -f /tmp/agent-stats/*.json
        echo "清理完成"
        ;;
    
    *)
        echo "用法：$0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "命令:"
        echo "  start   - 启动所有 Agent"
        echo "  stop    - 停止所有 Agent"
        echo "  restart - 重启所有 Agent"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志 (需指定 Agent 名)"
        echo "  clean   - 清理 PID、日志和队列文件"
        exit 1
        ;;
esac
