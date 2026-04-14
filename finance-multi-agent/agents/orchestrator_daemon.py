#!/usr/bin/env python3
"""
Orchestrator - 协调者（直接调用版本）

直接调用各个 Agent 的处理函数，不通过消息队列。
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict

# 导入各个 Agent 的类
from data_fetcher_agent import DataFetcherAgent
from analyst_agent import AnalystAgent
from reporter_agent import ReporterAgent
from reviewer_agent import ReviewerAgent


class Orchestrator:
    """协调者（直接调用）"""
    
    def run_task(self, symbol: str) -> Dict:
        """同步运行完整流程"""
        start_time = time.time()
        
        print(f'[Orchestrator] 开始任务：{symbol}', file=sys.stderr)
        
        # 步骤 1: DataFetcher 获取数据
        print(f'[Orchestrator] 调用 DataFetcher...', file=sys.stderr)
        fetcher = DataFetcherAgent.__new__(DataFetcherAgent)
        fetcher.name = 'DataFetcher'
        fetcher.api_stats = {'alpha_vantage': {'success': 0, 'total': 0}, 'mock': {'success': 0, 'total': 0}}
        fetcher.api_priority = {'alpha_vantage': 100, 'mock': 50}
        data_result = fetcher.fetch_financial_data(symbol)
        
        if not data_result.get('success'):
            return {'success': False, 'error': 'DataFetcher 失败'}
        
        # 步骤 2: Analyst 分析数据
        print(f'[Orchestrator] 调用 Analyst...', file=sys.stderr)
        analyst = AnalystAgent.__new__(AnalystAgent)
        analyst.name = 'Analyst'
        analyst.strategy_stats = {'conservative': {'success': 0, 'total': 0}, 'balanced': {'success': 0, 'total': 0}, 'aggressive': {'success': 0, 'total': 0}}
        analysis_result = analyst.analyze_data(data_result.get('data', {}))
        
        # 步骤 3: Reporter 生成报告
        print(f'[Orchestrator] 调用 Reporter...', file=sys.stderr)
        reporter = ReporterAgent.__new__(ReporterAgent)
        reporter.name = 'Reporter'
        reporter.revision_reasons = {}
        reporter.workspace = Path('/home/nio/.openclaw/workspace')
        report_result = reporter.generate_report(symbol, analysis_result)
        
        # 步骤 4: Reviewer 审核
        print(f'[Orchestrator] 调用 Reviewer...', file=sys.stderr)
        reviewer = ReviewerAgent.__new__(ReviewerAgent)
        reviewer.name = 'Reviewer'
        reviewer.quality_threshold = 70
        reviewer.review_history = []
        review_result = reviewer.review_report(report_result, version=1)
        
        duration = int((time.time() - start_time) * 1000)
        
        return {
            'success': True,
            'symbol': symbol,
            'result': {
                **report_result,
                'qualityCheck': review_result
            },
            'duration_ms': duration
        }


def main():
    """主函数 - 支持命令行调用"""
    if len(sys.argv) < 2:
        print('用法：python3 orchestrator_daemon.py <股票代码>', file=sys.stderr)
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    orchestrator = Orchestrator()
    result = orchestrator.run_task(symbol)
    
    # 输出 JSON 结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
