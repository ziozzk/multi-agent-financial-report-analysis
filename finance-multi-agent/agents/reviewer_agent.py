#!/usr/bin/env python3
"""
Reviewer Agent - 质量审核

职责：
- 审核报告质量
- 动态调整质量阈值
- 要求 Reporter 返工

能力：
- 协商：要求 Reporter 返工
- 学习：根据历史调整阈值
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from message_queue import REPORT_QUEUE, REVIEW_QUEUE, NEGOTIATION_QUEUE, AgentRegistry
from base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """质量审核 Agent"""
    
    def __init__(self):
        super().__init__(
            name='Reviewer',
            agent_type='Reviewer',
            capabilities=['review_report', 'request_revision', 'approve_report']
        )
        
        # 质量阈值（可学习调整）
        self.quality_threshold = 70
        
        # 审核历史
        self.review_history = []
        self._load_stats()
    
    def _load_stats(self):
        """加载历史统计"""
        stats_file = Path('/tmp/agent-stats/reviewer_stats.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    self.quality_threshold = data.get('threshold', 70)
                    self.review_history = data.get('history', [])
            except:
                pass
    
    def _save_stats(self):
        """保存统计"""
        stats_file = Path('/tmp/agent-stats/reviewer_stats.json')
        stats_file.parent.mkdir(exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump({
                'threshold': self.quality_threshold,
                'history': self.review_history[-50:]  # 保留最近 50 条
            }, f, indent=2)
    
    def consume_message(self, timeout_ms: int = 5000):
        """从报告队列消费消息"""
        return REPORT_QUEUE.consume(timeout_ms=timeout_ms)
    
    def handle_message(self, message: Dict):
        """处理消息"""
        action = message.get('action')
        task_id = message.get('taskId')
        
        # 处理报告生成和返工后的报告
        if action in ['report_generated', 'report_revised']:
            report = message.get('data', {})
            version = message.get('version', 1)
            
            review_result = self.review_report(report, version)
            
            if review_result['action'] == 'approve':
                # 通过 - 发布最终结果到 REVIEW_QUEUE
                print(f'[{self.name}] 报告通过审核', file=sys.stderr)
                REVIEW_QUEUE.publish({
                    'taskId': task_id,
                    'action': 'review_passed',
                    'data': {
                        'report': report,
                        'qualityCheck': review_result
                    },
                    'from_agent': self.agent_id
                })
            else:
                # 要求返工 - 协商
                print(f'[{self.name}] 要求返工：{review_result["feedback"]}', file=sys.stderr)
                
                NEGOTIATION_QUEUE.publish({
                    'taskId': task_id,
                    'action': 'revise_report',
                    'from_agent': self.agent_id,
                    'to_agent': 'Reporter',
                    'feedback': review_result['feedback'],
                    'original_report': report
                })
        
        elif action == 'ping':
            REVIEW_QUEUE.publish({
                'action': 'pong',
                'agentId': self.agent_id,
                'status': self.status,
                'threshold': self.quality_threshold
            })
        
        elif action == 'shutdown':
            print(f'[{self.name}] 收到关闭指令', file=sys.stderr)
            self.running = False
    
    def review_report(self, report: Dict, version: int) -> Dict:
        """
        审核报告质量
        
        动态阈值：
        - 版本越高，阈值越低（避免无限返工）
        """
        print(f'[{self.name}] 审核报告 (version={version})...', file=sys.stderr)
        
        content = report.get('content', '')
        
        # 质量检查项
        checks = [
            {'name': '内容非空', 'pass': bool(content), 'critical': True},
            {'name': '包含业务概览', 'pass': '业务概览' in content, 'critical': True},
            {'name': '包含财务摘要', 'pass': '财务摘要' in content, 'critical': True},
            {'name': '包含投资亮点', 'pass': '投资亮点' in content or '亮点' in content, 'critical': False},
            {'name': '包含风险提示', 'pass': '风险' in content or '提示' in content, 'critical': True},
            {'name': '包含股价信息', 'pass': '$' in content or '股价' in content, 'critical': False},
            {'name': '内容长度合理', 'pass': len(content) > 200, 'critical': False}
        ]
        
        failed_checks = [c for c in checks if not c['pass']]
        critical_failed = [c for c in failed_checks if c['critical']]
        
        score = self.calculate_score(checks)
        
        # 动态阈值决策
        dynamic_threshold = max(50, self.quality_threshold - (version - 1) * 10)
        
        print(f'[{self.name}] 评分：{score}, 阈值：{dynamic_threshold}', file=sys.stderr)
        
        # 决策：通过还是返工？
        if score >= dynamic_threshold and len(critical_failed) == 0:
            # 通过
            self._update_review_stats(score, 'approved')
            
            return {
                'action': 'approve',
                'passed': True,
                'score': score,
                'checks': checks,
                'reviewedAt': datetime.now().isoformat()
            }
        else:
            # 要求返工
            self._update_review_stats(score, 'rejected')
            
            return {
                'action': 'reject',
                'passed': False,
                'score': score,
                'checks': checks,
                'feedback': self.generate_feedback(failed_checks),
                'reviewedAt': datetime.now().isoformat()
            }
    
    def calculate_score(self, checks: list) -> int:
        """计算得分"""
        passed = sum(1 for c in checks if c['pass'])
        return round((passed / len(checks)) * 100)
    
    def generate_feedback(self, failed_checks: list) -> list:
        """生成返工反馈"""
        feedback = []
        
        for check in failed_checks:
            if check['name'] == '包含业务概览':
                feedback.append('缺少业务概览')
            elif check['name'] == '包含财务摘要':
                feedback.append('缺少财务摘要')
            elif check['name'] == '包含风险提示':
                feedback.append('缺少风险提示')
            elif check['name'] == '内容长度合理':
                feedback.append('内容过短')
            elif check['name'] == '内容非空':
                feedback.append('报告内容为空')
        
        return feedback
    
    def _update_review_stats(self, score: int, decision: str):
        """更新审核统计"""
        try:
            self.review_history.append({
                'score': score,
                'decision': decision,
                'timestamp': time.time()
            })
            
            # 动态调整阈值
            recent = self.review_history[-10:]
            if len(recent) >= 5:
                avg_score = sum(r['score'] for r in recent) / len(recent)
                if avg_score > 85:
                    self.quality_threshold = min(90, self.quality_threshold + 2)
                elif avg_score < 60:
                    self.quality_threshold = max(50, self.quality_threshold - 2)
            
            self._save_stats()
        except Exception as e:
            print(f'[{self.name}] 更新统计失败：{e}', file=sys.stderr)
    
    def cleanup(self):
        """清理资源"""
        print(f'[{self.name}] 清理资源...', file=sys.stderr)
        self._save_stats()


if __name__ == '__main__':
    agent = ReviewerAgent()
    agent.run()
