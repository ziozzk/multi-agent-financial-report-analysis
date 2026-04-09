#!/usr/bin/env python3
"""
飞书股票查询处理器 - OpenClaw Skill 执行器

当 OpenClaw 收到飞书股票查询消息时，调用此脚本处理。
"""

import subprocess
import sys
import json
import os
from pathlib import Path

# 项目根目录
WORKSPACE = '/home/nio/.openclaw/workspace'
FEISHU_BRIDGE = Path(WORKSPACE) / 'agents' / 'feishu-bridge.py'

def extract_stock_query(message: str) -> str:
    """从飞书消息中提取股票查询"""
    # 移除 @机器人 提及
    query = message.replace('@机器人', '').strip()
    
    # 移除常见前缀
    for prefix in ['生成', '查询', '分析', '查看', '来一个', '我要']:
        if query.startswith(prefix):
            query = query[len(prefix):].strip()
    
    # 移除常见后缀
    for suffix in ['财报', '报告', 'One Pager', 'onepager', '分析', '数据']:
        if query.endswith(suffix):
            query = query[:-len(suffix)].strip()
    
    return query.strip()

def is_stock_query(message: str) -> bool:
    """判断是否是股票查询消息"""
    # 检查是否包含 @机器人
    if '@机器人' not in message:
        return False
    
    # 提取查询内容
    query = extract_stock_query(message)
    if not query:
        return False
    
    # 检查是否是股票代码或公司名称
    # 股票代码：1-5 个大写字母
    import re
    if re.match(r'^[A-Z]{1,5}$', query.upper()):
        return True
    
    # 常见公司名称关键词
    company_keywords = [
        '苹果', '微软', '谷歌', '亚马逊', '特斯拉', '英伟达',
        'meta', '脸书', '奈飞', 'Netflix', 'AMD', '英特尔',
        '比亚迪', '美团', '阿里巴巴', '百度', '京东', '拼多多',
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'
    ]
    
    query_upper = query.upper()
    for keyword in company_keywords:
        if keyword in query_upper or keyword in query:
            return True
    
    return False

def process_feishu_stock_query(message: str) -> dict:
    """处理飞书股票查询"""
    query = extract_stock_query(message)
    
    if not query:
        return {
            'success': False,
            'error': '无法识别查询内容',
            'message': '请提供股票代码 (如 AAPL) 或公司名称 (如 苹果)'
        }
    
    try:
        # 调用 Feishu Bridge
        result = subprocess.run(
            ['python3', str(FEISHU_BRIDGE), query],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 解析结果
        try:
            response = json.loads(result.stdout)
        except:
            response = {
                'success': False,
                'error': '解析响应失败',
                'raw_output': result.stdout[:500]
            }
        
        return response
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': '处理超时',
            'message': '查询处理时间超过 60 秒，请稍后重试'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': '处理失败，请稍后重试'
        }

def format_feishu_reply(response: dict) -> dict:
    """格式化飞书回复"""
    if not response.get('success'):
        return {
            'msg_type': 'text',
            'content': {
                'text': f'❌ 处理失败\n\n{response.get("error", "未知错误")}\n\n{response.get("message", "")}'
            }
        }
    
    report = response.get('report', {})
    quality_check = report.get('qualityCheck', {})
    
    # 质量状态
    quality_status = '✅' if quality_check.get('passed') else '⚠️'
    quality_score = quality_check.get('score', 'N/A')
    
    # 报告内容
    content = report.get('content', '报告生成失败')
    
    # 查询的股票
    query = response.get('query', '股票')
    
    # 飞书富文本格式
    return {
        'msg_type': 'post',
        'content': {
            'post': {
                'zh_cn': {
                    'title': f'📊 {query} 财报 One Pager',
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
                                'text': f'\n---\n⏱️ 生成时间：{__import__("datetime").datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'
                            }
                        ]
                    ]
                }
            }
        }
    }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': '缺少消息参数',
            'usage': 'python3 feishu-stock-processor.py "<消息内容>"'
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 获取消息内容
    message = ' '.join(sys.argv[1:])
    
    # 判断是否是股票查询
    if not is_stock_query(message):
        print(json.dumps({
            'success': False,
            'error': '不是股票查询消息',
            'message': '请确保消息包含 @机器人 和股票代码/公司名称'
        }, ensure_ascii=False))
        sys.exit(0)
    
    # 处理查询
    response = process_feishu_stock_query(message)
    
    # 格式化回复
    reply = format_feishu_reply(response)
    
    # 输出结果
    output = {
        'success': response.get('success', False),
        'query': response.get('query'),
        'reply': reply,
        'metrics': response.get('metrics')
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
