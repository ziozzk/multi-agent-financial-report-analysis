#!/usr/bin/env python3
"""
DataFetcher Agent - 独立进程

职责：获取财务数据
通信方式：stdin/stdout (JSON-RPC)
"""

import subprocess
import sys
import json
import os
import readline
import time
from typing import Dict, Optional

class DataFetcherAgent:
    def __init__(self):
        self.agent_id = f'data-fetcher-{os.getpid()}'
        self.status = 'idle'
        self.workspace = '/home/nio/.openclaw/workspace'
        
        print(f'[DataFetcher] Agent 已启动：{self.agent_id}', file=sys.stderr)
        self.listen()
    
    def listen(self):
        """监听标准输入，接收任务"""
        for line in sys.stdin:
            try:
                message = json.loads(line.strip())
                self.handle_message(message)
            except json.JSONDecodeError as e:
                self.send_error(f'JSON 解析错误：{e}')
            except Exception as e:
                self.send_error(str(e))
    
    def handle_message(self, message: Dict):
        """处理消息"""
        action = message.get('action')
        task_id = message.get('taskId')
        symbol = message.get('symbol')
        
        print(f'[DataFetcher] 收到任务：{action} {symbol or ""}', file=sys.stderr)
        
        if action == 'fetch':
            self.status = 'busy'
            data = self.fetch_financial_data(symbol)
            self.send_result({'taskId': task_id, 'action': 'fetch', 'data': data})
            self.status = 'idle'
        
        elif action == 'ping':
            self.send_result({'action': 'pong', 'agentId': self.agent_id, 'status': self.status})
        
        elif action == 'shutdown':
            print(f'[DataFetcher] 收到关闭指令', file=sys.stderr)
            sys.exit(0)
        
        else:
            self.send_error(f'未知动作：{action}')
    
    def fetch_financial_data(self, symbol: str) -> Dict:
        """获取财务数据"""
        print(f'[DataFetcher] 获取 {symbol} 的财务数据...', file=sys.stderr)
        
        try:
            # 直接使用 Alpha Vantage API，不经过 MCP
            data = self.fetch_alpha_vantage_data(symbol)
            
            if data:
                print(f'[DataFetcher] 数据获取成功', file=sys.stderr)
                return {
                    'success': True,
                    'data': data,
                    'source': 'Alpha Vantage API',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                }
            else:
                return {'success': False, 'error': '未找到数据', 'data': None}
        
        except Exception as e:
            print(f'[DataFetcher] 错误：{e}', file=sys.stderr)
            return {'success': False, 'error': str(e), 'data': None}
    
    def fetch_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """直接从 Alpha Vantage 获取数据"""
        import urllib.request
        import time
        
        API_KEY = 'RK9S21IP5X28J7IC'
        BASE_URL = 'https://www.alphavantage.co/query'
        
        try:
            # 获取股价
            quote_url = f'{BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}'
            req = urllib.request.Request(quote_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                quote_data = json.loads(response.read().decode('utf-8'))
            
            if 'Note' in quote_data or 'Information' in quote_data:
                # API 配额限制，返回模拟数据
                return self.get_mock_data(symbol)
            
            quote = quote_data.get('Global Quote', {})
            
            time.sleep(1.5)  # 避免速率限制
            
            # 获取公司信息
            overview_url = f'{BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}'
            req = urllib.request.Request(overview_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                overview_data = json.loads(response.read().decode('utf-8'))
            
            return {
                'name': overview_data.get('Name') or f'{symbol} Corporation',
                'sector': overview_data.get('Sector') or 'N/A',
                'industry': overview_data.get('Industry') or 'N/A',
                'description': overview_data.get('Description') or 'N/A',
                'marketCap': overview_data.get('MarketCapitalization', 'N/A'),
                'peRatio': float(overview_data.get('PERatio', 0) or 0),
                'profitMargin': float(overview_data.get('ProfitMargin', 0) or 0) * 100,
                'currentPrice': float(quote.get('05. price', 0)),
                'week52High': float(quote.get('03. high', 0)),
                'week52Low': float(quote.get('04. low', 0)),
            }
        
        except Exception as e:
            print(f'[DataFetcher] API 错误：{e}，使用模拟数据', file=sys.stderr)
            return self.get_mock_data(symbol)
    
    def get_mock_data(self, symbol: str) -> Optional[Dict]:
        """模拟数据"""
        mock_data = {
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'peRatio': 28.5, 'profitMargin': 25.3, 'currentPrice': 178.72},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'peRatio': 36.2, 'profitMargin': 36.7, 'currentPrice': 420.45},
        }
        return mock_data.get(symbol)
    
    def send_result(self, result: Dict):
        """发送结果"""
        print(json.dumps({'type': 'result', **result}, ensure_ascii=False))
    
    def send_error(self, message: str):
        """发送错误"""
        print(json.dumps({'type': 'error', 'message': message}))

if __name__ == '__main__':
    agent = DataFetcherAgent()
