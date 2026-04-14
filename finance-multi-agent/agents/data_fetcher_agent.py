#!/usr/bin/env python3
"""
DataFetcher Agent - 数据获取

职责：
- 获取财务数据（通过 MCP Server）
- 自主选择 API（基于成功率）
- 降级策略（API 失败时用模拟数据）

能力：
- 自主性：根据历史成功率选择 API
- 学习能力：记录各 API 的成功率
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional

from message_queue import REQUEST_QUEUE, DATA_QUEUE, AgentRegistry
from base_agent import BaseAgent


class DataFetcherAgent(BaseAgent):
    """数据获取 Agent"""
    
    def __init__(self):
        super().__init__(
            name='DataFetcher',
            agent_type='DataFetcher',
            capabilities=['fetch_financial_data', 'fetch_historical_data', 'fetch_industry_data']
        )
        
        self.workspace = Path('/home/nio/.openclaw/workspace')
        
        # API 统计（学习能力）
        self.api_stats = {
            'alpha_vantage': {'success': 0, 'total': 0},
            'mock': {'success': 0, 'total': 0}
        }
        
        # API 优先级（用于自主选择）
        self.api_priority = {
            'alpha_vantage': 100,  # 主要 API
            'mock': 50             # 备用
        }
        
        self._load_api_stats()
    
    def _load_api_stats(self):
        """加载历史 API 统计"""
        stats_file = Path('/tmp/agent-stats/datafetcher_api.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.api_stats = json.load(f)
            except:
                pass
    
    def _save_api_stats(self):
        """保存 API 统计"""
        stats_file = Path('/tmp/agent-stats/datafetcher_api.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.api_stats, f, indent=2)
    
    def consume_message(self, timeout_ms: int = 5000):
        """从请求队列消费消息"""
        return REQUEST_QUEUE.consume(timeout_ms=timeout_ms)
    
    def handle_message(self, message: Dict):
        """处理消息"""
        action = message.get('action')
        task_id = message.get('taskId')
        symbol = message.get('symbol')
        
        print(f'[{self.name}] 收到任务：{action} {symbol or ""}', file=sys.stderr)
        
        if action == 'fetch':
            data = self.fetch_financial_data(symbol)
            DATA_QUEUE.publish({
                'taskId': task_id,
                'action': 'fetch_result',
                'symbol': symbol,
                'data': data,
                'from_agent': self.agent_id
            })
        
        elif action == 'fetch_historical':
            data = self.fetch_historical_data(symbol, message.get('years', 5))
            DATA_QUEUE.publish({
                'taskId': task_id,
                'action': 'historical_result',
                'data': data,
                'from_agent': self.agent_id
            })
        
        elif action == 'ping':
            DATA_QUEUE.publish({
                'action': 'pong',
                'agentId': self.agent_id,
                'status': self.status,
                'api_stats': self.api_stats
            })
        
        elif action == 'shutdown':
            print(f'[{self.name}] 收到关闭指令', file=sys.stderr)
            self.running = False
    
    def fetch_financial_data(self, symbol: str) -> Dict:
        """
        获取财务数据
        
        自主决策：根据历史成功率选择 API
        """
        print(f'[{self.name}] 获取 {symbol} 的财务数据...', file=sys.stderr)
        start_time = time.time()
        
        # 自主选择 API
        api = self.select_best_api()
        print(f'[{self.name}] 选择 API: {api} (基于历史成功率)', file=sys.stderr)
        
        try:
            if api == 'alpha_vantage':
                data = self.fetch_via_mcp(symbol)
                success = data.get('success', False)
                
                # 降级策略
                if not success:
                    print(f'[{self.name}] MCP 调用失败，降级到 mock 数据', file=sys.stderr)
                    mock_data = self.get_mock_data(symbol)
                    if mock_data:
                        data = {'success': True, 'data': mock_data}
                        success = True
                        api = 'mock'
            else:
                data = self.get_mock_data(symbol)
                success = data is not None
                if success:
                    data = {'success': True, 'data': data}
            
            # 更新统计
            self._update_api_stats(api, success)
            
            elapsed = int((time.time() - start_time) * 1000)
            print(f'[{self.name}] 数据获取完成，耗时：{elapsed}ms, 成功：{success}', file=sys.stderr)
            
            return {
                'success': success,
                'data': data.get('data') if success else None,
                'source': api,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'elapsed_ms': elapsed
            }
            
        except Exception as e:
            self._update_api_stats(api, False)
            
            # 降级到模拟数据
            mock_data = self.get_mock_data(symbol)
            if mock_data:
                return {
                    'success': True,
                    'data': mock_data,
                    'source': 'mock_fallback',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                }
            
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def select_best_api(self) -> str:
        """
        自主选择最佳 API
        
        决策逻辑：
        1. 计算各 API 成功率
        2. 选择成功率最高的
        """
        best_api = 'alpha_vantage'
        best_score = 0
        
        for api, stats in self.api_stats.items():
            if stats['total'] == 0:
                # 没有历史数据，使用优先级
                rate = self.api_priority.get(api, 0) / 100
            else:
                # 有历史数据，使用成功率
                rate = stats['success'] / stats['total']
            
            if rate > best_score:
                best_score = rate
                best_api = api
        
        return best_api
    
    def _update_api_stats(self, api: str, success: bool):
        """更新 API 统计"""
        if api not in self.api_stats:
            self.api_stats[api] = {'success': 0, 'total': 0}
        
        self.api_stats[api]['total'] += 1
        if success:
            self.api_stats[api]['success'] += 1
        
        self._save_api_stats()
    
    def fetch_via_mcp(self, symbol: str) -> Dict:
        """通过 MCP Server 获取数据"""
        try:
            result = subprocess.run(
                ['mcporter', 'call', 'financial-report.get_financial_data', f'symbol={symbol}'],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                content = response.get('content', [{}])[0].get('text', '{}')
                data = json.loads(content)
                return data
            
            return {'success': False, 'error': 'MCP 调用失败'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_historical_data(self, symbol: str, years: int = 5) -> Dict:
        """获取历史数据（用于增长分析）"""
        print(f'[{self.name}] 获取 {symbol} 的{years}年历史数据...', file=sys.stderr)
        
        # 模拟历史数据
        mock_historical = {
            'AAPL': {
                'revenue_growth': [0.08, 0.12, 0.05, 0.33, 0.11],
                'net_income_growth': [0.05, 0.15, 0.08, 0.50, 0.15],
                'years': list(range(2021, 2026))
            },
            'MSFT': {
                'revenue_growth': [0.10, 0.14, 0.08, 0.18, 0.12],
                'net_income_growth': [0.12, 0.16, 0.10, 0.20, 0.14],
                'years': list(range(2021, 2026))
            }
        }
        
        data = mock_historical.get(symbol, {
            'revenue_growth': [0.10] * years,
            'net_income_growth': [0.12] * years,
            'years': list(range(2021, 2021 + years))
        })
        
        return {
            'success': True,
            'data': data,
            'source': 'mock_historical'
        }
    
    def get_mock_data(self, symbol: str) -> Optional[Dict]:
        """模拟数据（备用）"""
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
    
    def cleanup(self):
        """清理资源"""
        print(f'[{self.name}] 清理资源...', file=sys.stderr)
        self._save_api_stats()
    
    def process_message(self, message: Dict) -> bool:
        """处理消息并返回是否成功"""
        try:
            self.handle_message(message)
            self.stats['tasks_processed'] += 1
            self.stats['tasks_success'] += 1
            return True
        except Exception as e:
            print(f'[{self.name}] 处理失败：{e}', file=sys.stderr)
            self.stats['tasks_failed'] += 1
            return False


if __name__ == '__main__':
    agent = DataFetcherAgent()
    agent.run()
