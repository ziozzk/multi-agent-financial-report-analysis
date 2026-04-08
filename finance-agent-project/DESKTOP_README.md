# 多 Agent 美股财报分析系统 - 桌面版

> 完整的生产就绪版本（不含测试脚本）

---

## 📁 文件结构

```
finance-agent-project/
├── agents/
│   ├── orchestrator-multi.py    # 协调者 Agent
│   ├── data-fetcher.py          # 数据获取 Agent
│   ├── analyst.py               # 数据分析 Agent
│   ├── reporter.py              # 报告生成 Agent
│   ├── reviewer.py              # 质量审核 Agent
│   ├── feishu-bridge.py         # 飞书桥接器
│   ├── start.sh                 # 启动脚本
│   └── PYTHON_README.md         # 使用指南
│
├── mcp-servers/financial-report/
│   └── index.py                 # MCP Server
│
├── skills/feishu-finance-agent/
│   ├── SKILL.md                 # Skill 文档
│   ├── feishu-skill.py          # 飞书 Skill 执行器
│   └── AGENT_INSTRUCTIONS.md    # AI Agent 指令
│
├── config/
│   └── mcporter.json            # MCP 配置
│
├── requirements.txt             # Python 依赖
├── README.md                    # 主项目说明
├── SOUL.md                      # AI 人格定义
└── PYTHON_PROJECT_SUMMARY.md    # 项目总结
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 MCP

编辑 `config/mcporter.json`，确保 API Key 正确：

```json
{
  "mcpServers": {
    "alpha-vantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    },
    "financial-report": {
      "command": "python3",
      "args": ["./mcp-servers/financial-report/index.py"]
    }
  }
}
```

### 3. 测试运行

```bash
# 测试完整流程
cd agents
python3 test-python-flow.py AAPL

# 或使用启动脚本
./start.sh MSFT
```

---

## 📊 核心功能

- 🤖 **5 个独立进程 Agent** - 协调者、数据获取、分析、报告、审核
- 📈 **Alpha Vantage API** - 实时美股数据
- ✅ **7 项质量检查** - 自动化质量保障
- 📱 **飞书集成** - 富文本回复
- 🐍 **Python 实现** - 完整 Python 技术栈

---

## 📝 使用说明

### 在 OpenClaw 中使用

当 AI Agent 在飞书中收到股票查询时：

1. AI 读取 `SOUL.md` 中的指令
2. 调用 `exec` 工具执行 `feishu-skill.py`
3. 解析返回的 JSON
4. 使用 `message` 工具回复到飞书

### 直接调用

```bash
# 调用 Skill
python3 skills/feishu-finance-agent/feishu-skill.py "@机器人 AAPL"

# 调用多 Agent 系统
python3 agents/orchestrator-multi.py AAPL

# 调用 MCP Server
mcporter call financial-report.generate_onepager symbol=TSLA
```

---

## ⚠️ 注意事项

1. **API 配额** - Alpha Vantage 每日 25 次免费请求
2. **Python 版本** - 需要 Python 3.8+
3. **工作目录** - 需要在项目根目录运行
4. **飞书配置** - 需要配置 OpenClaw 飞书渠道

---

## 📚 详细文档

- [agents/PYTHON_README.md](./agents/PYTHON_README.md) - 详细使用指南
- [skills/feishu-finance-agent/AGENT_INSTRUCTIONS.md](./skills/feishu-finance-agent/AGENT_INSTRUCTIONS.md) - AI Agent 指令
- [PYTHON_PROJECT_SUMMARY.md](./PYTHON_PROJECT_SUMMARY.md) - 项目总结

---

*复制时间：2026-04-08*
*原始位置：/home/nio/.openclaw/workspace*
