#!/usr/bin/env python3
"""
DataFetcher Agent - 独立进程

职责：获取财务数据（通过 MCP Server 统一调用）
通信方式：stdin/stdout (JSON-RPC)

架构说明:
- 不再直接调用 Alpha Vantage API
- 通过 MCP Server (financial-report) 获取数据
- API Key 集中在 MCP Server 中管理
"""

import subprocess
import sys
import json
import os
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
        """
        获取财务数据（通过 MCP Server 调用）
        
        架构改进:
        - 通过 MCP Server 统一调用 Alpha Vantage API
        - API Key 集中在 MCP Server 中管理
        - 复用 MCP Server 的数据缓存和配额管理
        """
        print(f'[DataFetcher] 获取 {symbol} 的财务数据 (via MCP)...', file=sys.stderr)
        start_time = time.time()
        
        try:
            # 调用 MCP Server
            print(f'[DataFetcher] 执行：mcporter call financial-report.get_financial_data symbol={symbol}', file=sys.stderr)
            result = subprocess.run(
                ['mcporter', 'call', 'financial-report.get_financial_data', f'symbol={symbol}'],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = int((time.time() - start_time) * 1000)
            print(f'[DataFetcher] MCP 调用完成，耗时：{elapsed}ms, returncode={result.returncode}', file=sys.stderr)
            
            # 解析 MCP 响应
            if result.returncode == 0:
                response = json.loads(result.stdout)
                content = response.get('content', [{}])[0].get('text', '{}')
                data = json.loads(content)
                
                if data.get('success'):
                    print(f'[DataFetcher] 数据获取成功 (MCP)', file=sys.stderr)
                    return {
                        'success': True,
                        'data': data.get('data'),
                        'source': 'MCP financial-report',
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', '未知错误'),
                        'data': None
                    }
            else:
                # MCP 调用失败，使用备用模拟数据
                print(f'[DataFetcher] MCP 调用失败，使用模拟数据', file=sys.stderr)
                mock_data = self.get_mock_data(symbol)
                if mock_data:
                    return {
                        'success': True,
                        'data': mock_data,
                        'source': 'Mock Data (Fallback)',
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                return {
                    'success': False,
                    'error': f'MCP 调用失败：{result.stderr}',
                    'data': None
                }
        
        except subprocess.TimeoutExpired:
            print(f'[DataFetcher] MCP 调用超时', file=sys.stderr)
            return {
                'success': False,
                'error': 'MCP 调用超时',
                'data': None
            }
        
        except Exception as e:
            print(f'[DataFetcher] 错误：{e}', file=sys.stderr)
            return {'success': False, 'error': str(e), 'data': None}
    
    def get_mock_data(self, symbol: str) -> Optional[Dict]:
        """
        模拟数据（备用）
        当 MCP Server 不可用或 API 配额耗尽时使用
        """
        mock_data = {
            'AAPL': {
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'peRatio': 28.5,
                'profitMargin': 25.3,
                'currentPrice': 178.72,
                'marketCap': '2.85T',
                'revenue': '383.29B',
            },
            'MSFT': {
                'name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software - Infrastructure',
                'peRatio': 36.2,
                'profitMargin': 36.7,
                'currentPrice': 420.45,
                'marketCap': '3.12T',
                'revenue': '245.12B',
            },
            'GOOGL': {
                'name': 'Alphabet Inc.',
                'sector': 'Communication Services',
                'industry': 'Internet Content & Information',
                'peRatio': 25.8,
                'profitMargin': 26.2,
                'currentPrice': 175.35,
                'marketCap': '2.15T',
                'revenue': '307.39B',
            },
            'TSLA': {
                'name': 'Tesla, Inc.',
                'sector': 'Consumer Cyclical',
                'industry': 'Auto Manufacturers',
                'peRatio': 95.2,
                'profitMargin': 15.5,
                'currentPrice': 345.16,
                'marketCap': '1.08T',
                'revenue': '96.77B',
            },
            'NVDA': {
                'name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'peRatio': 65.8,
                'profitMargin': 55.0,
                'currentPrice': 139.91,
                'marketCap': '3.45T',
                'revenue': '79.77B',
            },
        }
        return mock_data.get(symbol)
    
    def send_result(self, result: Dict):
        """发送结果"""
        print(json.dumps({'type': 'result', **result}, ensure_ascii=False), flush=True)
    
    def send_error(self, message: str):
        """发送错误"""
        print(json.dumps({'type': 'error', 'message': message}), flush=True)

if __name__ == '__main__':
    agent = DataFetcherAgent()
