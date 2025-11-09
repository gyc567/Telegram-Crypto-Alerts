"""
测试ErrorRecoveryManager错误恢复和监控系统
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.monitor.large_orders.src.error_recovery import (
    ErrorRecoveryManager,
    ErrorEvent,
    ErrorSeverity,
    ReconnectAttempt
)


class TestErrorRecoveryManager:
    """测试ErrorRecoveryManager"""
    
    @pytest.fixture
    def recovery(self):
        """创建错误恢复管理器"""
        return ErrorRecoveryManager(
            exchange_name="binance",
            max_reconnect_attempts=5,
            base_backoff=2.0,
            max_backoff=60.0,
            critical_error_threshold=3,
            recovery_timeout=300
        )
    
    def test_initialization(self, recovery):
        """测试初始化"""
        assert recovery.exchange_name == "binance"
        assert recovery.max_reconnect_attempts == 5
        assert recovery.base_backoff == 2.0
        assert recovery.max_backoff == 60.0
        assert recovery.critical_error_threshold == 3
        assert recovery.recovery_timeout == 300
        
        assert recovery.current_state == "disconnected"
        assert len(recovery.reconnect_attempts) == 0
        assert len(recovery.error_history) == 0
        assert recovery.last_successful_connection is None
        assert recovery.consecutive_failures == 0
        
        assert recovery.stats["total_errors"] == 0
        assert recovery.stats["reconnects_attempted"] == 0
        assert recovery.stats["reconnects_successful"] == 0
        assert recovery.stats["avg_reconnect_time"] == 0.0
    
    def test_set_callbacks(self, recovery):
        """测试设置回调函数"""
        admin_alert = Mock()
        state_change = Mock()
        recovery_callback = Mock()
        
        recovery.set_admin_alert_callback(admin_alert)
        recovery.set_state_change_callback(state_change)
        recovery.set_recovery_callback(recovery_callback)
        
        assert recovery.admin_alert_callback == admin_alert
        assert recovery.state_change_callback == state_change
        assert recovery.recovery_callback == recovery_callback
    
    def test_update_state(self, recovery):
        """测试状态更新"""
        mock_callback = Mock()
        recovery.set_state_change_callback(mock_callback)
        
        recovery.update_state("connecting")
        
        assert recovery.current_state == "connecting"
        mock_callback.assert_called_once_with("connecting")
    
    def test_record_error_low_severity(self, recovery):
        """测试记录低严重性错误"""
        recovery.record_error(
            "warning",
            "Test warning",
            ErrorSeverity.LOW
        )
        
        assert len(recovery.error_history) == 1
        assert recovery.stats["total_errors"] == 1
        
        error = recovery.error_history[0]
        assert error.error_type == "warning"
        assert error.message == "Test warning"
        assert error.severity == ErrorSeverity.LOW
    
    def test_record_error_high_severity(self, recovery):
        """测试记录高严重性错误"""
        alert_callback = Mock()
        recovery.set_admin_alert_callback(alert_callback)
        
        recovery.record_error(
            "connection_error",
            "Connection failed",
            ErrorSeverity.HIGH
        )
        
        assert len(recovery.error_history) == 1
        assert recovery.stats["total_errors"] == 1
        alert_callback.assert_called_once()
    
    def test_record_error_with_details(self, recovery):
        """测试记录带详细信息的错误"""
        recovery.record_error(
            "api_error",
            "API rate limit",
            ErrorSeverity.MEDIUM,
            details={"retry_after": 60, "status_code": 429}
        )
        
        error = recovery.error_history[0]
        assert error.details["retry_after"] == 60
        assert error.details["status_code"] == 429
    
    def test_start_reconnect_attempt(self, recovery):
        """测试开始重连尝试"""
        attempt_num = recovery.start_reconnect_attempt()
        
        assert attempt_num == 1
        assert len(recovery.reconnect_attempts) == 1
        assert recovery.stats["reconnects_attempted"] == 1
        
        attempt = recovery.reconnect_attempts[0]
        assert attempt.attempt_number == 1
        assert attempt.start_time is not None
        assert attempt.end_time is None
        assert attempt.success is False
        assert attempt.error is None
    
    def test_complete_reconnect_attempt_success(self, recovery):
        """测试重连尝试成功"""
        recovery.start_reconnect_attempt()
        
        recovery.complete_reconnect_attempt(1, True)
        
        attempt = recovery.reconnect_attempts[0]
        assert attempt.success is True
        assert attempt.end_time is not None
        assert recovery.consecutive_failures == 0
        assert recovery.stats["reconnects_successful"] == 1
    
    def test_complete_reconnect_attempt_failure(self, recovery):
        """测试重连尝试失败"""
        recovery.start_reconnect_attempt()
        
        error = ConnectionError("Connection refused")
        recovery.complete_reconnect_attempt(1, False, error)
        
        attempt = recovery.reconnect_attempts[0]
        assert attempt.success is False
        assert attempt.end_time is not None
        assert attempt.error == error
        assert recovery.consecutive_failures == 1
    
    def test_max_reconnect_attempts(self, recovery):
        """测试达到最大重连次数"""
        alert_callback = Mock()
        recovery.set_admin_alert_callback(alert_callback)
        
        # 模拟多次重连失败
        for i in range(recovery.max_reconnect_attempts):
            recovery.start_reconnect_attempt()
            recovery.complete_reconnect_attempt(i + 1, False, ConnectionError("Failed"))
        
        assert len(alert_callback.call_args_list) > 0
        # 应该收到关键错误告警（包含EXHAUSTED或CRITICAL）
        critical_alerts = [
            call for call in alert_callback.call_args_list
            if "EXHAUSTED" in str(call) or "CRITICAL" in str(call)
        ]
        assert len(critical_alerts) > 0
    
    def test_should_continue_reconnecting(self, recovery):
        """测试是否应该继续重连"""
        # 初始状态应该可以重连
        assert recovery.should_continue_reconnecting() is True
        
        # 模拟多次失败但未达到上限
        for i in range(recovery.max_reconnect_attempts - 1):
            recovery.start_reconnect_attempt()
            recovery.complete_reconnect_attempt(i + 1, False, ConnectionError("Failed"))
        
        assert recovery.should_continue_reconnecting() is True
        
        # 达到最大次数后不应该继续
        recovery.start_reconnect_attempt()
        recovery.complete_reconnect_attempt(
            recovery.max_reconnect_attempts,
            False,
            ConnectionError("Failed")
        )
        
        assert recovery.should_continue_reconnecting() is False
    
    def test_get_recent_errors(self, recovery):
        """测试获取最近的错误"""
        now = datetime.now()
        
        # 创建1小时前的错误
        old_error = ErrorEvent(
            timestamp=now - timedelta(hours=2),
            exchange="binance",
            error_type="old",
            message="Old error",
            severity=ErrorSeverity.LOW
        )
        
        # 创建最近的错误
        recent_error = ErrorEvent(
            timestamp=now - timedelta(minutes=30),
            exchange="binance",
            error_type="recent",
            message="Recent error",
            severity=ErrorSeverity.LOW
        )
        
        recovery.error_history = [old_error, recent_error]
        
        recent_errors = recovery._get_recent_errors(60)  # 1小时
        
        assert len(recent_errors) == 1
        assert recent_errors[0].error_type == "recent"
    
    def test_calculate_uptime_percentage(self, recovery):
        """测试计算运行时间百分比"""
        # 设置上次成功连接时间
        recovery.last_successful_connection = datetime.now() - timedelta(minutes=10)
        
        # 模拟5分钟重连时间
        attempt = ReconnectAttempt(
            attempt_number=1,
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now() - timedelta(minutes=4, seconds=50),
            success=True
        )
        recovery.reconnect_attempts = [attempt]
        
        uptime = recovery._calculate_uptime_percentage()
        
        # 10分钟总时间，10秒停机时间
        #  uptime = (600 - 10) / 600 * 100 = 98.33%
        assert 95 < uptime < 100
    
    def test_get_status_report(self, recovery):
        """测试获取状态报告"""
        now = datetime.now()
        
        # 模拟一些状态
        recovery.current_state = "connected"
        recovery.consecutive_failures = 0
        recovery.last_successful_connection = now - timedelta(minutes=5)
        recovery.start_reconnect_attempt()
        recovery.complete_reconnect_attempt(1, True)
        
        report = recovery.get_status_report()
        
        assert report["exchange"] == "binance"
        assert report["state"] == "connected"
        assert report["consecutive_failures"] == 0
        assert "last_successful_connection" in report
        assert report["total_errors"] == 0
        assert report["reconnect_attempts"] == 1
        assert report["reconnect_success_rate"] == 100.0
        # 允许微小的时间差异（由于执行时间）
        assert 0.0 <= report["avg_reconnect_time"] < 0.001
        assert 0 <= report["uptime_percentage"] <= 100
        assert report["recent_errors_1h"] == 0
    
    def test_multiple_reconnects(self, recovery):
        """测试多次重连统计"""
        # 第一次重连
        recovery.start_reconnect_attempt()
        recovery.complete_reconnect_attempt(1, True)

        # 第二次重连
        recovery.start_reconnect_attempt()
        recovery.complete_reconnect_attempt(2, True)

        # 检查统计数据
        assert recovery.stats["reconnects_attempted"] == 2
        assert recovery.stats["reconnects_successful"] == 2
        # reconnect_success_rate 在 get_status_report 中计算
        report = recovery.get_status_report()
        assert report["reconnect_success_rate"] == 100.0


class TestErrorEvent:
    """测试ErrorEvent数据模型"""
    
    def test_error_event_creation(self):
        """测试创建错误事件"""
        now = datetime.now()
        
        event = ErrorEvent(
            timestamp=now,
            exchange="binance",
            error_type="connection_error",
            message="Connection failed",
            severity=ErrorSeverity.HIGH,
            details={"error_code": 500},
            traceback_str="Traceback...",
            recovered=False
        )
        
        assert event.timestamp == now
        assert event.exchange == "binance"
        assert event.error_type == "connection_error"
        assert event.message == "Connection failed"
        assert event.severity == ErrorSeverity.HIGH
        assert event.details == {"error_code": 500}
        assert event.traceback_str == "Traceback..."
        assert event.recovered is False


class TestReconnectAttempt:
    """测试ReconnectAttempt数据模型"""
    
    def test_reconnect_attempt_creation(self):
        """测试创建重连尝试记录"""
        now = datetime.now()
        
        attempt = ReconnectAttempt(
            attempt_number=1,
            start_time=now,
            end_time=now + timedelta(seconds=5),
            success=True,
            error=None,
            backoff_seconds=2.0
        )
        
        assert attempt.attempt_number == 1
        assert attempt.start_time == now
        assert attempt.end_time == now + timedelta(seconds=5)
        assert attempt.success is True
        assert attempt.error is None
        assert attempt.backoff_seconds == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
