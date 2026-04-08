# 飞书股票查询处理指南

## 触发条件

当你在飞书中收到消息，且满足以下条件时：

1. 消息包含 `@机器人`
2. 消息中包含以下任一内容：
   - **股票代码**: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX 等
   - **公司名称**: 苹果，微软，谷歌，亚马逊，特斯拉，英伟达，Meta，奈飞等
   - **关键词**: 股票，财报，One Pager, 分析，查询

**示例消息:**
- `@机器人 AAPL`
- `@机器人 生成苹果财报`
- `@机器人 查询 MSFT`
- `@机器人 特斯拉 One Pager`
- `@机器人 来一个英伟达的财报分析`

---

## 处理流程

### 步骤 1: 判断是否是股票查询

检查消息是否包含：
- `@机器人` + 股票代码/公司名称/关键词

**如果不是股票查询** → 正常回复或忽略

**如果是股票查询** → 继续步骤 2

---

### 步骤 2: 调用多 Agent 系统

使用 `exec` 工具执行 Python 脚本：

```bash
exec "python3 /home/nio/.openclaw/workspace/skills/feishu-finance-agent/feishu-skill.py '<消息内容>'"
```

**示例:**
```bash
exec "python3 /home/nio/.openclaw/workspace/skills/feishu-finance-agent/feishu-skill.py '@机器人 AAPL'"
```

---

### 步骤 3: 解析返回结果

脚本返回 JSON 格式：

```json
{
  "success": true,
  "symbol": "AAPL",
  "reply": {
    "msg_type": "post",
    "content": {
      "post": {
        "zh_cn": {
          "title": "📊 AAPL 财报 One Pager",
          "content": [
            [{"tag": "text", "text": "✅ 质量评分：100/100..."}],
            [{"tag": "text", "text": "## 📊 Apple Inc. (AAPL)..."}],
            [{"tag": "text", "text": "生成时间：..."}]
          ]
        }
      }
    }
  }
}
```

**提取 `reply` 字段的内容**，这是飞书回复的格式。

---

### 步骤 4: 回复到飞书

使用 `message` 工具发送回复：

```bash
message send --channel feishu --target <chat_id> --message "<回复内容>"
```

**如果返回的是富文本格式**，需要构造飞书卡片消息。

**简化方式:** 直接发送 Markdown 格式的文本：

```bash
message send --channel feishu --target <chat_id> --message "## 📊 AAPL 财报 One Pager

### 🏢 业务概览
...

### 💰 财务摘要
...

### ✨ 投资亮点
...

### ⚠️ 风险提示
..."
```

---

## 完整示例

### 用户消息
```
@机器人 AAPL
```

### AI Agent 处理

```bash
# 步骤 1: 调用多 Agent 系统
exec "python3 /home/nio/.openclaw/workspace/skills/feishu-finance-agent/feishu-skill.py '@机器人 AAPL'"

# 步骤 2: 解析返回（假设返回存储在 $result 中）
# $result = {"success": true, "symbol": "AAPL", "reply": {...}}

# 步骤 3: 回复到飞书
message send --channel feishu --target "oc_chat_id" --message "$result.reply.content"
```

### 飞书回复
```
📊 AAPL 财报 One Pager

✅ 质量评分：100/100
⏱️ 耗时：2500ms

## 📊 Apple Inc. (AAPL)

### 🏢 业务概览
- **行业**: Technology / Consumer Electronics
- **主营业务**: 设计、制造和销售智能手机...

### 💰 财务摘要 (TTM)
| 指标 | 数值 |
|------|------|
| 市值 | 2.85T |
| 营收 | 383.29B |
...

### ✨ 投资亮点
• 全球最有价值品牌之一...

### ⚠️ 风险提示
• 对 iPhone 销售依赖度较高...

---
生成时间：2026/04/08 20:45:00
```

---

## 错误处理

### 情况 1: 无法识别股票代码

**返回:**
```json
{
  "success": false,
  "error": "无法识别股票代码",
  "message": "请提供股票代码 (如 AAPL) 或公司名称 (如 苹果)"
}
```

**回复到飞书:**
```
❌ 无法识别股票代码

请提供股票代码 (如 AAPL, MSFT) 或公司名称 (如 苹果，微软，特斯拉)

示例：
@机器人 AAPL
@机器人 生成苹果财报
```

### 情况 2: 处理超时

**返回:**
```json
{
  "success": false,
  "error": "处理超时"
}
```

**回复到飞书:**
```
⏱️ 处理超时

查询处理时间超过 60 秒，请稍后重试。

如果问题持续，可能是：
1. API 配额限制
2. 网络问题
3. 服务器繁忙
```

### 情况 3: 不是股票查询

**不执行任何操作**，正常回复或忽略。

---

## 支持的公司/股票代码

| 公司 | 代码 | 公司 | 代码 |
|------|------|------|------|
| 苹果 | AAPL | 微软 | MSFT |
| 谷歌 | GOOGL | 亚马逊 | AMZN |
| 特斯拉 | TSLA | 英伟达 | NVDA |
| Meta | META | 奈飞 | NFLX |
| 比亚迪 | BYDDY | 美团 | MPNGY |

---

## 性能指标

| 指标 | 预期 |
|------|------|
| 响应时间 | 2-3 秒 |
| 质量评分 | 100/100 |
| 成功率 | > 95% |

---

## 注意事项

1. **API 配额**: Alpha Vantage 每日 25 次免费请求
2. **超时设置**: 60 秒超时
3. **消息长度**: 飞书富文本消息最大 10000 字符
4. **工作目录**: 脚本需要在 `/home/nio/.openclaw/workspace` 运行

---

*最后更新：2026-04-08*
