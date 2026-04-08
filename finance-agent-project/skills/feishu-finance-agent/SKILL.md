# 飞书财报 Agent 技能

当用户在飞书中查询股票财报时，调用多 Agent 协作系统生成 One Pager 报告。

## 触发条件

用户在飞书发送：
- `@机器人 AAPL`
- `@机器人 生成苹果财报`
- `@机器人 查询 MSFT`
- `@机器人 特斯拉 One Pager`

## 执行流程

1. **接收飞书消息** - OpenClaw Gateway 接收 `im.message.receive_v1`
2. **调用 Feishu Bridge** - 执行 `python3 agents/feishu-bridge.py <消息内容>`
3. **多 Agent 协作** - Feishu Bridge 调用 Orchestrator，触发 5 个 Agent
4. **返回报告** - 将 One Pager 回复到飞书

## 使用方法

### 方式 1: 直接在 AI Agent 中调用

```python
import subprocess
import json

async def handle_feishu_stock_query(message):
    result = subprocess.run(
        ['python3', 'agents/feishu-bridge.py', message],
        capture_output=True,
        text=True,
        cwd='/home/nio/.openclaw/workspace'
    )
    return json.loads(result.stdout)
```

### 方式 2: 使用 OpenClaw message 工具

```bash
# 发送飞书消息
message send --channel feishu --target <chat_id> --message "AAPL 财报"

# 调用 Feishu Bridge
exec "python3 /home/nio/.openclaw/workspace/agents/feishu-bridge.py AAPL"
```

## 输出格式

### 成功响应

```json
{
  "success": true,
  "query": "AAPL",
  "report": {
    "format": "markdown",
    "content": "## 📊 Apple Inc (AAPL)\n\n### 🏢 业务概览...",
    "qualityCheck": {
      "passed": true,
      "score": 100
    }
  },
  "metrics": {
    "totalSteps": 4,
    "completedSteps": 4,
    "duration": 2500
  }
}
```

### 飞书回复格式

```json
{
  "msg_type": "post",
  "content": {
    "post": {
      "zh_cn": {
        "title": "📊 AAPL 财报 One Pager",
        "content": [
          [{"tag": "text", "text": "✅ 质量评分：100/100\n\n"}],
          [{"tag": "text", "text": "## 📊 Apple Inc (AAPL)\n\n### 🏢 业务概览..."}],
          [{"tag": "text", "text": "\n---\n⏱️ 生成时间：2026-04-08 16:00:00"}]
        ]
      }
    }
  }
}
```

## 错误处理

### 股票代码无法识别

```json
{
  "success": false,
  "error": "无法识别股票代码",
  "message": "请提供股票代码 (如 AAPL, MSFT) 或公司名称 (如 苹果，微软)"
}
```

### Orchestrator 超时

```json
{
  "success": false,
  "error": "Orchestrator 响应超时 (60 秒)"
}
```

## 测试

```bash
# 测试 Feishu Bridge
cd /home/nio/.openclaw/workspace/agents
python3 feishu-bridge.py "@机器人 AAPL"

# 测试 Orchestrator
python3 orchestrator-multi.py AAPL

# 测试完整流程
python3 test-python-flow.py AAPL
```

## 配置

### OpenClaw Gateway 配置

确保 `~/.openclaw/openclaw.json` 中飞书渠道已启用：

```json
{
  "channels": {
    "feishu": {
      "appId": "cli_a93166220039dbd6",
      "appSecret": "z6Haipw4tbkN2ZQ17tsQ0ftxuzQ5MDzJ",
      "enabled": true,
      "connectionMode": "websocket",
      "groupPolicy": "open",
      "groups": {
        "*": {
          "requireMention": true
        }
      }
    }
  }
}
```

### MCP 配置

确保 `config/mcporter.json` 中包含 financial-report：

```json
{
  "mcpServers": {
    "alpha-vantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=RK9S21IP5X28J7IC"
    },
    "financial-report": {
      "command": "python3",
      "args": ["/home/nio/.openclaw/workspace/mcp-servers/financial-report/index.py"]
    }
  }
}
```

## 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 响应时间 | < 30 秒 | ~3 秒 |
| 质量检查通过率 | > 95% | 100% |
| API 配额使用 | < 25 次/日 | 视使用情况 |

## 注意事项

1. **API 配额** - Alpha Vantage 每日 25 次免费请求
2. **超时设置** - Orchestrator 默认 60 秒超时
3. **内存限制** - 独立进程版本占用 ~200MB
4. **飞书消息长度** - 富文本消息最大 10000 字符

---

*技能版本：1.0.0 (Python)*  
*最后更新：2026-04-08*
