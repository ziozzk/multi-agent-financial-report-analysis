#!/usr/bin/env python3
"""
Analyst Agent - 独立进程

职责：分析财务数据，生成投资亮点和风险
通信方式：stdin/stdout (JSON-RPC)
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, List

class AnalystAgent:
    def __init__(self):
        self.agent_id = f'analyst-{os.getpid()}'
        self.status = 'idle'
        
        print(f'[Analyst] Agent 已启动：{self.agent_id}', file=sys.stderr)
        self.listen()
    
    def listen(self):
        """监听标准输入"""
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
        financial_data = message.get('financialData', {})
        
        print(f'[Analyst] 收到任务：{action}', file=sys.stderr)
        
        if action == 'analyze':
            self.status = 'busy'
            analysis = self.analyze_data(financial_data)
            self.send_result({'taskId': task_id, 'action': 'analyze', 'data': analysis})
            self.status = 'idle'
        
        elif action == 'ping':
            self.send_result({'action': 'pong', 'agentId': self.agent_id, 'status': self.status})
        
        elif action == 'shutdown':
            print(f'[Analyst] 收到关闭指令', file=sys.stderr)
            sys.exit(0)
        
        else:
            self.send_error(f'未知动作：{action}')
    
    def analyze_data(self, financial_data: Dict) -> Dict:
        """分析财务数据"""
        print(f'[Analyst] 分析财务数据...', file=sys.stderr)
        
        # 生成投资亮点
        highlights = self.generate_highlights(financial_data)
        
        # 生成风险提示
        risks = self.generate_risks(financial_data)
        
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
            'valuationRating': self.rate_valuation(pe_ratio, profit_margin)
        }
        
        print(f'[Analyst] 分析完成', file=sys.stderr)
        
        return {
            'highlights': highlights,
            'risks': risks,
            'metrics': metrics,
            'analyzedAt': datetime.now().isoformat()
        }
    
    def generate_highlights(self, data: Dict) -> list:
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
        try:
            if 'T' in str(market_cap):
                highlights.append('市值超万亿，行业龙头地位稳固')
        except:
            pass
        
        # 默认亮点
        if not highlights:
            highlights = ['财务状况稳健', '市场竞争力强']
        
        return highlights[:3]
    
    def generate_risks(self, data: Dict) -> list:
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
    
    def send_result(self, result: Dict):
        """发送结果"""
        print(json.dumps({'type': 'result', **result}, ensure_ascii=False), flush=True)
    
    def send_error(self, message: str):
        """发送错误"""
        print(json.dumps({'type': 'error', 'message': message}), flush=True)

if __name__ == '__main__':
    agent = AnalystAgent()
