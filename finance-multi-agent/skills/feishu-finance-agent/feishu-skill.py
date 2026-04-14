#!/usr/bin/env python3
"""
飞书股票查询 Skill

调用多 Agent 协作系统生成财报 One Pager 报告。
"""

import subprocess
import sys
import json
import os
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/mnt/c/Users/27901/Desktop/finance-multi-agent')
AGENTS_DIR = WORKSPACE / 'agents'
START_SCRIPT = AGENTS_DIR / 'start-agents.sh'

# 添加 agents 目录到 Python 路径
sys.path.insert(0, str(AGENTS_DIR))


def extract_symbol(message: str) -> str:
    """从消息中提取股票代码"""
    query = message.replace('@机器人', '').strip()
    
    company_map = {
        '苹果': 'AAPL', 'APPLE': 'AAPL',
        '微软': 'MSFT', 'MICROSOFT': 'MSFT',
        '谷歌': 'GOOGL', 'GOOGLE': 'GOOGL',
        '亚马逊': 'AMZN', 'AMAZON': 'AMZN',
        '特斯拉': 'TSLA', 'TESLA': 'TSLA',
        '英伟达': 'NVDA', 'NVIDIA': 'NVDA',
        'META': 'META', '脸书': 'META',
        '奈飞': 'NFLX', 'NETFLIX': 'NFLX',
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
    
    for name, symbol in company_map.items():
        if name in query.upper() or name in query:
            return symbol
    
    import re
    match = re.search(r'\b([A-Z]{1,5})\b', query.upper())
    if match:
        return match.group(1)
    
    return None


def ensure_agents_running():
    """确保 Agent 进程正在运行"""
    try:
        result = subprocess.run(
            [str(START_SCRIPT), 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'orchestrator' not in result.stdout or '未运行' in result.stdout:
            print(f'[Skill] 启动多 Agent 系统...', file=sys.stderr)
            subprocess.run(
                [str(START_SCRIPT), 'start'],
                capture_output=True,
                text=True,
                timeout=10
            )
            time.sleep(2)
    except Exception as e:
        print(f'[Skill] 检查 Agent 状态失败：{e}', file=sys.stderr)


def run_multi_agent_flow(symbol: str) -> dict:
    """运行多 Agent 协作流程（同步调用）"""
    try:
        result = subprocess.run(
            ['python3', str(AGENTS_DIR / 'orchestrator_daemon.py'), symbol],
            cwd=str(AGENTS_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        try:
            response = json.loads(result.stdout)
        except:
            return {
                'success': False,
                'error': '解析响应失败',
                'raw_output': result.stdout[:500]
            }
        
        if response.get('success'):
            report_data = response.get('result', {})
            report_content = report_data.get('content', '')
            quality_score = report_data.get('score', 100)
            total_time = response.get('duration_ms', 2500)
            
            return {
                'success': True,
                'symbol': symbol,
                'report': report_content,
                'qualityScore': quality_score,
                'totalTime': total_time
            }
        else:
            return {
                'success': False,
                'symbol': symbol,
                'error': response.get('error', '处理失败'),
                'totalTime': 0
            }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': '处理超时',
            'totalTime': 60000
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'totalTime': 0
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


def format_reply(response: dict) -> str:
    """格式化回复（纯文本）"""
    if not response.get('success'):
        return f'❌ 处理失败\n\n{response.get("error", "未知错误")}'
    
    quality_status = '✅' if response.get('qualityScore', 0) >= 80 else '⚠️'
    
    return f"""{quality_status} 质量评分：{response.get('qualityScore', 0)}/100
⏱️ 耗时：{response.get('totalTime', 0)}ms

{response.get('report', '')}

---
生成时间：{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}"""


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
    
    # 输出纯文本
    print(reply)


if __name__ == '__main__':
    main()
