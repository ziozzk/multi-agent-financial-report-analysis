# 多 Agent 美股财报分析系统 📊

> 基于 Python + MCP  的财报 One Pager 自动生成系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Alpha Vantage](https://img.shields.io/badge/Data-Alpha_Vantage-blue)](https://www.alphavantage.co/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-green)](https://modelcontextprotocol.io/)

---

## ✨ 功能特性

- 🤖 **多 Agent 协作** - 5 个独立进程 Agent 分工合作
- 📈 **实时股价** - Alpha Vantage 实时美股数据
- 💰 **财务摘要** - 营收、利润、毛利率等关键指标
- ✨ **智能分析** - AI 生成的投资亮点和风险提示
- ✅ **质量保障** - 自动化 7 项质量检查
- 🐍 **Python 实现** - 完整的 Python 技术栈

---

## 🚀 快速开始

### 前置条件

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **mcporter** - MCP 客户端
   ```bash
   pip install mcporter  # 或 npm install -g mcporter
   ```

3. **Alpha Vantage API Key** - 已配置（？）
   - 每日 25 次免费请求

### 安装步骤

#### 1. 安装 Python 依赖

```bash
cd /home/nio/.openclaw/workspace
pip install -r requirements.txt
```

#### 2. 验证 MCP 配置

```bash
mcporter list
# 应该看到 financial-report 和 alpha-vantage 两个服务器
```

#### 3. 测试运行

```bash
# 测试完整多 Agent 流程
cd agents
python3 test-python-flow.py AAPL
```

---

## 📱 使用方法

### 方式 1: 测试完整流程

```bash
cd /home/nio/.openclaw/workspace/agents

# 测试 AAPL
python3 test-python-flow.py AAPL

# 测试 MSFT
python3 test-python-flow.py MSFT

# 测试中文名称
python3 test-python-flow.py 苹果
```

### 方式 2: 使用启动脚本

```bash
./start.sh AAPL
```

### 方式 3: 直接调用 MCP

```bash
mcporter call financial-report.generate_onepager symbol=AAPL
```

### 输出示例

```markdown
## 📊 Apple Inc. (AAPL)

### 🏢 业务概览
- **行业**: Technology / Consumer Electronics
- **主营业务**: 设计、制造和销售智能手机、个人电脑、平板电脑...
- **市场地位**: 行业领先企业

### 💰 财务摘要 (TTM)
| 指标 | 数值 |
|------|------|
| 市值 | 2.85T |
| 营收 | 383.29B |
| 净利润 | 96.99B |
| 毛利率 | 44.1% |
| PE (TTM) | 28.5 |

### ✨ 投资亮点
• 全球最有价值品牌之一，生态系统壁垒极高
• 服务业务持续增长，提供稳定现金流
• 强大的定价能力和品牌忠诚度

### ⚠️ 风险提示
• 对 iPhone 销售依赖度较高
• 中国市场销售存在不确定性
• 监管压力增加（反垄断、App Store 政策）
```

---

## 🏗️ 架构说明

```
用户输入 (AAPL)
    ↓
Orchestrator (协调者进程)
    ↓
┌─────────────────────────────────────────┐
│  5 个独立进程 Agent                        │
│  - DataFetcher  → 获取财务数据           │
│  - Analyst      → 分析数据               │
│  - Reporter     → 生成报告               │
│  - Reviewer     → 质量检查               │
└─────────────────────────────────────────┘
    ↓
MCP Server (Python)
    ↓
Alpha Vantage API (实时数据)
```

详见：[agents/PYTHON_README.md](./agents/PYTHON_README.md)

---

## 📁 项目结构

```
/home/nio/.openclaw/workspace/
├── agents/
│   ├── orchestrator-multi.py    # 协调者 Agent
│   ├── data-fetcher.py          # 数据获取 Agent
│   ├── analyst.py               # 数据分析 Agent
│   ├── reporter.py              # 报告生成 Agent
│   ├── reviewer.py              # 质量审核 Agent
│   ├── feishu-bridge.py         # 飞书桥接器
│   ├── test-python-flow.py      # 完整流程测试
│   ├── start.sh                 # 启动脚本
│   └── PYTHON_README.md         # Python 使用指南
│
├── mcp-servers/
│   └── financial-report/
│       ├── index.py             # Python 版 MCP Server
│       └── index.js.bak         # Node.js 备份
│
├── config/
│   └── mcporter.json            # MCP 配置
│
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

---

## 🔧 配置说明

### 支持的股票

目前支持所有美股，常用股票：

| 公司 | 代码 | 公司 | 代码 |
|------|------|------|------|
| 苹果 | AAPL | 微软 | MSFT |
| 谷歌 | GOOGL | 亚马逊 | AMZN |
| 特斯拉 | TSLA | 英伟达 | NVDA |
| Meta | META | 奈飞 | NFLX |

、

## 🛠️ 开发

### MCP 服务器开发

```bash
cd mcp-servers/financial-report
npm install
node index.js
```

### 测试 API 调用

```bash
# 直接调用 Alpha Vantage API
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_API_KEY"

# 通过 MCP 调用
mcporter call alpha-vantage.TOOL_CALL --args '{"tool_name": "GLOBAL_QUOTE", "arguments": {"symbol": "AAPL"}}'
```

---

## ⚠️ 注意事项

1. **API Key 安全**
   - 不要将包含真实 API Key 的配置文件提交到 Git
   - 使用 `config/mcporter.example.json` 作为模板

2. **数据延迟**
   - 股价数据有 15 分钟延迟
   - 不适合实时交易决策

3. **配额限制**
   - 免费账户每日 25 次请求
   - 建议缓存结果减少请求

---

## 📚 文档

- [架构说明](./feishu-finance-bot/ARCHITECTURE.md)
- [安装指南](./feishu-finance-bot/SETUP.md)
- [快速开始](./feishu-finance-bot/QUICKSTART.md)
- [Alpha Vantage 配置](./memory/alpha-vantage-setup.example.md)
- [MCP 服务器列表](./memory/mcp-servers-reference.md)



## 🔗 相关资源

- [OpenClaw 文档](https://docs.openclaw.ai)
- [Alpha Vantage API](https://www.alphavantage.co)
- [MCP 协议](https://modelcontextprotocol.io)
- [飞书开放平台](https://open.feishu.cn)

---


*最后更新：2026-04-08*
