#!/usr/bin/env python3
"""
Analyst Agent - 数据分析

职责：
- 分析财务数据
- 生成投资亮点和风险提示
- 自主判断数据是否足够

能力：
- 自主性：判断数据是否足够分析
- 协商：可请求 DataFetcher 补充数据
- 学习：记录分析策略效果
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from message_queue import DATA_QUEUE, ANALYSIS_QUEUE, NEGOTIATION_QUEUE, AgentRegistry
from base_agent import BaseAgent


class AnalystAgent(BaseAgent):
    """数据分析 Agent"""
    
    def __init__(self):
        super().__init__(
            name='Analyst',
            agent_type='Analyst',
            capabilities=['analyze_financial_data', 'request_more_data', 'generate_investment_thesis']
        )
        
        # 分析策略统计
        self.strategy_stats = {
            'conservative': {'success': 0, 'total': 0},
            'balanced': {'success': 0, 'total': 0},
            'aggressive': {'success': 0, 'total': 0}
        }
        
        self._load_strategy_stats()
    
    def _load_strategy_stats(self):
        """加载历史策略统计"""
        stats_file = Path('/tmp/agent-stats/analyst_strategy.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.strategy_stats = json.load(f)
            except:
                pass
    
    def _save_strategy_stats(self):
        """保存策略统计"""
        stats_file = Path('/tmp/agent-stats/analyst_strategy.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.strategy_stats, f, indent=2)
    
    def consume_message(self, timeout_ms: int = 5000):
        """从数据队列消费消息"""
        return DATA_QUEUE.consume(timeout_ms=timeout_ms)
    
    def handle_message(self, message: Dict):
        """处理消息"""
        action = message.get('action')
        task_id = message.get('taskId')
        
        if action == 'fetch_result':
            financial_data = message.get('data', {})
            
            # 自主决策：数据是否足够分析？
            if not self.has_enough_data(financial_data):
                # 协商：请求更多数据
                print(f'[{self.name}] 数据不足，请求更多数据...', file=sys.stderr)
                NEGOTIATION_QUEUE.publish({
                    'taskId': task_id,
                    'action': 'request_more_data',
                    'from_agent': self.agent_id,
                    'to_agent': 'DataFetcher',
                    'requirements': {
                        'need_historical': True,
                        'need_industry': True,
                        'reason': '数据不足以进行深度分析'
                    }
                })
                return
            
            # 数据足够，开始分析
            analysis = self.analyze_data(financial_data.get('data', {}))
            
            # 从原始消息获取 symbol
            symbol = message.get('symbol', 'UNKNOWN')
            
            ANALYSIS_QUEUE.publish({
                'taskId': task_id,
                'action': 'analysis_result',
                'symbol': symbol,
                'data': analysis,
                'from_agent': self.agent_id
            })
        
        elif action == 'more_data_result':
            # 收到补充数据，深度分析
            financial_data = message.get('data', {})
            analysis = self.analyze_data(financial_data.get('data', {}), deep=True)
            
            ANALYSIS_QUEUE.publish({
                'taskId': task_id,
                'action': 'analysis_result',
                'data': analysis,
                'from_agent': self.agent_id,
                'note': '基于补充数据的深度分析'
            })
        
        elif action == 'ping':
            ANALYSIS_QUEUE.publish({
                'action': 'pong',
                'agentId': self.agent_id,
                'status': self.status
            })
        
        elif action == 'shutdown':
            print(f'[{self.name}] 收到关闭指令', file=sys.stderr)
            self.running = False
    
    def has_enough_data(self, financial_data: Dict) -> bool:
        """
        自主决策：判断数据是否足够分析
        
        决策标准：
        - 必须有基础财务指标（PE、利润率）
        - 必须有市值和营收
        """
        data = financial_data.get('data', {})
        
        required_fields = ['peRatio', 'profitMargin', 'marketCap', 'revenue']
        
        for field in required_fields:
            if not data.get(field):
                return False
        
        return True
    
    def analyze_data(self, financial_data: Dict, deep: bool = False) -> Dict:
        """
        分析财务数据
        
        自主决策：选择分析策略
        """
        print(f'[{self.name}] 分析财务数据 (deep={deep})...', file=sys.stderr)
        
        # 自主选择分析策略
        strategy = self.select_strategy(financial_data, deep)
        print(f'[{self.name}] 选择分析策略：{strategy}', file=sys.stderr)
        
        # 更新统计
        self.strategy_stats[strategy]['total'] += 1
        
        # 生成分析
        highlights = self.generate_highlights(financial_data, strategy)
        risks = self.generate_risks(financial_data, strategy)
        
        # 财务指标分析
        pe_ratio = financial_data.get('peRatio', 0) or 0
        profit_margin = financial_data.get('profitMargin', 0) or 0
        
        metrics = {
            'peRatio': pe_ratio,
            'profitMargin': profit_margin,
            'grossMargin': financial_data.get('grossMargin', 0) or 0,
            'marketCap': financial_data.get('marketCap', 'N/A'),
            'revenue': financial_data.get('revenue', 'N/A'),
            'currentPrice': financial_data.get('currentPrice', 0),
            'peRating': self.rate_pe(pe_ratio),
            'profitabilityRating': self.rate_profitability(profit_margin),
            'valuationRating': self.rate_valuation(pe_ratio, profit_margin),
            'strategy_used': strategy
        }
        
        # 记录策略成功
        self.strategy_stats[strategy]['success'] += 1
        self._save_strategy_stats()
        
        print(f'[{self.name}] 分析完成', file=sys.stderr)
        
        return {
            'highlights': highlights,
            'risks': risks,
            'metrics': metrics,
            'analyzedAt': datetime.now().isoformat(),
            'deep_analysis': deep
        }
    
    def select_strategy(self, financial_data: Dict, deep: bool) -> str:
        """
        自主选择分析策略
        
        决策逻辑：
        - 深度分析请求 → aggressive
        - 数据丰富 → balanced
        - 数据有限 → conservative
        """
        if deep:
            return 'aggressive'
        
        data_count = sum(1 for v in financial_data.values() if v)
        
        if data_count > 10:
            return 'balanced'
        else:
            return 'conservative'
    
    def generate_highlights(self, data: Dict, strategy: str) -> List[str]:
        """生成投资亮点"""
        sector = (data.get('sector') or '').upper()
        profit_margin = data.get('profitMargin', 0) or 0
        pe_ratio = data.get('peRatio', 0) or 0
        
        highlights = []
        
        # 基于利润率
        if profit_margin > 30:
            highlights.append('净利率超过 30%，盈利能力极强')
        elif profit_margin > 20:
            highlights.append('净利率超过 20%，盈利能力优秀')
        
        # 基于行业
        if 'TECHNOLOGY' in sector:
            highlights.append('科技行业，增长潜力大')
        elif 'HEALTHCARE' in sector:
            highlights.append('医疗行业，防御性强')
        
        # 基于市值
        market_cap = data.get('marketCap', '0')
        if 'T' in str(market_cap):
            highlights.append('市值超万亿，行业龙头地位稳固')
        
        # 激进策略添加更多亮点
        if strategy == 'aggressive':
            if pe_ratio < 30:
                highlights.append('估值合理，有上升空间')
        
        # 默认亮点
        if not highlights:
            highlights = ['财务状况稳健', '市场竞争力强']
        
        return highlights[:3]
    
    def generate_risks(self, data: Dict, strategy: str) -> List[str]:
        """生成风险提示"""
        pe_ratio = data.get('peRatio', 0) or 0
        sector = (data.get('sector') or '').upper()
        
        risks = []
        
        # 高估值风险
        if pe_ratio > 50:
            risks.append('PE 比率超过 50，估值较高，存在回调风险')
        elif pe_ratio > 30:
            risks.append('PE 比率超过 30，估值偏高')
        
        # 行业风险
        if 'TECHNOLOGY' in sector:
            risks.append('科技行业波动性大，受政策影响')
        
        # 保守策略添加更多风险
        if strategy == 'conservative':
            risks.append('宏观经济不确定性')
        
        # 默认风险
        if not risks:
            risks = ['市场竞争加剧', '宏观经济不确定性']
        
        return risks[:3]
    
    def rate_pe(self, pe: float) -> str:
        """PE 评级"""
        if not pe:
            return 'N/A'
        if pe < 15:
            return '低估'
        if pe < 25:
            return '合理'
        if pe < 40:
            return '偏高'
        return '高估'
    
    def rate_profitability(self, margin: float) -> str:
        """盈利能力评级"""
        if not margin:
            return 'N/A'
        if margin > 30:
            return '优秀'
        if margin > 20:
            return '良好'
        if margin > 10:
            return '一般'
        return '较差'
    
    def rate_valuation(self, pe: float, margin: float) -> str:
        """估值评级"""
        if not pe or not margin:
            return 'N/A'
        peg = pe / (margin * 100)
        if peg < 1:
            return '低估'
        if peg < 2:
            return '合理'
        return '高估'
    
    def cleanup(self):
        """清理资源"""
        print(f'[{self.name}] 清理资源...', file=sys.stderr)
        self._save_strategy_stats()
    
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
    agent = AnalystAgent()
    agent.run()
