"""
错误恢复和WebSocket状态监控系统
增强重连失败告警和状态监控
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"          # 警告，不影响主要功能
    MEDIUM = "medium"    # 中等，影响部分功能
    HIGH = "high"        # 严重，影响核心功能
    CRITICAL = "critical"  # 致命，系统不可用


@dataclass
class ErrorEvent:
    """错误事件数据模型"""
    timestamp: datetime
    exchange: str
    error_type: str
    message: str
    severity: ErrorSeverity
    details: Dict = field(default_factory=dict)
    traceback_str: Optional[str] = None
    recovered: bool = False


@dataclass
class ReconnectAttempt:
    """重连尝试记录"""
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[Exception] = None
    backoff_seconds: float = 0


class ErrorRecoveryManager:
    """
    错误恢复管理器
    
    功能：
    1. 跟踪WebSocket连接状态
    2. 记录重连尝试和结果
    3. 检测异常模式（频繁断线）
    4. 发送管理员告警
    5. 指数退避重连
    """
    
    def __init__(
        self,
        exchange_name: str,
        max_reconnect_attempts: int = 10,
        base_backoff: float = 2.0,
        max_backoff: float = 300.0,  # 5分钟
        critical_error_threshold: int = 3,
        recovery_timeout: int = 600  # 10分钟
    ):
        self.exchange_name = exchange_name
        self.max_reconnect_attempts = max_reconnect_attempts
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.critical_error_threshold = critical_error_threshold
        self.recovery_timeout = recovery_timeout
        
        # 状态跟踪
        self.current_state = "disconnected"
        self.reconnect_attempts: List[ReconnectAttempt] = []
        self.error_history: List[ErrorEvent] = []
        self.last_successful_connection: Optional[datetime] = None
        self.consecutive_failures = 0
        
        # 回调函数
        self.admin_alert_callback: Optional[Callable[[str], None]] = None
        self.state_change_callback: Optional[Callable[[str], None]] = None
        self.recovery_callback: Optional[Callable[[], None]] = None
        
        # 统计信息
        self.stats = {
            "total_errors": 0,
            "reconnects_attempted": 0,
            "reconnects_successful": 0,
            "avg_reconnect_time": 0.0,
            "uptime_percentage": 0.0,
            "last_alert_time": None
        }
        
        logger.info(f"初始化 {exchange_name} 错误恢复管理器")
    
    def set_admin_alert_callback(self, callback: Callable[[str], None]) -> None:
        """设置管理员告警回调"""
        self.admin_alert_callback = callback
    
    def set_state_change_callback(self, callback: Callable[[str], None]) -> None:
        """设置状态变更回调"""
        self.state_change_callback = callback
    
    def set_recovery_callback(self, callback: Callable[[], None]) -> None:
        """设置恢复成功回调"""
        self.recovery_callback = callback
    
    def update_state(self, new_state: str) -> None:
        """更新连接状态"""
        old_state = self.current_state
        self.current_state = new_state
        
        logger.info(f"{self.exchange_name}: 状态变更 {old_state} -> {new_state}")
        
        if self.state_change_callback:
            self.state_change_callback(new_state)
        
        # 状态变化时更新统计
        if new_state == "connected":
            self._on_connection_restored()
        elif new_state == "failed":
            self._on_connection_failed()
    
    def _on_connection_restored(self) -> None:
        """连接恢复时的处理"""
        self.last_successful_connection = datetime.now()
        self.consecutive_failures = 0
        self.stats["reconnects_successful"] += 1
        
        logger.info(f"{self.exchange_name}: 连接已恢复")
        
        if self.recovery_callback:
            self.recovery_callback()
        
        # 发送恢复通知
        self._send_alert(
            f"✅ {self.exchange_name} 连接已恢复",
            ErrorSeverity.LOW
        )
    
    def _on_connection_failed(self) -> None:
        """连接失败时的处理"""
        self.consecutive_failures += 1
        
        logger.warning(f"{self.exchange_name}: 连接失败 (连续 {self.consecutive_failures} 次)")
        
        # 检查是否需要发送关键错误告警
        if self.consecutive_failures >= self.critical_error_threshold:
            self._send_critical_alert()
    
    def _send_critical_alert(self) -> None:
        """发送关键错误告警"""
        uptime = self._calculate_uptime_percentage()
        recent_errors = self._get_recent_errors(minutes=60)
        
        alert_msg = (
            f"🚨 CRITICAL: {self.exchange_name} 连接失败\n"
            f"连续失败次数: {self.consecutive_failures}\n"
            f"过去1小时错误数: {len(recent_errors)}\n"
            f"系统运行时间: {uptime:.1f}%\n"
            f"重连尝试: {len(self.reconnect_attempts)}\n\n"
            f"需要立即检查！"
        )
        
        self._send_alert(alert_msg, ErrorSeverity.CRITICAL)
    
    def _send_alert(self, message: str, severity: ErrorSeverity) -> None:
        """发送管理员告警"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # 记录到日志
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(full_message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(full_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(full_message)
        else:
            logger.info(full_message)
        
        # 发送到管理员
        if self.admin_alert_callback:
            self.admin_alert_callback(full_message)
        
        # 更新告警时间
        self.stats["last_alert_time"] = datetime.now()
    
    def record_error(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity,
        details: Optional[Dict] = None
    ) -> None:
        """记录错误事件"""
        error_event = ErrorEvent(
            timestamp=datetime.now(),
            exchange=self.exchange_name,
            error_type=error_type,
            message=message,
            severity=severity,
            details=details or {},
            traceback_str=traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        )
        
        self.error_history.append(error_event)
        self.stats["total_errors"] += 1
        
        # 只保留最近1000个错误记录
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        # 关键错误立即告警
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._send_alert(
                f"⚠️ {self.exchange_name} 错误: {message}",
                severity
            )
    
    def start_reconnect_attempt(self) -> int:
        """开始重连尝试"""
        attempt_number = len(self.reconnect_attempts) + 1
        
        # 创建重连记录
        attempt = ReconnectAttempt(
            attempt_number=attempt_number,
            start_time=datetime.now()
        )
        
        self.reconnect_attempts.append(attempt)
        self.stats["reconnects_attempted"] += 1
        
        # 计算退避时间
        backoff = min(
            self.base_backoff * (2 ** (attempt_number - 1)),
            self.max_backoff
        )
        
        logger.info(
            f"{self.exchange_name}: 开始第 {attempt_number} 次重连，"
            f"退避时间 {backoff:.1f}秒"
        )
        
        return attempt_number
    
    def complete_reconnect_attempt(
        self,
        attempt_number: int,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """完成重连尝试"""
        if attempt_number > len(self.reconnect_attempts):
            logger.error(f"无效的重连尝试编号: {attempt_number}")
            return
        
        attempt = self.reconnect_attempts[attempt_number - 1]
        attempt.end_time = datetime.now()
        attempt.success = success
        attempt.error = error
        attempt.backoff_seconds = 0  # 将在reconnect方法中设置
        
        if success:
            self._on_successful_reconnect(attempt)
        else:
            self._on_failed_reconnect(attempt, error)
    
    def _on_successful_reconnect(self, attempt: ReconnectAttempt) -> None:
        """重连成功"""
        self.consecutive_failures = 0
        self.stats["reconnects_successful"] += 1
        
        # 计算重连时间
        if attempt.end_time:
            reconnect_time = (attempt.end_time - attempt.start_time).total_seconds()
            self._update_avg_reconnect_time(reconnect_time)
        
        logger.info(
            f"{self.exchange_name}: 第 {attempt.attempt_number} 次重连成功，"
            f"耗时 {reconnect_time:.1f}秒"
        )
    
    def _on_failed_reconnect(self, attempt: ReconnectAttempt, error: Optional[Exception]) -> None:
        """重连失败"""
        self.consecutive_failures += 1
        
        error_msg = str(error) if error else "未知错误"
        logger.error(
            f"{self.exchange_name}: 第 {attempt.attempt_number} 次重连失败: {error_msg}"
        )
        
        # 记录错误事件
        self.record_error(
            "reconnect_failed",
            f"重连失败 ({error_msg})",
            ErrorSeverity.MEDIUM if self.consecutive_failures < self.critical_error_threshold else ErrorSeverity.HIGH
        )
        
        # 检查是否达到最大重连次数
        if self.consecutive_failures >= self.max_reconnect_attempts:
            self._send_max_attempts_alert()
    
    def _send_max_attempts_alert(self) -> None:
        """发送达到最大重连次数的告警"""
        alert_msg = (
            f"🔴 EXHAUSTED: {self.exchange_name} 达到最大重连次数 ({self.max_reconnect_attempts})\n"
            f"连续失败: {self.consecutive_failures} 次\n"
            f"请立即手动检查系统状态！"
        )
        
        self._send_alert(alert_msg, ErrorSeverity.CRITICAL)
    
    def _update_avg_reconnect_time(self, reconnect_time: float) -> None:
        """更新平均重连时间"""
        current_avg = self.stats["avg_reconnect_time"]
        successful_attempts = self.stats["reconnects_successful"]
        
        if successful_attempts == 1:
            self.stats["avg_reconnect_time"] = reconnect_time
        else:
            # 增量更新平均时间
            total_time = (current_avg * (successful_attempts - 1)) + reconnect_time
            self.stats["avg_reconnect_time"] = total_time / successful_attempts
    
    def _calculate_uptime_percentage(self) -> float:
        """计算运行时间百分比"""
        if not self.last_successful_connection:
            return 0.0
        
        now = datetime.now()
        total_time = (now - self.last_successful_connection).total_seconds()
        downtime = sum(
            (attempt.end_time - attempt.start_time).total_seconds()
            for attempt in self.reconnect_attempts
            if attempt.end_time
        )
        
        if total_time <= 0:
            return 0.0
        
        uptime = ((total_time - downtime) / total_time) * 100
        return max(0.0, min(100.0, uptime))
    
    def _get_recent_errors(self, minutes: int = 60) -> List[ErrorEvent]:
        """获取最近的错误事件"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            error for error in self.error_history
            if error.timestamp > cutoff
        ]
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        uptime = self._calculate_uptime_percentage()
        recent_errors = self._get_recent_errors(60)
        
        return {
            "exchange": self.exchange_name,
            "state": self.current_state,
            "consecutive_failures": self.consecutive_failures,
            "last_successful_connection": self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            "total_errors": self.stats["total_errors"],
            "reconnect_attempts": self.stats["reconnects_attempted"],
            "reconnect_success_rate": (
                self.stats["reconnects_successful"] / max(1, self.stats["reconnects_attempted"])
            ) * 100,
            "avg_reconnect_time": self.stats["avg_reconnect_time"],
            "uptime_percentage": uptime,
            "recent_errors_1h": len(recent_errors),
            "errors_last_hour": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "type": error.error_type,
                    "message": error.message,
                    "severity": error.severity.value
                }
                for error in recent_errors
            ]
        }
    
    def should_continue_reconnecting(self) -> bool:
        """检查是否应该继续重连"""
        return self.consecutive_failures < self.max_reconnect_attempts


# 使用示例
"""
# 1. 创建错误恢复管理器
recovery = ErrorRecoveryManager(
    exchange_name="binance",
    max_reconnect_attempts=10,
    base_backoff=2.0,
    max_backoff=300.0,
    critical_error_threshold=3
)

# 2. 设置告警回调
recovery.set_admin_alert_callback(send_admin_telegram_alert)
recovery.set_state_change_callback(on_state_changed)
recovery.set_recovery_callback(on_connection_recovered)

# 3. 记录错误
recovery.record_error(
    "websocket_error",
    "连接被远程主机强制关闭",
    ErrorSeverity.HIGH
)

# 4. 开始重连
if recovery.should_continue_reconnecting():
    attempt_num = recovery.start_reconnect_attempt()
    # ... 尝试重连 ...
    success = await attempt_reconnect()
    recovery.complete_reconnect_attempt(attempt_num, success, error if not success else None)

# 5. 获取状态报告
status = recovery.get_status_report()
print(f"运行时间: {status['uptime_percentage']:.1f}%")
"""
