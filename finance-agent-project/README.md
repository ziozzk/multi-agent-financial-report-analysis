# 多 Agent 美股财报分析系统 📊

基于 Python 多 Agent 协作 与 MCP 的美股财报 One Pager 自动生成系统。

---

## 🚀 快速开始

### 前置条件

```bash
# Python 3.8+
python3 --version

# 安装 mcporter (MCP 客户端)
pip install mcporter  # 或 npm install -g mcporter

# 安装依赖
pip install -r requirements.txt
```

### 配置 MCP

编辑 `config/mcporter.json`，确保包含：

```json
{
  "mcpServers": {
    "alpha-vantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    },
    "financial-report": {
      "command": "python3",
      "args": ["mcp-servers/financial-report/index.py"]
    }
  }
}
```

---

## 📱 使用方法

### 方式 1: 飞书机器人

在飞书中发送：
```
@机器人 AAPL
@机器人 阿里巴巴
@机器人 MSFT
```

### 方式 2: 命令行

```bash
# 通过 orchestrator 运行
cd agents
python3 orchestrator-multi.py AAPL

# 通过 feishu-skill 运行
cd skills/feishu-finance-agent
python3 feishu-skill.py 'AAPL'
```

---

## 🏗️ 架构

```
用户 (飞书/命令行)
    ↓
feishu-skill.py (入口)
    ↓
orchestrator-multi.py (协调者)
    ↓
┌─────────────────────────────────────┐
│  4 个独立 Agent 进程                   │
│  • DataFetcher  → 获取财务数据       │
│  • Analyst      → 分析数据           │
│  • Reporter     → 生成报告           │
│  • Reviewer     → 质量检查           │
└─────────────────────────────────────┘
    ↓
MCP Server → Alpha Vantage API
    ↓
One Pager 报告 (Markdown)
```

---

## 📁 项目结构

```
finance-agent-project/
├── agents/                          # 多 Agent 系统
│   ├── orchestrator-multi.py        # 协调者
│   ├── data-fetcher.py              # 数据获取
│   ├── analyst.py                   # 数据分析
│   ├── reporter.py                  # 报告生成
│   ├── reviewer.py                  # 质量审核
│   └── feishu-bridge.py             # 飞书桥接
│
├── mcp-servers/financial-report/    # MCP 服务器
│   └── index.py                     # 财务数据服务
│
├── skills/feishu-finance-agent/     # 飞书技能
│   ├── feishu-skill.py              # 飞书入口
│   └── feishu-stock-processor.py    # 股票处理
│
├── config/
│   └── mcporter.json                # MCP 配置
│
└── requirements.txt                 # Python 依赖
```

---

## 📊 支持股票

### 美股
| 公司 | 代码 | 公司 | 代码 |
|------|------|------|------|
| 苹果 | AAPL | 微软 | MSFT |
| 谷歌 | GOOGL | 亚马逊 | AMZN |
| 特斯拉 | TSLA | 英伟达 | NVDA |
| Meta | META | 奈飞 | NFLX |

### 中概股
| 公司 | 代码 | 公司 | 代码 |
|------|------|------|------|
| 阿里巴巴 | BABA | 腾讯 | TCEHY |
| 拼多多 | PDD | 京东 | JD |
| 百度 | BIDU | 比亚迪 | BYDDY |
| 美团 | MPNGY | 网易 | NTES |
| 小米 | XIACY | | |

---

## 📈 输出示例

```markdown
## 📊 Microsoft Corporation (MSFT)

### 🏢 业务概览
- **行业**: Technology / Software - Infrastructure
- **主营业务**: 开发、许可和支持软件、服务、设备和解决方案
- **市场地位**: 行业领先企业

### 💰 财务摘要 (TTM)
| 指标 | 数值 |
|------|------|
| 市值 | 3.12T |
| 营收 | 245.12B |
| 净利润 | 88.14B |
| PE (TTM) | 36.2 |

### ✨ 投资亮点
• Azure 云业务持续增长，市场份额提升
• AI 投资领先，Copilot 产品商业化顺利

### ⚠️ 风险提示
• 云市场竞争加剧（AWS、Google Cloud）
• AI 投资回报存在不确定性
```

---

## ⚙️ 配置说明

### Alpha Vantage API

1. 获取免费 API Key: https://www.alphavantage.co/support/#api-key
2. 编辑 `config/mcporter.json`，替换 `YOUR_API_KEY`
3. 免费配额：25 次/日

### 模拟数据

当 API 配额用尽时，系统自动使用内置模拟数据（支持常用股票）。

---

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| 协议 | MCP (Model Context Protocol) |
| 数据源 | Alpha Vantage API |
| 通信 | stdin/stdout (JSON) |
| 部署 | 本地运行 |

---


*最后更新：2026-04-09*
