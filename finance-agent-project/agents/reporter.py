#!/usr/bin/env python3
"""
Reporter Agent - 独立进程

职责：格式化 One Pager 报告
通信方式：stdin/stdout (JSON-RPC)
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from typing import Dict

class ReporterAgent:
    def __init__(self):
        self.agent_id = f'reporter-{os.getpid()}'
        self.status = 'idle'
        self.workspace = '/home/nio/.openclaw/workspace'
        
        print(f'[Reporter] Agent 已启动：{self.agent_id}', file=sys.stderr)
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
        symbol = message.get('symbol')
        financial_data = message.get('financialData', {})
        analysis = message.get('analysis', {})
        
        print(f'[Reporter] 收到任务：{action} {symbol or ""}', file=sys.stderr)
        
        if action == 'generate':
            self.status = 'busy'
            report = self.generate_report(symbol, financial_data, analysis)
            self.send_result({'taskId': task_id, 'action': 'generate', 'data': report})
            self.status = 'idle'
        
        elif action == 'ping':
            self.send_result({'action': 'pong', 'agentId': self.agent_id, 'status': self.status})
        
        elif action == 'shutdown':
            print(f'[Reporter] 收到关闭指令', file=sys.stderr)
            sys.exit(0)
        
        else:
            self.send_error(f'未知动作：{action}')
    
    def generate_report(self, symbol: str, financial_data: Dict, analysis: Dict) -> Dict:
        """生成 One Pager 报告"""
        print(f'[Reporter] 生成 One Pager 报告...', file=sys.stderr)
        
        try:
            result = subprocess.run(
                ['mcporter', 'call', 'financial-report.generate_onepager', f'symbol={symbol}'],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f'[Reporter] 报告生成成功', file=sys.stderr)
            
            return {
                'format': 'markdown',
                'content': result.stdout,
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'dataUsed': {
                    'hasFinancialData': bool(financial_data),
                    'hasAnalysis': bool(analysis)
                }
            }
        
        except subprocess.TimeoutExpired:
            print(f'[Reporter] 错误：超时', file=sys.stderr)
            return {
                'format': 'markdown',
                'content': f'# 报告生成失败\n\n错误：超时',
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'error': '超时'
            }
        
        except Exception as e:
            print(f'[Reporter] 错误：{e}', file=sys.stderr)
            return {
                'format': 'markdown',
                'content': f'# 报告生成失败\n\n错误：{str(e)}',
                'symbol': symbol,
                'generatedAt': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def send_result(self, result: Dict):
        """发送结果"""
        print(json.dumps({'type': 'result', **result}, ensure_ascii=False), flush=True)
    
    def send_error(self, message: str):
        """发送错误"""
        print(json.dumps({'type': 'error', 'message': message}), flush=True)

if __name__ == '__main__':
    agent = ReporterAgent()
