#!/usr/bin/env python3
"""
Orchestrator Agent - 多 Agent 协作协调者（独立进程版本）

职责:
- 解析用户意图
- 启动/管理子 Agent 进程
- 分发任务
- 汇总结果
"""

import subprocess
import sys
import json
import time
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Agent 配置
AGENT_CONFIGS = {
    'dataFetcher': {
        'file': 'data-fetcher.py',
        'name': 'DataFetcher'
    },
    'analyst': {
        'file': 'analyst.py',
        'name': 'Analyst'
    },
    'reporter': {
        'file': 'reporter.py',
        'name': 'Reporter'
    },
    'reviewer': {
        'file': 'reviewer.py',
        'name': 'Reviewer'
    }
}

class AgentProcess:
    """Agent 进程封装"""
    def __init__(self, key: str, name: str, process: subprocess.Popen):
        self.key = key
        self.name = name
        self.process = process
        self.status = 'starting'
        self.pending_responses = {}

class OrchestratorAgent:
    def __init__(self):
        self.agent_id = f'orchestrator-{os.getpid()}'
        self.agents: Dict[str, AgentProcess] = {}
        self.tasks = {}
        self.task_counter = 0
        self.script_dir = Path(__file__).parent
        
        print(f'[Orchestrator] Agent 已启动：{self.agent_id}', file=sys.stderr)
    
    def start_agents(self):
        """启动所有子 Agent 进程"""
        print(f'[Orchestrator] 启动子 Agent 进程...', file=sys.stderr)
        
        for key, config in AGENT_CONFIGS.items():
            self.spawn_agent(key, config)
        
        print(f'[Orchestrator] 所有子 Agent 已启动', file=sys.stderr)
    
    def spawn_agent(self, key: str, config: Dict):
        """生成单个 Agent 进程"""
        try:
            agent_file = self.script_dir / config['file']
            
            child = subprocess.Popen(
                ['python3', str(agent_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            agent = AgentProcess(key, config['name'], child)
            
            # 等待 Agent 就绪
            time.sleep(0.5)
            agent.status = 'ready'
            self.agents[key] = agent
            
            print(f'[{config["name"]}] 就绪', file=sys.stderr)
            
        except Exception as e:
            print(f'[{config["name"]}] 启动失败：{e}', file=sys.stderr)
    
    def send_to_agent(self, agent_key: str, message: Dict, timeout: int = 30) -> Optional[Dict]:
        """发送消息到 Agent"""
        agent = self.agents.get(agent_key)
        if not agent or agent.status != 'ready':
            raise Exception(f'Agent {agent_key} 未就绪')
        
        task_id = message.get('taskId') or f'task_{int(time.time() * 1000)}_{self.task_counter}'
        message['taskId'] = task_id
        self.task_counter += 1
        
        # 发送消息
        agent.process.stdin.write(json.dumps(message) + '\n')
        agent.process.stdin.flush()
        
        # 等待响应
        start_time = time.time()
        while time.time() - start_time < timeout:
            if agent.process.poll() is not None:
                # 进程已退出
                raise Exception(f'Agent {agent_key} 进程已退出')
            
            # 读取一行响应
            try:
                line = agent.process.stdout.readline()
                if line:
                    response = json.loads(line.strip())
                    if response.get('taskId') == task_id:
                        return response
            except:
                continue
            
            time.sleep(0.1)
        
        raise Exception(f'Agent {agent_key} 响应超时')
    
    def handle_request(self, user_input: str) -> Dict:
        """处理用户请求"""
        print(f'[Orchestrator] 收到请求：{user_input}', file=sys.stderr)
        
        task_id = f'task_{int(time.time() * 1000)}'
        start_time = time.time()
        
        try:
            # 步骤 1: 解析股票代码
            symbol = self.extract_symbol(user_input)
            if not symbol:
                raise Exception('无法识别股票代码')
            
            print(f'[Orchestrator] 提取到股票代码：{symbol}', file=sys.stderr)
            
            # 步骤 2: DataFetcher 获取数据
            print(f'[Orchestrator] 调用 DataFetcher...', file=sys.stderr)
            fetch_result = self.send_to_agent('dataFetcher', {
                'action': 'fetch',
                'symbol': symbol
            })
            financial_data = fetch_result.get('data', {}).get('data')
            
            # 步骤 3: Analyst 分析数据
            print(f'[Orchestrator] 调用 Analyst...', file=sys.stderr)
            analysis_result = self.send_to_agent('analyst', {
                'action': 'analyze',
                'financialData': financial_data or {}
            })
            analysis = analysis_result.get('data')
            
            # 步骤 4: Reporter 生成报告
            print(f'[Orchestrator] 调用 Reporter...', file=sys.stderr)
            report_result = self.send_to_agent('reporter', {
                'action': 'generate',
                'symbol': symbol,
                'financialData': financial_data or {},
                'analysis': analysis or {}
            })
            report = report_result.get('data')
            
            # 步骤 5: Reviewer 审核
            print(f'[Orchestrator] 调用 Reviewer...', file=sys.stderr)
            review_result = self.send_to_agent('reviewer', {
                'action': 'review',
                'report': report or {}
            })
            review = review_result.get('data')
            
            duration = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'taskId': task_id,
                'symbol': symbol,
                'report': {
                    **report,
                    'qualityCheck': review
                },
                'metrics': {
                    'totalSteps': 4,
                    'completedSteps': 4,
                    'duration': duration
                }
            }
            
        except Exception as e:
            print(f'[Orchestrator] 任务失败：{e}', file=sys.stderr)
            return {
                'success': False,
                'taskId': task_id,
                'error': str(e)
            }
    
    def extract_symbol(self, user_input: str) -> Optional[str]:
        """从用户输入中提取股票代码"""
        input_upper = user_input.upper().strip()
        
        # 直接是股票代码
        import re
        if re.match(r'^[A-Z]{1,5}$', input_upper):
            return input_upper
        
        # 公司名称映射
        company_map = {
            '苹果': 'AAPL', 'APPLE': 'AAPL',
            '微软': 'MSFT', 'MICROSOFT': 'MSFT',
            '谷歌': 'GOOGL', 'GOOGLE': 'GOOGL',
            '特斯拉': 'TSLA', 'TESLA': 'TSLA',
            '英伟达': 'NVDA', 'NVIDIA': 'NVDA',
            '亚马逊': 'AMZN', 'AMAZON': 'AMZN',
            'META': 'META', 'FACEBOOK': 'META',
            '奈飞': 'NFLX', 'NETFLIX': 'NFLX',
            '比亚迪': 'BYDDY',
            '美团': 'MPNGY',
        }
        
        for name, symbol in company_map.items():
            if name in input_upper or name in user_input:
                return symbol
        
        return None
    
    def shutdown(self):
        """关闭所有 Agent"""
        print(f'[Orchestrator] 关闭所有 Agent...', file=sys.stderr)
        
        for key, agent in self.agents.items():
            try:
                agent.process.stdin.write(json.dumps({'action': 'shutdown'}) + '\n')
                agent.process.stdin.flush()
                time.sleep(0.3)
            except:
                pass
            
            agent.process.terminate()
        
        print(f'[Orchestrator] 所有 Agent 已关闭', file=sys.stderr)

def main():
    orchestrator = OrchestratorAgent()
    
    try:
        # 启动子 Agent
        orchestrator.start_agents()
        
        # 获取用户输入
        user_input = ' '.join(sys.argv[1:])
        if not user_input:
            print('用法：python orchestrator-multi.py <股票代码或公司名称>', file=sys.stderr)
            print('示例：python orchestrator-multi.py AAPL', file=sys.stderr)
            print('      python orchestrator-multi.py 生成苹果财报', file=sys.stderr)
            sys.exit(1)
        
        # 处理请求
        result = orchestrator.handle_request(user_input)
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 关闭
        orchestrator.shutdown()
        sys.exit(0 if result.get('success') else 1)
        
    except Exception as e:
        print(f'[Orchestrator] 错误：{e}', file=sys.stderr)
        orchestrator.shutdown()
        sys.exit(1)

if __name__ == '__main__':
    main()
