# 多 Agent 美股财报分析系统 📊

真正的多 Agent 协作系统，每个 Agent 具备自主性、持续性、社交能力和学习能力。

---

## 🚀 快速开始

### 1. 启动 Agent 集群

```bash
cd agents
./start-agents.sh start
```

### 2. 查看状态

```bash
./start-agents.sh status
```

### 3. 测试查询

```bash
python3 ../skills/feishu-finance-agent/feishu-skill.py "@机器人 AAPL"
```

### 4. 查看日志

```bash
./start-agents.sh logs datafetcher
```

### 5. 停止 Agent

```bash
./start-agents.sh stop
```

---

## 🏗️ 系统架构

```
用户 (飞书)
    ↓
feishu-skill.py
    ↓
消息队列 (基于文件)
    ↓
┌─────────────────────────────────────┐
│  5 个常驻 Agent                       │
│  • DataFetcher  → 获取财务数据       │
│  • Analyst      → 分析数据           │
│  • Reporter     → 生成报告           │
│  • Reviewer     → 质量审核           │
│  • Orchestrator → 协调调度           │
└─────────────────────────────────────┘
    ↓
MCP Server → Alpha Vantage API
    ↓
One Pager 报告 (纯文本)
```

---

## 🤖 5 个 Agent

| Agent | 职责 | 自主性体现 |
|-------|------|-----------|
| **DataFetcher** | 获取财务数据 | 自主选择 API（基于成功率） |
| **Analyst** | 分析数据 | 判断数据是否足够，可请求补充 |
| **Reporter** | 生成报告 | 根据反馈返工 |
| **Reviewer** | 质量审核 | 动态调整质量阈值 |
| **Orchestrator** | 协调调度 | 进程管理、健康检查 |

---

## 💬 Agent 间协商

**场景 1: Analyst 请求更多数据**
```
Analyst → NEGOTIATION_QUEUE → DataFetcher
"数据不足，需要历史数据"
```

**场景 2: Reviewer 要求返工**
```
Reviewer → NEGOTIATION_QUEUE → Reporter
"缺少风险提示，评分 60/100"
```

---

## 📊 质量检查

| 检查项 | 关键 |
|--------|------|
| 内容非空 | ✅ |
| 包含业务概览 | ✅ |
| 包含财务摘要 | ✅ |
| 包含投资亮点 | ⚠️ |
| 包含风险提示 | ✅ |
| 包含股价信息 | ⚠️ |
| 内容长度合理 | ⚠️ |

---

## 📁 项目结构

```
finance-multi-agent/
├── agents/                          # 多 Agent 核心
│   ├── message_queue.py             # 消息队列
│   ├── base_agent.py                # Agent 基类
│   ├── data_fetcher_agent.py        # DataFetcher
│   ├── analyst_agent.py             # Analyst
│   ├── reporter_agent.py            # Reporter
│   ├── reviewer_agent.py            # Reviewer
│   ├── orchestrator_daemon.py       # Orchestrator
│   └── start-agents.sh              # 启动脚本
│
├── skills/feishu-finance-agent/     # 飞书集成
│   └── feishu-skill.py              # Skill 执行器
│
├── config/
│   └── mcporter.json                # MCP 配置
│
└── README.md                        # 本文档
```

---

## 🔧 配置

### MCP 配置

编辑 `config/mcporter.json`:

```json
{
  "mcpServers": {
    "alpha-vantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

### API Key

Alpha Vantage API Key: `RK9S21IP5X28J7IC` (25 次/日免费)

---

## 📈 性能指标

| 指标 | 目标 |
|------|------|
| 响应时间 | < 3 秒 |
| 质量评分 | > 90 分 |
| 服务可用性 | 100% |

---

## 🛠️ 技术栈

- **语言**: Python 3.8+
- **通信**: 基于文件的简易消息队列
- **数据源**: Alpha Vantage API (via MCP)
- **渠道**: 飞书开放平台

---

*最后更新：2026-04-10*
