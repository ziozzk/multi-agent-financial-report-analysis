#!/usr/bin/env python3
"""
Reviewer Agent - 独立进程

职责：质量审核
通信方式：stdin/stdout (JSON-RPC)
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, List

class ReviewerAgent:
    def __init__(self):
        self.agent_id = f'reviewer-{os.getpid()}'
        self.status = 'idle'
        
        print(f'[Reviewer] Agent 已启动：{self.agent_id}', file=sys.stderr)
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
        report = message.get('report', {})
        
        print(f'[Reviewer] 收到任务：{action}', file=sys.stderr)
        
        if action == 'review':
            self.status = 'busy'
            review_result = self.review_report(report)
            self.send_result({'taskId': task_id, 'action': 'review', 'data': review_result})
            self.status = 'idle'
        
        elif action == 'ping':
            self.send_result({'action': 'pong', 'agentId': self.agent_id, 'status': self.status})
        
        elif action == 'shutdown':
            print(f'[Reviewer] 收到关闭指令', file=sys.stderr)
            sys.exit(0)
        
        else:
            self.send_error(f'未知动作：{action}')
    
    def review_report(self, report: Dict) -> Dict:
        """审核报告质量"""
        print(f'[Reviewer] 审核报告质量...', file=sys.stderr)
        
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
        
        passed = len(critical_failed) == 0
        
        print(f'[Reviewer] 审核完成：{"通过" if passed else "失败"} ({len(failed_checks)} 项未通过)', file=sys.stderr)
        
        return {
            'passed': passed,
            'score': self.calculate_score(checks),
            'checks': checks,
            'failedChecks': [c['name'] for c in failed_checks],
            'suggestions': self.generate_suggestions(failed_checks),
            'reviewedAt': datetime.now().isoformat()
        }
    
    def calculate_score(self, checks: list) -> int:
        """计算得分"""
        passed = sum(1 for c in checks if c['pass'])
        return round((passed / len(checks)) * 100)
    
    def generate_suggestions(self, failed_checks: list) -> list:
        """生成改进建议"""
        suggestions = []
        
        for check in failed_checks:
            if check['name'] == '包含业务概览':
                suggestions.append('添加公司业务描述和行业信息')
            elif check['name'] == '包含财务摘要':
                suggestions.append('添加营收、利润、市值等财务指标')
            elif check['name'] == '包含风险提示':
                suggestions.append('添加投资风险提示')
            elif check['name'] == '内容长度合理':
                suggestions.append('扩展报告内容，提供更多信息')
        
        return suggestions
    
    def send_result(self, result: Dict):
        """发送结果"""
        print(json.dumps({'type': 'result', **result}, ensure_ascii=False), flush=True)
    
    def send_error(self, message: str):
        """发送错误"""
        print(json.dumps({'type': 'error', 'message': message}), flush=True)

if __name__ == '__main__':
    agent = ReviewerAgent()
