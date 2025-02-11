"""WebSocket指标收集和导出模块"""
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import time
from datetime import datetime, timedelta
import asyncio
import Lugwit_Module as LM

lprint = LM.lprint

class MetricsAlert:
    """指标报警"""
    def __init__(self, name: str, threshold: float, window: int = 60):
        self.name = name
        self.threshold = threshold
        self.window = window  # 时间窗口(秒)
        self.values: List[tuple[float, float]] = []  # (timestamp, value)
        self.last_alert: Optional[float] = None
        self.alert_cooldown = 300  # 报警冷却时间(秒)

    def add_value(self, value: float) -> bool:
        """添加新值并检查是否需要报警
        
        Args:
            value: 指标值
            
        Returns:
            bool: 是否需要报警
        """
        now = time.time()
        self.values.append((now, value))
        
        # 清理过期数据
        cutoff = now - self.window
        self.values = [(t, v) for t, v in self.values if t > cutoff]
        
        # 计算平均值
        if not self.values:
            return False
            
        avg_value = sum(v for _, v in self.values) / len(self.values)
        
        # 检查是否需要报警
        if avg_value > self.threshold:
            if self.last_alert is None or (now - self.last_alert) > self.alert_cooldown:
                self.last_alert = now
                return True
        return False

class Metrics:
    """监控指标收集"""
    def __init__(self):
        self.event_counts = defaultdict(int)  # 事件计数
        self.event_latencies = defaultdict(list)  # 事件处理延迟
        self.error_counts = defaultdict(int)  # 错误计数
        self.retry_counts = defaultdict(int)  # 重试计数
        self.active_connections = 0  # 活跃连接数
        self.message_counts = defaultdict(int)  # 消息计数
        self.room_counts = defaultdict(int)  # 房间计数
        
        # 性能指标
        self.event_processing_times = defaultdict(list)  # 事件处理时间
        self.queue_sizes = []  # 队列大小历史
        self.memory_usage = []  # 内存使用历史
        
        # 报警配置
        self.alerts = {
            "high_latency": MetricsAlert("high_latency", 1.0),  # 延迟超过1秒
            "error_rate": MetricsAlert("error_rate", 0.1),  # 错误率超过10%
            "connection_limit": MetricsAlert("connection_limit", 1000),  # 连接数超过1000
            "queue_size": MetricsAlert("queue_size", 100)  # 队列大小超过100
        }
        
        # 启动指标聚合任务
        asyncio.create_task(self._metrics_aggregation_loop())

    async def _metrics_aggregation_loop(self):
        """指标聚合循环"""
        while True:
            try:
                # 聚合延迟数据
                for event_type in list(self.event_latencies.keys()):
                    latencies = self.event_latencies[event_type]
                    if latencies:
                        avg_latency = sum(latencies) / len(latencies)
                        if self.alerts["high_latency"].add_value(avg_latency):
                            lprint(f"警告: 事件 {event_type} 的平均延迟 ({avg_latency:.2f}s) 过高")
                        # 只保留最近的数据
                        self.event_latencies[event_type] = latencies[-100:]
                
                # 检查错误率
                total_events = sum(self.event_counts.values())
                total_errors = sum(self.error_counts.values())
                if total_events > 0:
                    error_rate = total_errors / total_events
                    if self.alerts["error_rate"].add_value(error_rate):
                        lprint(f"警告: 错误率 ({error_rate:.2%}) 过高")
                
                # 检查连接数
                if self.alerts["connection_limit"].add_value(self.active_connections):
                    lprint(f"警告: 活跃连接数 ({self.active_connections}) 过高")
                
                # 清理历史数据
                self._cleanup_old_data()
                
                await asyncio.sleep(10)  # 每10秒聚合一次
                
            except Exception as e:
                lprint(f"指标聚合错误: {str(e)}")
                await asyncio.sleep(60)  # 错误后等待较长时间

    def _cleanup_old_data(self):
        """清理旧数据"""
        now = time.time()
        cutoff = now - 3600  # 保留1小时的数据
        
        # 清理性能指标
        self.queue_sizes = [x for x in self.queue_sizes if x[0] > cutoff]
        self.memory_usage = [x for x in self.memory_usage if x[0] > cutoff]

    def record_event(self, event_type: str, latency: float):
        """记录事件指标"""
        self.event_counts[event_type] += 1
        self.event_latencies[event_type].append(latency)

    def record_error(self, error_type: str):
        """记录错误指标"""
        self.error_counts[error_type] += 1

    def record_retry(self, operation: str):
        """记录重试指标"""
        self.retry_counts[operation] += 1

    def update_connections(self, delta: int):
        """更新连接数"""
        self.active_connections += delta

    def record_message(self, message_type: str):
        """记录消息指标"""
        self.message_counts[message_type] += 1

    def record_room(self, room_type: str, delta: int):
        """记录房间指标"""
        self.room_counts[room_type] += delta

    def record_queue_size(self, size: int):
        """记录队列大小"""
        now = time.time()
        self.queue_sizes.append((now, size))
        if self.alerts["queue_size"].add_value(size):
            lprint(f"警告: 事件队列大小 ({size}) 过高")

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        lines = []
        
        # 事件计数
        lines.append("# HELP websocket_events_total WebSocket事件总数")
        lines.append("# TYPE websocket_events_total counter")
        for event_type, count in self.event_counts.items():
            lines.append(f'websocket_events_total{{type="{event_type}"}} {count}')
        
        # 事件延迟
        lines.append("# HELP websocket_event_latency_seconds WebSocket事件处理延迟")
        lines.append("# TYPE websocket_event_latency_seconds histogram")
        for event_type, latencies in self.event_latencies.items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                lines.append(f'websocket_event_latency_seconds{{type="{event_type}"}} {avg_latency}')
        
        # 错误计数
        lines.append("# HELP websocket_errors_total WebSocket错误总数")
        lines.append("# TYPE websocket_errors_total counter")
        for error_type, count in self.error_counts.items():
            lines.append(f'websocket_errors_total{{type="{error_type}"}} {count}')
        
        # 活跃连接
        lines.append("# HELP websocket_active_connections WebSocket活跃连接数")
        lines.append("# TYPE websocket_active_connections gauge")
        lines.append(f"websocket_active_connections {self.active_connections}")
        
        # 消息计数
        lines.append("# HELP websocket_messages_total WebSocket消息总数")
        lines.append("# TYPE websocket_messages_total counter")
        for message_type, count in self.message_counts.items():
            lines.append(f'websocket_messages_total{{type="{message_type}"}} {count}')
        
        # 房间计数
        lines.append("# HELP websocket_rooms WebSocket房间数")
        lines.append("# TYPE websocket_rooms gauge")
        for room_type, count in self.room_counts.items():
            lines.append(f'websocket_rooms{{type="{room_type}"}} {count}')
        
        # 队列大小
        if self.queue_sizes:
            current_size = self.queue_sizes[-1][1]
            lines.append("# HELP websocket_event_queue_size WebSocket事件队列大小")
            lines.append("# TYPE websocket_event_queue_size gauge")
            lines.append(f"websocket_event_queue_size {current_size}")
        
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "events": {
                event_type: {
                    "count": count,
                    "avg_latency": sum(self.event_latencies[event_type]) / len(self.event_latencies[event_type])
                    if self.event_latencies[event_type] else 0
                }
                for event_type, count in self.event_counts.items()
            },
            "errors": dict(self.error_counts),
            "retries": dict(self.retry_counts),
            "active_connections": self.active_connections,
            "messages": dict(self.message_counts),
            "rooms": dict(self.room_counts),
            "performance": {
                "queue_size": self.queue_sizes[-1][1] if self.queue_sizes else 0,
                "memory_usage_mb": self.memory_usage[-1][1] if self.memory_usage else 0
            }
        }
        return stats 