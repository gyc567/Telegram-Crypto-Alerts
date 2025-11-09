"""
测试配置文件
"""
import pytest
import asyncio
from unittest.mock import Mock


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_telegram_bot():
    """模拟Telegram Bot"""
    bot = Mock()
    bot.send_message = Mock()
    return bot


@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    ws = Mock()
    ws.recv = Mock()
    ws.send = Mock()
    ws.close = Mock()
    return ws


@pytest.fixture
def sample_trade_data():
    """示例交易数据"""
    return {
        "e": "trade",
        "E": 123456789,
        "s": "BTCUSDT",
        "t": 12345,
        "p": "50000.00",
        "q": "50.00",
        "b": 88,
        "a": 50,
        "T": 123456789,
        "m": False,
        "M": True
    }


@pytest.fixture
def binance_response():
    """币安API响应示例"""
    return {
        "symbol": "BTCUSDT",
        "price": "50000.00"
    }


@pytest.fixture
def error_scenarios():
    """错误场景数据"""
    return {
        "connection_error": ConnectionError("Connection refused"),
        "timeout_error": asyncio.TimeoutError("Request timeout"),
        "rate_limit_error": Exception("Rate limit exceeded"),
        "invalid_response": ValueError("Invalid response format")
    }


# 测试数据提供者
def pytest_generate_tests(metafunc):
    """为测试生成参数化数据"""
    if "symbol" in metafunc.fixturenames:
        metafunc.parametrize("symbol", [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "SOLUSDT"
        ])
    
    if "stable_coin" in metafunc.fixturenames:
        metafunc.parametrize("stable_coin", [
            "USDT",
            "BUSD",
            "USDC",
            "DAI"
        ])


# 自定义标记
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "api: 需要API访问的测试")


# 测试覆盖率配置
# 注意：pytest_cov 插件在pytest.ini或setup.cfg中配置
