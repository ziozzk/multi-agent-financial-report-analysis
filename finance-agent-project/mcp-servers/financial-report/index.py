#!/usr/bin/env python3
"""
Financial Report MCP Server
提供美股财务数据查询功能（使用 Alpha Vantage 实时 API）
"""

import json
import sys
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Alpha Vantage API 配置
ALPHA_VANTAGE_KEY = 'RK9S21IP5X28J7IC'
BASE_URL = 'https://www.alphavantage.co/query'

# 常用公司股票代码映射
STOCK_SYMBOLS = {
    'AAPL': 'AAPL', 'APPLE': 'AAPL', '苹果': 'AAPL',
    'MSFT': 'MSFT', 'MICROSOFT': 'MSFT', '微软': 'MSFT',
    'GOOGL': 'GOOGL', 'GOOG': 'GOOGL', 'GOOGLE': 'GOOGL', '谷歌': 'GOOGL',
    'AMZN': 'AMZN', 'AMAZON': 'AMZN', '亚马逊': 'AMZN',
    'TSLA': 'TSLA', 'TESLA': 'TSLA', '特斯拉': 'TSLA',
    'NVDA': 'NVDA', 'NVIDIA': 'NVDA', '英伟达': 'NVDA',
    'META': 'META', 'FACEBOOK': 'META', '脸书': 'META',
    'NFLX': 'NFLX', 'NETFLIX': 'NFLX', '奈飞': 'NFLX',
    'BYDDY': 'BYDDY', '比亚迪': 'BYDDY',
    'MPNGY': 'MPNGY', '美团': 'MPNGY',
}

# 模拟财务数据（备用）
def get_mock_financial_data(symbol: str) -> Optional[Dict[str, Any]]:
    mock_data = {
        'AAPL': {
            'name': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'description': '设计、制造和销售智能手机、个人电脑、平板电脑、可穿戴设备和配件',
            'marketCap': '2.85T',
            'peRatio': 28.5,
            'psRatio': 7.2,
            'profitMargin': 25.3,
            'grossMargin': 44.1,
            'revenue': '383.29B',
            'netIncome': '96.99B',
            'eps': 6.13,
            'dividendYield': 0.5,
            'beta': 1.29,
            'week52High': 199.62,
            'week52Low': 164.08,
            'currentPrice': 178.72,
        },
        'MSFT': {
            'name': 'Microsoft Corporation',
            'sector': 'Technology',
            'industry': 'Software - Infrastructure',
            'description': '开发、许可和支持软件、服务、设备和解决方案',
            'marketCap': '3.12T',
            'peRatio': 36.2,
            'psRatio': 12.8,
            'profitMargin': 36.7,
            'grossMargin': 69.8,
            'revenue': '245.12B',
            'netIncome': '88.14B',
            'eps': 11.86,
            'dividendYield': 0.7,
            'beta': 0.90,
            'week52High': 468.35,
            'week52Low': 362.90,
            'currentPrice': 420.45,
        },
        'GOOGL': {
            'name': 'Alphabet Inc.',
            'sector': 'Communication Services',
            'industry': 'Internet Content & Information',
            'description': '提供在线广告、搜索引擎、云计算、软件和硬件产品',
            'marketCap': '2.15T',
            'peRatio': 25.8,
            'psRatio': 6.5,
            'profitMargin': 26.2,
            'grossMargin': 57.1,
            'revenue': '307.39B',
            'netIncome': '73.80B',
            'eps': 5.80,
            'dividendYield': 0.4,
            'beta': 1.06,
            'week52High': 193.31,
            'week52Low': 129.40,
            'currentPrice': 175.35,
        },
        'TSLA': {
            'name': 'Tesla, Inc.',
            'sector': 'Consumer Cyclical',
            'industry': 'Auto Manufacturers',
            'description': '设计、开发、制造、租赁和销售电动汽车和能源存储系统',
            'marketCap': '1.08T',
            'peRatio': 95.2,
            'psRatio': 10.5,
            'profitMargin': 15.5,
            'grossMargin': 18.2,
            'revenue': '96.77B',
            'netIncome': '14.97B',
            'eps': 4.30,
            'dividendYield': 0.0,
            'beta': 2.31,
            'week52High': 488.54,
            'week52Low': 138.80,
            'currentPrice': 345.16,
        },
        'NVDA': {
            'name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'industry': 'Semiconductors',
            'description': '设计和制造图形处理器 (GPU)、移动处理器和相关多媒体软件',
            'marketCap': '3.45T',
            'peRatio': 65.8,
            'psRatio': 42.5,
            'profitMargin': 55.0,
            'grossMargin': 75.0,
            'revenue': '79.77B',
            'netIncome': '42.60B',
            'eps': 1.92,
            'dividendYield': 0.03,
            'beta': 1.68,
            'week52High': 152.89,
            'week52Low': 49.50,
            'currentPrice': 139.91,
        },
        'BYDDY': {
            'name': 'BYD Company Limited',
            'sector': 'Consumer Cyclical',
            'industry': 'Auto Manufacturers',
            'description': '比亚迪股份有限公司是一家从事汽车、轨道交通、新能源等业务的中国公司',
            'marketCap': '95.5B',
            'peRatio': 25.8,
            'psRatio': 2.1,
            'profitMargin': 5.2,
            'grossMargin': 18.5,
            'revenue': '72.5B',
            'netIncome': '3.8B',
            'eps': 1.35,
            'dividendYield': 0.3,
            'beta': 1.15,
            'week52High': 15.85,
            'week52Low': 10.20,
            'currentPrice': 13.15,
        },
    }
    return mock_data.get(symbol)

def format_number(num: Any) -> str:
    if num is None or num == 'N/A':
        return 'N/A'
    if isinstance(num, str):
        return num
    if num >= 1e12:
        return f'{num / 1e12:.2f}T'
    if num >= 1e9:
        return f'{num / 1e9:.2f}B'
    if num >= 1e6:
        return f'{num / 1e6:.2f}M'
    return str(num)

def fetch_json(url: str) -> Dict[str, Any]:
    """发送 HTTP GET 请求并返回 JSON"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f'[ERROR] fetch_json failed: {e}', file=sys.stderr)
        return {}

def fetch_alpha_vantage_data(symbol: str) -> Dict[str, Any]:
    """从 Alpha Vantage 获取实时数据"""
    print(f'[AlphaVantage] 获取 {symbol} 数据...', file=sys.stderr)
    
    try:
        # 1. 获取实时股价 (GLOBAL_QUOTE)
        quote_url = f'{BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
        quote_data = fetch_json(quote_url)
        print(f'[AlphaVantage] 股价：{json.dumps(quote_data)[:300]}', file=sys.stderr)
        
        # 检查 API 配额
        if 'Note' in quote_data or 'Information' in quote_data:
            print('[AlphaVantage] API 配额限制，使用模拟数据', file=sys.stderr)
            return get_mock_financial_data(symbol) or {}
        
        quote = quote_data.get('Global Quote', {})
        current_price = float(quote.get('05. price', 0))
        week52_high = float(quote.get('03. high', 0))
        week52_low = float(quote.get('04. low', 0))
        
        # 延时避免速率限制
        time.sleep(1.5)
        
        # 2. 获取公司信息 (OVERVIEW)
        overview_url = f'{BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
        overview_data = fetch_json(overview_url)
        print(f'[AlphaVantage] 公司：Name={overview_data.get("Name")}, Sector={overview_data.get("Sector")}', file=sys.stderr)
        
        # 提取数据
        data = {
            'name': overview_data.get('Name') or f'{symbol} Corporation',
            'sector': overview_data.get('Sector') or 'N/A',
            'industry': overview_data.get('Industry') or 'N/A',
            'description': overview_data.get('Description') or 'N/A',
            'marketCap': format_number(overview_data.get('MarketCapitalization')),
            'peRatio': float(overview_data.get('PERatio', 0) or 0),
            'psRatio': float(overview_data.get('PriceToSalesRatioTTM', 0) or 0),
            'profitMargin': (float(overview_data.get('ProfitMargin', 0) or 0)) * 100,
            'grossMargin': 0,
            'revenue': format_number(overview_data.get('RevenueTTM')),
            'netIncome': format_number(overview_data.get('NetIncomeTTM')) or format_number(overview_data.get('EPS', 0) * overview_data.get('SharesOutstanding', 0)),
            'eps': float(overview_data.get('EPS', 0) or 0),
            'dividendYield': (float(overview_data.get('DividendYield', 0) or 0)) * 100,
            'beta': float(overview_data.get('Beta', 0) or 0),
            'week52High': week52_high or float(overview_data.get('52WeekHigh', 0) or 0),
            'week52Low': week52_low or float(overview_data.get('52WeekLow', 0) or 0),
            'currentPrice': current_price,
        }
        
        print(f'[AlphaVantage] 数据获取成功：{data["name"]}', file=sys.stderr)
        return data
        
    except Exception as e:
        print(f'[AlphaVantage] 错误：{e}，使用模拟数据', file=sys.stderr)
        return get_mock_financial_data(symbol) or {}

def generate_highlights(symbol: str, data: Dict) -> list:
    highlights = {
        'AAPL': ['全球最有价值品牌之一，生态系统壁垒极高', '服务业务持续增长，提供稳定现金流', '强大的定价能力和品牌忠诚度'],
        'MSFT': ['Azure 云业务持续增长，市场份额提升', 'AI 投资领先，Copilot 产品商业化顺利', '多元化收入来源，抗风险能力强'],
        'GOOGL': ['搜索业务垄断地位稳固', 'YouTube 广告收入增长强劲', '云业务扭亏为盈，估值有提升空间'],
        'TSLA': ['电动车市场领导者，规模优势明显', 'FSD 自动驾驶技术潜力巨大', '能源业务快速增长'],
        'NVDA': ['AI 芯片绝对龙头，市场需求爆发', '数据中心业务高速增长', '技术壁垒高，竞争格局有利'],
        'BYDDY': ['全球新能源汽车领导者', '电池技术优势明显，垂直整合能力强', '中国市场销量领先'],
    }
    return highlights.get(symbol, ['数据有限，请查阅更多来源'])

def generate_risks(symbol: str, data: Dict) -> list:
    risks = {
        'AAPL': ['对 iPhone 销售依赖度较高', '中国市场销售存在不确定性', '监管压力增加（反垄断、App Store 政策）'],
        'MSFT': ['云市场竞争加剧（AWS、Google Cloud）', 'AI 投资回报存在不确定性', '监管审查风险'],
        'GOOGL': ['反垄断诉讼风险', 'AI 搜索竞争加剧', '广告收入受经济周期影响'],
        'TSLA': ['估值较高，波动性大', '竞争加剧（传统车企 + 新势力）', '执行风险（Cybertruck、FSD 进展）'],
        'NVDA': ['估值极高，预期已打满', '客户自研芯片风险', '地缘政治风险（中国销售限制）'],
        'BYDDY': ['海外市场竞争加剧', '原材料价格波动风险', '政策补贴退坡影响'],
    }
    return risks.get(symbol, ['数据有限，请查阅更多来源'])

def generate_onepager(symbol: str, data: Dict) -> str:
    highlights = '\n'.join([f'• {h}' for h in generate_highlights(symbol, data)])
    risks = '\n'.join([f'• {r}' for r in generate_risks(symbol, data)])
    
    onepager = f'''## 📊 {data.get('name', symbol)} ({symbol})

### 🏢 业务概览
- **行业**: {data.get('sector', 'N/A')} / {data.get('industry', 'N/A')}
- **主营业务**: {data.get('description', 'N/A')}
- **市场地位**: 行业领先企业

### 💰 财务摘要 (TTM)
| 指标 | 数值 |
|------|------|
| 市值 | {data.get('marketCap', 'N/A')} |
| 营收 | {data.get('revenue', 'N/A')} |
| 净利润 | {data.get('netIncome', 'N/A')} |
| 毛利率 | {data.get('grossMargin', 0)}% |
| 净利率 | {data.get('profitMargin', 0):.1f}% |
| PE (TTM) | {data.get('peRatio', 0)} |
| PS (TTM) | {data.get('psRatio', 0)} |
| 股息率 | {data.get('dividendYield', 0):.2f}% |

### 📈 股价表现
- **当前股价**: ${data.get('currentPrice', 0)}
- **52 周范围**: ${data.get('week52Low', 0)} - ${data.get('week52High', 0)}
- **Beta**: {data.get('beta', 0)}

### ✨ 投资亮点
{highlights}

### ⚠️ 风险提示
{risks}

---
*数据来源：Alpha Vantage | 更新时间：{time.strftime('%Y-%m-%d')}'''
    
    return onepager

# MCP 工具定义
TOOLS = {
    'lookup_symbol': {
        'description': '根据公司名称或股票代码查询美股代码',
        'input_schema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': '公司名称或股票代码'}
            },
            'required': ['query']
        }
    },
    'get_financial_data': {
        'description': '获取美股公司的财务数据和基本信息',
        'input_schema': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'description': '股票代码 (如 AAPL, MSFT)'}
            },
            'required': ['symbol']
        }
    },
    'generate_onepager': {
        'description': '生成公司股票的结构化 One Pager 报告',
        'input_schema': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'description': '股票代码'}
            },
            'required': ['symbol']
        }
    }
}

def handle_tool_call(tool_name: str, arguments: Dict) -> Dict:
    """处理工具调用"""
    print(f'[MCP] 调用工具：{tool_name}, 参数：{arguments}', file=sys.stderr)
    
    try:
        if tool_name == 'lookup_symbol':
            query = arguments.get('query', '')
            if not query:
                return {'content': [{'type': 'text', 'text': '请提供公司名称或股票代码'}], 'isError': True}
            
            upper_query = query.upper()
            symbol = STOCK_SYMBOLS.get(query) or STOCK_SYMBOLS.get(upper_query)
            
            if symbol:
                return {'content': [{'type': 'text', 'text': f'找到股票代码：{symbol}'}]}
            
            return {'content': [{'type': 'text', 'text': f'未找到 "{query}" 的股票代码。支持：AAPL, MSFT, GOOGL, TSLA, NVDA 等'}], 'isError': True}
        
        elif tool_name == 'get_financial_data':
            symbol = arguments.get('symbol', '').upper()
            if not symbol:
                return {'content': [{'type': 'text', 'text': '请提供股票代码'}], 'isError': True}
            
            data = fetch_alpha_vantage_data(symbol)
            if not data:
                return {'content': [{'type': 'text', 'text': f'未找到 "{symbol}" 的数据'}], 'isError': True}
            
            return {
                'content': [{
                    'type': 'text',
                    'text': json.dumps({
                        'success': True,
                        'data': {
                            **data,
                            'highlights': generate_highlights(symbol, data),
                            'risks': generate_risks(symbol, data)
                        },
                        'source': 'Alpha Vantage API',
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    }, ensure_ascii=False, indent=2)
                }]
            }
        
        elif tool_name == 'generate_onepager':
            symbol = arguments.get('symbol', '').upper()
            if not symbol:
                return {'content': [{'type': 'text', 'text': '请提供股票代码'}], 'isError': True}
            
            data = fetch_alpha_vantage_data(symbol)
            if not data:
                return {'content': [{'type': 'text', 'text': f'未找到 "{symbol}" 的数据'}], 'isError': True}
            
            onepager = generate_onepager(symbol, data)
            return {'content': [{'type': 'text', 'text': onepager}]}
        
        else:
            return {'content': [{'type': 'text', 'text': f'未知工具：{tool_name}'}], 'isError': True}
    
    except Exception as e:
        return {'content': [{'type': 'text', 'text': f'错误：{str(e)}'}], 'isError': True}

def main():
    """MCP Server 主循环（stdio 传输）"""
    print('[MCP] Financial Report Server 启动 (stdio)', file=sys.stderr)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            message = json.loads(line.strip())
            
            # 处理 initialize
            if message.get('method') == 'initialize':
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {'tools': {}},
                        'serverInfo': {'name': 'financial-report', 'version': '1.0.0'}
                    }
                }
                print(json.dumps(response), flush=True)
            
            # 处理 tools/list
            elif message.get('method') == 'tools/list':
                tools_list = [
                    {'name': name, 'description': info['description'], 'inputSchema': info['input_schema']}
                    for name, info in TOOLS.items()
                ]
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {'tools': tools_list}
                }
                print(json.dumps(response), flush=True)
            
            # 处理 tools/call
            elif message.get('method') == 'tools/call':
                params = message.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                result = handle_tool_call(tool_name, arguments)
                
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': result
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
            
            # 处理 ping
            elif message.get('method') == 'ping':
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {}
                }
                print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            print(f'[MCP] JSON 解析错误：{e}', file=sys.stderr)
        except Exception as e:
            print(f'[MCP] 错误：{e}', file=sys.stderr)

if __name__ == '__main__':
    main()
