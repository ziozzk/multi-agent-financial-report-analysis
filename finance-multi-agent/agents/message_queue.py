#!/usr/bin/env python3
"""
基于文件的简易消息队列

用于 Agent 间通信，支持：
- 发布/订阅模式
- 持久化（文件存储）
- 文件锁保证并发安全
"""

import os
import json
import time
import fcntl
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# 队列目录
QUEUE_DIR = Path('/tmp/agent-queues')
QUEUE_DIR.mkdir(exist_ok=True)


class MessageQueue:
    """基于文件的消息队列"""
    
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.queue_file = QUEUE_DIR / f'{queue_name}.jsonl'
        self.lock_file = QUEUE_DIR / f'{queue_name}.lock'
        
    def _acquire_lock(self, exclusive: bool = True):
        """获取文件锁"""
        self.lock_fd = open(self.lock_file, 'w')
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(self.lock_fd.fileno(), lock_type)
        
    def _release_lock(self):
        """释放文件锁"""
        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
        self.lock_fd.close()
        
    def publish(self, message: Dict, timeout_ms: int = 30000) -> bool:
        """发布消息"""
        try:
            self._acquire_lock()
            
            message['_timestamp'] = time.time() * 1000
            message['_timeout'] = timeout_ms
            
            with open(self.queue_file, 'a') as f:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
            
            return True
        except Exception as e:
            print(f'[MQ] Publish error: {e}')
            return False
        finally:
            self._release_lock()
    
    def consume(self, timeout_ms: int = 5000) -> Optional[Dict]:
        """消费消息（阻塞等待）"""
        start_time = time.time()
        
        while True:
            try:
                self._acquire_lock()
                
                if not self.queue_file.exists():
                    self._release_lock()
                    time.sleep(0.1)
                    continue
                
                # 读取第一行
                with open(self.queue_file, 'r') as f:
                    lines = f.readlines()
                
                if not lines:
                    self._release_lock()
                    
                    # 检查是否超时
                    if (time.time() - start_time) * 1000 > timeout_ms:
                        return None
                    
                    time.sleep(0.1)
                    continue
                
                # 移除第一行
                with open(self.queue_file, 'w') as f:
                    f.writelines(lines[1:])
                
                self._release_lock()
                
                message = json.loads(lines[0].strip())
                
                # 检查是否过期
                now = time.time() * 1000
                if now - message.get('_timestamp', 0) > message.get('_timeout', 30000):
                    continue  # 过期，跳过
                
                return message
                
            except Exception as e:
                self._release_lock()
                time.sleep(0.1)
                
                if (time.time() - start_time) * 1000 > timeout_ms:
                    return None
    
    def peek(self) -> Optional[Dict]:
        """查看第一条消息（不消费）"""
        try:
            self._acquire_lock(exclusive=False)
            
            if not self.queue_file.exists():
                return None
            
            with open(self.queue_file, 'r') as f:
                line = f.readline()
            
            if line:
                return json.loads(line.strip())
            return None
        except:
            return None
        finally:
            self._release_lock()
    
    def clear(self):
        """清空队列"""
        try:
            self._acquire_lock()
            if self.queue_file.exists():
                self.queue_file.unlink()
        finally:
            self._release_lock()
    
    def size(self) -> int:
        """获取队列大小"""
        try:
            self._acquire_lock(exclusive=False)
            
            if not self.queue_file.exists():
                return 0
            
            with open(self.queue_file, 'r') as f:
                return sum(1 for _ in f)
        except:
            return 0
        finally:
            self._release_lock()


class AgentRegistry:
    """Agent 注册中心 - 记录 Agent 状态和能力"""
    
    REGISTRY_FILE = QUEUE_DIR / 'registry.json'
    
    def __init__(self):
        self.lock_fd = None
    
    def _acquire_lock(self, exclusive: bool = True):
        try:
            self.lock_fd = open(QUEUE_DIR / 'registry.lock', 'w')
            lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(self.lock_fd.fileno(), lock_type)
        except Exception as e:
            print(f'[Registry] 获取锁失败：{e}', file=sys.stderr)
        
    def _release_lock(self):
        try:
            if self.lock_fd:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_fd = None
        except Exception as e:
            print(f'[Registry] 释放锁失败：{e}', file=sys.stderr)
    
    def register(self, agent_id: str, agent_type: str, capabilities: List[str]):
        """注册 Agent"""
        try:
            self._acquire_lock()
            
            registry = {}
            if self.REGISTRY_FILE.exists():
                with open(self.REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
            
            registry[agent_id] = {
                'type': agent_type,
                'capabilities': capabilities,
                'status': 'active',
                'registered_at': datetime.now().isoformat(),
                'last_heartbeat': time.time(),
                'stats': {
                    'tasks_processed': 0,
                    'success_rate': 1.0
                }
            }
            
            with open(self.REGISTRY_FILE, 'w') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
        finally:
            self._release_lock()
    
    def unregister(self, agent_id: str):
        """注销 Agent"""
        try:
            self._acquire_lock()
            
            if self.REGISTRY_FILE.exists():
                with open(self.REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                if agent_id in registry:
                    del registry[agent_id]
                
                with open(self.REGISTRY_FILE, 'w') as f:
                    json.dump(registry, f, indent=2, ensure_ascii=False)
            
        finally:
            self._release_lock()
    
    def get_agents(self, agent_type: Optional[str] = None) -> Dict:
        """获取注册的 Agent"""
        try:
            self._acquire_lock(exclusive=False)
            
            if not self.REGISTRY_FILE.exists():
                return {}
            
            with open(self.REGISTRY_FILE, 'r') as f:
                registry = json.load(f)
            
            if agent_type:
                return {k: v for k, v in registry.items() if v.get('type') == agent_type}
            
            return registry
        finally:
            self._release_lock()
    
    def update_stats(self, agent_id: str, stats: Dict):
        """更新 Agent 统计信息（用于学习）"""
        try:
            self._acquire_lock()
            
            if self.REGISTRY_FILE.exists():
                with open(self.REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                if agent_id in registry:
                    registry[agent_id].update(stats)
                    registry[agent_id]['last_heartbeat'] = time.time()
                    
                    # 更新统计
                    if 'tasks_processed' in stats:
                        registry[agent_id]['stats']['tasks_processed'] += stats['tasks_processed']
                    if 'success' in stats:
                        old_stats = registry[agent_id]['stats']
                        total = old_stats.get('tasks_processed', 0) + 1
                        success = old_stats.get('success_count', 0) + (1 if stats['success'] else 0)
                        registry[agent_id]['stats']['success_rate'] = success / total if total > 0 else 1.0
                
                with open(self.REGISTRY_FILE, 'w') as f:
                    json.dump(registry, f, indent=2, ensure_ascii=False)
            
        finally:
            self._release_lock()


# 预定义队列实例
REQUEST_QUEUE = MessageQueue('requests')      # 用户请求
DATA_QUEUE = MessageQueue('data')             # DataFetcher 输出
ANALYSIS_QUEUE = MessageQueue('analysis')     # Analyst 输出
REPORT_QUEUE = MessageQueue('report')         # Reporter 输出
REVIEW_QUEUE = MessageQueue('review')         # Reviewer 输出
NEGOTIATION_QUEUE = MessageQueue('negotiation')  # Agent 协商
