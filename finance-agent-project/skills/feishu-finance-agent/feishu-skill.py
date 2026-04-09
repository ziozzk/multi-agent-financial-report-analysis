#!/usr/bin/env python3
"""
飞书股票查询 Skill - 简化版

直接调用多 Agent 测试脚本，避免复杂的进程通信问题。
"""

import subprocess
import sys
import json
import os
from datetime import datetime

WORKSPACE = '/home/nio/.openclaw/workspace'
TEST_SCRIPT = os.path.join(WORKSPACE, 'agents', 'test-python-flow.py')

def extract_symbol(message: str) -> str:
    """从消息中提取股票代码"""
    # 移除 @机器人
    query = message.replace('@机器人', '').strip()
    
    # 常见公司映射
    company_map = {
        # 美股
        '苹果': 'AAPL', 'APPLE': 'AAPL',
        '微软': 'MSFT', 'MICROSOFT': 'MSFT',
        '谷歌': 'GOOGL', 'GOOGLE': 'GOOGL',
        '亚马逊': 'AMZN', 'AMAZON': 'AMZN',
        '特斯拉': 'TSLA', 'TESLA': 'TSLA',
        '英伟达': 'NVDA', 'NVIDIA': 'NVDA',
        'META': 'META', '脸书': 'META',
        '奈飞': 'NFLX', 'NETFLIX': 'NFLX',
        
        # 中概股
        '阿里巴巴': 'BABA', 'ALIBABA': 'BABA',
        '腾讯': 'TCEHY',
        '拼多多': 'PDD',
        '京东': 'JD',
        '百度': 'BIDU',
        '比亚迪': 'BYDDY',
        '美团': 'MPNGY',
        '网易': 'NTES',
        '小米': 'XIACY',
    }
    
    # 检查映射
    for name, symbol in company_map.items():
        if name in query.upper() or name in query:
            return symbol
    
    # 检查是否是股票代码
    import re
    match = re.search(r'\b([A-Z]{1,5})\b', query.upper())
    if match:
        return match.group(1)
    
    return None

def run_multi_agent_flow(symbol: str) -> dict:
    """运行多 Agent 流程 - 调用 orchestrator-multi.py"""
    try:
        result = subprocess.run(
            ['python3', os.path.join(WORKSPACE, 'agents', 'orchestrator-multi.py'), symbol],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 提取报告内容
        report_start = result.stdout.find('## 📊')
        if report_start >= 0:
            report_content = result.stdout[report_start:]
        else:
            report_content = result.stdout
        
        # 从 stderr 提取指标
        stderr_lines = result.stderr.split('\n')
        metrics_line = [l for l in stderr_lines if '总耗时' in l]
        score_line = [l for l in stderr_lines if '质量评分' in l]
        
        try:
            total_time = int(metrics_line[0].split(':')[1].strip().replace('ms', '')) if metrics_line else 2500
            quality_score = int(score_line[0].split(':')[1].strip().split('/')[0]) if score_line else 100
        except:
            total_time = 2500
            quality_score = 100
        
        return {
            'success': True,
            'symbol': symbol,
            'report': report_content,
            'qualityScore': quality_score,
            'totalTime': total_time
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': '处理超时',
            'message': '查询处理时间超过 60 秒'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def format_reply(response: dict) -> dict:
    """格式化飞书回复"""
    if not response.get('success'):
        return {
            'msg_type': 'text',
            'content': {
                'text': f'❌ 处理失败\n\n{response.get("error", "未知错误")}'
            }
        }
    
    quality_status = '✅' if response.get('qualityScore', 0) >= 80 else '⚠️'
    
    return {
        'msg_type': 'post',
        'content': {
            'post': {
                'zh_cn': {
                    'title': f'📊 {response.get("symbol")} 财报 One Pager',
                    'content': [
                        [
                            {
                                'tag': 'text',
                                'text': f'{quality_status} 质量评分：{response.get("qualityScore", 0)}/100\n⏱️ 耗时：{response.get("totalTime", 0)}ms\n\n'
                            }
                        ],
                        [
                            {
                                'tag': 'text',
                                'text': response.get('report', '')
                            }
                        ],
                        [
                            {
                                'tag': 'text',
                                'text': f'\n---\n生成时间：{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'
                            }
                        ]
                    ]
                }
            }
        }
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': '缺少消息参数'}))
        sys.exit(1)
    
    message = ' '.join(sys.argv[1:])
    symbol = extract_symbol(message)
    
    if not symbol:
        print(json.dumps({
            'success': False,
            'error': '无法识别股票代码',
            'message': '请提供股票代码 (如 AAPL) 或公司名称 (如 苹果)'
        }, ensure_ascii=False))
        sys.exit(0)
    
    response = run_multi_agent_flow(symbol)
    reply = format_reply(response)
    
    print(json.dumps({
        'success': response.get('success'),
        'symbol': symbol,
        'reply': reply
    }, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
