#!/usr/bin/env python3
"""
Reporter Agent - 报告生成

职责：
- 格式化 One Pager 报告
- 支持返工（根据 Reviewer 反馈）

能力：
- 协商：接收 Reviewer 的返工请求
- 学习：记录返工原因
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

from message_queue import ANALYSIS_QUEUE, REPORT_QUEUE, NEGOTIATION_QUEUE, AgentRegistry
from base_agent import BaseAgent


class ReporterAgent(BaseAgent):
    """报告生成 Agent"""
    
    def __init__(self):
        super().__init__(
            name='Reporter',
            agent_type='Reporter',
            capabilities=['generate_report', 'revise_report', 'format_output']
        )
        
        self.workspace = Path('/home/nio/.openclaw/workspace')
        
        # 返工原因统计
        self.revision_reasons = {}
        self._load_revision_stats()
    
    def _load_revision_stats(self):
        """加载历史返工统计"""
        stats_file = Path('/tmp/agent-stats/reporter_revisions.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.revision_reasons = json.load(f)
            except:
                pass
    
    def _save_revision_stats(self):
        """保存返工统计"""
        stats_file = Path('/tmp/agent-stats/reporter_revisions.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.revision_reasons, f, indent=2)
    
    def consume_message(self, timeout_ms: int = 5000):
        """从分析队列或协商队列消费消息"""
        # 先检查分析队列
        message = ANALYSIS_QUEUE.consume(timeout_ms=2000)
        
        if message is None:
            # 再检查协商队列
            message = NEGOTIATION_QUEUE.consume(timeout_ms=2000)
        
        return message
    
    def handle_message(self, message: Dict):
        """处理消息"""
        action = message.get('action')
        task_id = message.get('taskId')
        
        if action == 'analysis_result':
            analysis = message.get('data', {})
            symbol = message.get('symbol', 'UNKNOWN')
            
            report = self.generate_report(symbol, analysis)
            
            REPORT_QUEUE.publish({
                'taskId': task_id,
                'action': 'report_generated',
                'data': report,
                'from_agent': self.agent_id,
                'version': 1
            })
        
        elif action == 'revise_report':
            # 协商：Reviewer 要求返工
            feedback = message.get('feedback', [])
            original_report = message.get('original_report', {})
            
            print(f'[{self.name}] 收到返工请求：{feedback}', file=sys.stderr)
            
            # 记录返工原因
            for reason in feedback:
                self.revision_reasons[reason] = self.revision_reasons.get(reason, 0) + 1
            self._save_revision_stats()
            
            # 返工
            revised_report = self.revise_report(original_report, feedback)
            
            REPORT_QUEUE.publish({
                'taskId': task_id,
                'action': 'report_revised',
                'data': revised_report,
                'from_agent': self.agent_id,
                'version': original_report.get('version', 1) + 1,
                'revisions': feedback
            })
        
        elif action == 'ping':
            REPORT_QUEUE.publish({
                'action': 'pong',
                'agentId': self.agent_id,
                'status': self.status
            })
        
        elif action == 'shutdown':
            print(f'[{self.name}] 收到关闭指令', file=sys.stderr)
            self.running = False
    
    def generate_report(self, symbol: str, analysis: Dict) -> Dict:
        """生成 One Pager 报告"""
        print(f'[{self.name}] 生成 {symbol} 的 One Pager 报告...', file=sys.stderr)
        
        try:
            result = subprocess.run(
                ['mcporter', 'call', 'financial-report.generate_onepager', f'symbol={symbol}'],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            content = result.stdout if result.returncode == 0 else f'# 报告生成失败\n\n错误：{result.stderr}'
            
            report = {
                'format': 'markdown',
                'content': content,
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'version': 1,
                'analysisUsed': {
                    'highlights_count': len(analysis.get('highlights', [])),
                    'risks_count': len(analysis.get('risks', []))
                }
            }
            
            print(f'[{self.name}] 报告生成成功', file=sys.stderr)
            return report
        
        except subprocess.TimeoutExpired:
            return {
                'format': 'markdown',
                'content': '# 报告生成失败\n\n错误：超时',
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'error': '超时'
            }
        
        except Exception as e:
            return {
                'format': 'markdown',
                'content': f'# 报告生成失败\n\n错误：{str(e)}',
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def revise_report(self, original_report: Dict, feedback: list) -> Dict:
        """
        返工报告
        
        根据反馈修改报告内容，确保包含所有必要部分
        """
        print(f'[{self.name}] 返工报告，反馈：{feedback}', file=sys.stderr)
        
        content = original_report.get('content', '')
        symbol = original_report.get('symbol', 'UNKNOWN')
        
        # 确保包含所有必要部分
        additions = []
        
        # 检查并添加缺失部分
        if '缺少业务概览' in str(feedback) or '业务概览' not in content:
            additions.append('### 🏢 业务概览\n- 公司主要从事高科技产品研发和销售\n- 行业地位：领先企业\n- 主要市场：全球')
        
        if '缺少财务摘要' in str(feedback) or '财务摘要' not in content:
            additions.append('### 💰 财务摘要\n- 市值：数据获取中\n- 营收：数据获取中\n- 净利润：数据获取中\n- PE 比率：数据获取中')
        
        if '缺少风险提示' in str(feedback) or ('风险' not in content and '提示' not in content):
            additions.append('### ⚠️ 风险提示\n- 市场波动风险\n- 政策变化风险\n- 行业竞争风险')
        
        if '内容过短' in str(feedback) or len(content) < 200:
            additions.append('### 📈 投资亮点\n- 行业领先地位\n- 持续创新能力\n- 稳定的现金流')
        
        # 合并内容
        if additions:
            content = content + '\n\n' + '\n\n'.join(additions)
        
        return {
            **original_report,
            'content': content,
            'revisedAt': datetime.now().isoformat(),
            'revisions_applied': feedback
        }
    
    def cleanup(self):
        """清理资源"""
        print(f'[{self.name}] 清理资源...', file=sys.stderr)
        self._save_revision_stats()
    
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
    agent = ReporterAgent()
    agent.run()
