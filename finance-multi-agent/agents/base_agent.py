#!/usr/bin/env python3
"""
Agent 基类

提供所有 Agent 的通用功能：
- 信号处理（优雅关闭）
- 日志记录
- 统计信息
- 注册到注册中心
"""

import os
import sys
import json
import time
import signal
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime

from message_queue import AgentRegistry


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, agent_type: str, capabilities: list):
        self.name = name
        self.agent_type = agent_type
        self.agent_id = f'{name}-{os.getpid()}'
        self.capabilities = capabilities
        self.status = 'starting'
        self.running = True
        
        # 统计信息
        self.stats = {
            'tasks_processed': 0,
            'tasks_success': 0,
            'tasks_failed': 0,
            'started_at': datetime.now().isoformat()
        }
        
        # 注册到注册中心
        self.registry = AgentRegistry()
        self.registry.register(self.agent_id, self.agent_type, self.capabilities)
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        print(f'[{self.name}] Agent 已启动：{self.agent_id}', file=sys.stderr)
    
    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        print(f'[{self.name}] 收到关闭信号，正在清理...', file=sys.stderr)
        self.running = False
        self.cleanup()
        self.registry.unregister(self.agent_id)
        self._save_stats()
        sys.exit(0)
    
    def _update_stats(self, success: bool):
        """更新统计信息"""
        self.stats['tasks_processed'] += 1
        if success:
            self.stats['tasks_success'] += 1
        else:
            self.stats['tasks_failed'] += 1
        
        # 更新注册中心
        self.registry.update_stats(self.agent_id, {
            'tasks_processed': 1,
            'success': success
        })
    
    def _save_stats(self):
        """保存统计信息到文件"""
        stats_file = f'/tmp/agent-stats/{self.name}.json'
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def _load_stats(self):
        """加载历史统计信息"""
        stats_file = f'/tmp/agent-stats/{self.name}.json'
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    self.stats.update(json.load(f))
            except:
                pass
    
    @abstractmethod
    def handle_message(self, message: Dict):
        """处理消息（子类实现）"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理资源（子类实现）"""
        pass
    
    def run(self):
        """主循环"""
        self._load_stats()
        self.status = 'ready'
        self.registry.update_stats(self.agent_id, {'status': 'ready'})
        
        print(f'[{self.name}] 等待请求...', file=sys.stderr)
        
        while self.running:
            try:
                message = self.consume_message()
                
                if message is None:
                    # 超时，发送心跳
                    self.registry.update_stats(self.agent_id, {
                        'last_heartbeat': time.time(),
                        'status': 'idle'
                    })
                    continue
                
                # 处理消息
                success = self.process_message(message)
                self._update_stats(success)
                
            except Exception as e:
                print(f'[{self.name}] 错误：{e}', file=sys.stderr)
                time.sleep(1)
        
        self.cleanup()
        self.registry.unregister(self.agent_id)
        self._save_stats()
    
    def consume_message(self, timeout_ms: int = 5000):
        """消费消息（子类实现具体队列）"""
        return None
    
    def process_message(self, message: Dict) -> bool:
        """处理消息并返回是否成功"""
        try:
            self.handle_message(message)
            return True
        except Exception as e:
            print(f'[{self.name}] 处理失败：{e}', file=sys.stderr)
            return False
