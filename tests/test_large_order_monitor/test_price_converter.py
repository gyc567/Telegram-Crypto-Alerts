"""
测试PriceConverter USD转换策略
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.monitor.large_orders.src.price_converter import PriceConverter, ExchangeRate


class TestPriceConverter:
    """测试PriceConverter"""
    
    @pytest.fixture
    async def converter(self):
        """创建转换器实例"""
        async with PriceConverter(cache_ttl=60) as converter:
            yield converter
    
    @pytest.mark.asyncio
    async def test_is_stable_coin(self, converter):
        """测试稳定币识别"""
        assert converter._is_stable_coin("USDT")
        assert converter._is_stable_coin("BUSD")
        assert converter._is_stable_coin("USDC")
        assert converter._is_stable_coin("DAI")
        assert not converter._is_stable_coin("BTC")
        assert not converter._is_stable_coin("ETH")
    
    @pytest.mark.asyncio
    async def test_normalize_symbol(self, converter):
        """测试符号标准化"""
        assert converter._normalize_symbol("btcusdt") == "BTCUSDT"
        assert converter._normalize_symbol("BTC/USDT") == "BTCUSDT"
        assert converter._normalize_symbol("BTC-USDT") == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_extract_currencies(self, converter):
        """测试货币提取"""
        # USDT交易对
        base, quote = converter._extract_currencies("BTCUSDT")
        assert base == "BTC"
        assert quote == "USDT"
        
        # BUSD交易对
        base, quote = converter._extract_currencies("ETHBUSD")
        assert base == "ETH"
        assert quote == "BUSD"
        
        # USDC交易对
        base, quote = converter._extract_currencies("ADAUSDC")
        assert base == "ADA"
        assert quote == "USDC"
    
    @pytest.mark.asyncio
    async def test_convert_stable_coin_pair(self, converter):
        """测试稳定币交易对转换"""
        # USDT交易对应该直接使用价格
        result = await converter.convert_to_usd("BTCUSDT", 50000, 10)
        assert result == 500000  # 50000 * 10
        
        # BUSD交易对
        result = await converter.convert_to_usd("ETHBUSD", 3000, 100)
        assert result == 300000  # 3000 * 100
        
        # USDC交易对
        result = await converter.convert_to_usd("BNBUSDC", 300, 1000)
        assert result == 300000  # 300 * 1000
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_convert_via_api(self, mock_get, converter):
        """测试通过API转换"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"price": "1.0"})
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        # 测试USDT/USD转换
        result = await converter._get_usdt_usd_rate()
        assert result == 1.0
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_convert_coin_to_usdt(self, mock_get, converter):
        """测试货币转换为USDT"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"price": "0.05"})
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        # 测试ETH/USDT转换
        result = await converter._get_coin_usdt_rate("ETH")
        assert result == 0.05
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_convert_stable_coin(self, converter):
        """测试稳定币直接转换"""
        # 稳定币应该返回1.0
        result = await converter._get_coin_usdt_rate("USDT")
        assert result == 1.0
        
        result = await converter._get_coin_usdt_rate("BUSD")
        assert result == 1.0
    
    @pytest.mark.asyncio
    async def test_batch_convert(self, converter):
        """测试批量转换"""
        with patch.object(converter, 'convert_to_usd', side_effect=[50000, 3000, 2500000]):
            trades = [
                ("BTCUSDT", 50000, 1),
                ("ETHUSDT", 3000, 1),
                ("BTCUSDT", 50000, 50)
            ]
            
            results = await converter.batch_convert(trades)
            
            assert results == [50000, 3000, 2500000]
            assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, converter):
        """测试缓存功能"""
        # 第一次调用，创建缓存
        rate = ExchangeRate(
            symbol="USDT",
            rate=1.0,
            source="test",
            timestamp=1234567890000,
            ttl=60
        )
        
        converter._rate_cache["USDT"] = rate
        
        # 检查缓存是否有效
        assert converter._is_cache_valid(rate) is True
        
        # 检查缓存的汇率
        cached_rates = converter.get_cached_rates()
        assert "USDT" in cached_rates
        assert cached_rates["USDT"].rate == 1.0
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, converter):
        """测试清除缓存"""
        converter._rate_cache["TEST"] = Mock()
        
        converter.clear_cache()
        
        assert "TEST" not in converter._rate_cache
    
    @pytest.mark.asyncio
    async def test_error_handling(self, converter):
        """测试错误处理"""
        # 转换失败时应该返回0.0
        with patch.object(converter, '_extract_currencies', side_effect=ValueError("Invalid symbol")):
            result = await converter.convert_to_usd("INVALID", 50000, 10)
            assert result == 0.0
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_api_failure(self, mock_get, converter):
        """测试API失败处理"""
        # 模拟API失败
        mock_get.side_effect = Exception("API error")
        
        # 应该返回保守估计1.0
        result = await converter._get_usdt_usd_rate()
        assert result == 1.0
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试异步上下文管理器"""
        async with PriceConverter(cache_ttl=60) as converter:
            assert converter._session is not None
        
        # 退出后session应该关闭
        # 注意：这里我们无法直接检查session状态，因为它是私有的
        # 但在上下文管理器测试中，通常检查是否没有异常


class TestExchangeRate:
    """测试ExchangeRate数据模型"""
    
    def test_exchange_rate_creation(self):
        """测试创建汇率对象"""
        rate = ExchangeRate(
            symbol="USDT",
            rate=1.0,
            source="binance",
            timestamp=1234567890000,
            ttl=60
        )
        
        assert rate.symbol == "USDT"
        assert rate.rate == 1.0
        assert rate.source == "binance"
        assert rate.timestamp == 1234567890000
        assert rate.ttl == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
