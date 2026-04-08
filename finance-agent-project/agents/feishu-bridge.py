#!/usr/bin/env python3
"""
飞书消息处理器 - 连接飞书和多 Agent 协作系统

职责:
- 监听飞书消息 (通过 OpenClaw)
- 转发到 Orchestrator Agent
- 将结果回复到飞书
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict

class FeishuAgentBridge:
    def __init__(self):
        self.orchestrator_path = Path(__file__).parent / 'orchestrator-multi.py'
        print(f'[FeishuBridge] 初始化完成，Orchestrator 路径：{self.orchestrator_path}', file=sys.stderr)
    
    def handle_message(self, message: str) -> Dict:
        """处理飞书消息"""
        print(f'[FeishuBridge] 收到飞书消息：{message}', file=sys.stderr)
        
        # 提取股票代码或公司名称
        query = self.extract_query(message)
        if not query:
            return {
                'success': False,
                'error': '无法识别股票代码',
                'message': '请提供股票代码 (如 AAPL, MSFT) 或公司名称 (如 苹果，微软)'
            }
        
        print(f'[FeishuBridge] 提取查询：{query}', file=sys.stderr)
        
        try:
            # 调用 Orchestrator Agent
            result = self.call_orchestrator(query)
            
            print(f'[FeishuBridge] 处理完成', file=sys.stderr)
            
            return {
                'success': True,
                'query': query,
                'report': result.get('report'),
                'qualityCheck': result.get('report', {}).get('qualityCheck'),
                'metrics': result.get('metrics')
            }
        
        except Exception as e:
            print(f'[FeishuBridge] 错误：{e}', file=sys.stderr)
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def extract_query(self, message: str) -> str:
        """从飞书消息中提取查询"""
        # 移除 @机器人 提及
        query = message.replace('@机器人', '').strip()
        
        # 移除常见前缀
        for prefix in ['生成', '查询', '分析', '查看']:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        
        # 移除常见后缀
        for suffix in ['财报', '报告', 'One Pager', 'onepager']:
            if query.endswith(suffix):
                query = query[:-len(suffix)].strip()
        
        return query.strip() if query.strip() else None
    
    def call_orchestrator(self, query: str) -> Dict:
        """调用 Orchestrator Agent"""
        print(f'[FeishuBridge] 调用 Orchestrator: {query}', file=sys.stderr)
        
        result = subprocess.run(
            ['python3', str(self.orchestrator_path), query],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 输出 Orchestrator 日志
        if result.stderr:
            print(f'[Orchestrator] {result.stderr}', file=sys.stderr)
        
        try:
            return json.loads(result.stdout)
        except:
            return {
                'success': True,
                'report': {
                    'content': result.stdout,
                    'format': 'text'
                }
            }
    
    def format_feishu_reply(self, result: Dict) -> Dict:
        """格式化飞书回复"""
        if not result.get('success'):
            return {
                'msg_type': 'text',
                'content': {
                    'text': f'❌ 处理失败\n\n{result.get("error", "未知错误")}'
                }
            }
        
        report = result.get('report', {})
        quality_check = report.get('qualityCheck', {})
        
        # 检查质量
        quality_status = '✅' if quality_check.get('passed') else '⚠️'
        quality_score = quality_check.get('score', 'N/A')
        
        # 提取报告内容
        content = report.get('content', '报告生成失败')
        
        # 飞书富文本格式
        return {
            'msg_type': 'post',
            'content': {
                'post': {
                    'zh_cn': {
                        'title': f'📊 {result.get("query", "")} 财报 One Pager',
                        'content': [
                            [
                                {
                                    'tag': 'text',
                                    'text': f'{quality_status} 质量评分：{quality_score}/100\n\n'
                                }
                            ],
                            [
                                {
                                    'tag': 'text',
                                    'text': content
                                }
                            ],
                            [
                                {
                                    'tag': 'text',
                                    'text': f'\n---\n⏱️ 生成时间：{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'
                                }
                            ]
                        ]
                    }
                }
            }
        }

def main():
    bridge = FeishuAgentBridge()
    
    # 获取用户输入
    message = ' '.join(sys.argv[1:])
    if not message:
        print('用法：python feishu-bridge.py <飞书消息>', file=sys.stderr)
        print('示例：python feishu-bridge.py "@机器人 AAPL"', file=sys.stderr)
        sys.exit(1)
    
    result = bridge.handle_message(message)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化飞书回复
    reply = bridge.format_feishu_reply(result)
    print(f'\n=== 飞书回复格式 ===', file=sys.stderr)
    print(json.dumps(reply, ensure_ascii=False, indent=2), file=sys.stderr)

if __name__ == '__main__':
    main()
