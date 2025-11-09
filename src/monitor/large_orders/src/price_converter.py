"""
USD转换策略实现
支持多种稳定币和计价货币的USD转换
"""
import asyncio
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ExchangeRate:
    """汇率数据"""
    symbol: str  # 交易对符号，如"USDT"
    rate: float  # 对USD的汇率
    source: str  # 数据来源：binance, coingecko, etc.
    timestamp: int  # 毫秒时间戳
    ttl: int  # 缓存时间（秒）


class PriceConverter:
    """
    USD价格转换器
    
    支持以下转换策略：
    1. 稳定币：USDT, BUSD, USDC -> 1:1转换
    2. USDT交易对：XXXUSDT -> 直接使用价格
    3. 跨币种转换：BTC/ETH -> 通过USDT转换
    4. 实时汇率：API获取最新汇率
    """
    
    def __init__(self, cache_ttl: int = 60):
        self.cache_ttl = cache_ttl
        self._rate_cache: Dict[str, ExchangeRate] = {}
        self._cache_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        
        # 稳定币列表（1:1兑换USD）
        self._stable_coins = {
            "USDT", "BUSD", "USDC", "DAI", "TUSD", "USDP", "FDUSD"
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            headers={'User-Agent': 'Telegram-Crypto-Alerts/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._session:
            await self._session.close()
    
    def _is_stable_coin(self, symbol: str) -> bool:
        """检查是否为稳定币"""
        return symbol.upper() in self._stable_coins
    
    def _normalize_symbol(self, symbol: str) -> str:
        """标准化交易对符号（移除连字符，转换为大写）"""
        return symbol.replace("-", "").upper()
    
    async def convert_to_usd(self, symbol: str, price: float, quantity: float) -> float:
        """
        将交易价值转换为USD
        
        Args:
            symbol: 交易对符号（支持多种格式）
                   - Binance格式：BTCUSDT, ETHUSDT
                   - 通用格式：BTC/USDT, BTC-USDT
            price: 交易价格
            quantity: 交易数量
            
        Returns:
            float: USD价值
            
        Examples:
            >>> converter.convert_to_usd("BTCUSDT", 50000, 1)
            50000.0  # BTC/USDT -> $50,000
            
            >>> converter.convert_to_usd("BTC/USDC", 50000, 1)
            50000.0  # BTC/USDC -> $50,000
            
            >>> converter.convert_to_usd("ETH/BTC", 20, 100)  
            1000000.0  # ETH/BTC -> 100 ETH * $5,000/ETH
        """
        try:
            # 标准化符号
            normalized = self._normalize_symbol(symbol)
            
            # 提取基础货币和计价货币
            base_coin, quote_coin = self._extract_currencies(normalized)
            
            # 情况1: 稳定币交易对（USDT, BUSD, USDC等）
            if self._is_stable_coin(quote_coin):
                # 直接使用价格 * 数量
                return price * quantity
            
            # 情况2: USDT作为计价货币（通过API获取USDT/USD汇率）
            elif quote_coin == "USDT":
                # USDT通常1:1挂钩美元
                # 但为精确性，仍获取实时汇率
                usdt_rate = await self._get_usdt_usd_rate()
                return price * quantity * usdt_rate
            
            # 情况3: 其他交易对（如ETH/BTC）
            else:
                # 需要通过中间货币转换
                # 步骤1: 将基础货币转换为USDT
                base_to_usdt = await self._get_coin_usdt_rate(base_coin)
                
                # 步骤2: 将USDT转换为USD
                usdt_to_usd = await self._get_usdt_usd_rate()
                
                # 步骤3: 计算总价值
                # base_value_usdt = quantity * price * base_to_usdt
                # total_value_usd = base_value_usdt * usdt_to_usd
                return quantity * price * base_to_usdt * usdt_to_usd
                
        except Exception as e:
            logger.error(f"转换失败: {symbol} @ {price} * {quantity} - {e}")
            # 转换失败时返回0，触发告警
            return 0.0
    
    def _extract_currencies(self, symbol: str) -> Tuple[str, str]:
        """
        提取交易对的基础货币和计价货币
        
        Args:
            symbol: 标准化后的交易对符号（如"ETHUSDT"）
            
        Returns:
            Tuple[str, str]: (基础货币, 计价货币)
            
        Examples:
            >>> self._extract_currencies("BTCUSDT")
            ("BTC", "USDT")
            
            >>> self._extract_currencies("ETHBTC")
            ("ETH", "BTC")
        """
        # 常见稳定币长度列表（从长到短排序，避免误匹配）
        stable_coin_lengths = sorted([
            len(coin) for coin in self._stable_coins
        ], reverse=True)
        
        for length in stable_coin_lengths:
            if symbol.endswith(self._normalize_symbol(length)):
                base_coin = symbol[:-length]
                quote_coin = symbol[-length:]
                return base_coin, quote_coin
        
        # 如果没有匹配到稳定币，假设是3-4字符的计价货币
        # 例如：BTCETH, ETHADA等
        if len(symbol) == 6:
            base_coin = symbol[:3]
            quote_coin = symbol[3:]
            return base_coin, quote_coin
        elif len(symbol) == 7:
            # 可能是4+3的组合，如BNBUSDT
            if symbol.endswith("USDT"):
                return symbol[:-4], "USDT"
            else:
                return symbol[:3], symbol[3:]
        else:
            raise ValueError(f"无法解析交易对符号: {symbol}")
    
    async def _get_usdt_usd_rate(self) -> float:
        """获取USDT对USD的汇率"""
        async with self._cache_lock:
            cache_key = "USDT"
            
            if cache_key in self._rate_cache:
                rate = self._rate_cache[cache_key]
                if self._is_cache_valid(rate):
                    return rate.rate
            
            # 从币安API获取USDT价格
            try:
                if not self._session:
                    self._session = aiohttp.ClientSession()
                
                url = "https://api.binance.com/api/v3/ticker/price"
                params = {"symbol": "USDTBUSD"}  # BUSD与USD挂钩
                
                async with self._session.get(url, params=params) as resp:
                    data = await resp.json()
                    rate = float(data["price"])
                
                # 更新缓存
                self._rate_cache[cache_key] = ExchangeRate(
                    symbol="USDT",
                    rate=rate,
                    source="binance",
                    timestamp=int(asyncio.get_event_loop().time() * 1000),
                    ttl=self.cache_ttl
                )
                
                logger.debug(f"获取USDT/USD汇率: {rate}")
                return rate
                
            except Exception as e:
                logger.error(f"获取USDT/USD汇率失败: {e}")
                # 如果获取失败，返回保守估计1.0
                return 1.0
    
    async def _get_coin_usdt_rate(self, coin: str) -> float:
        """获取货币对USDT的汇率"""
        async with self._cache_lock:
            cache_key = f"{coin}USDT"
            
            if cache_key in self._rate_cache:
                rate = self._rate_cache[cache_key]
                if self._is_cache_valid(rate):
                    return rate.rate
            
            # 如果是稳定币，直接返回1.0
            if self._is_stable_coin(coin):
                return 1.0
            
            # 从币安API获取价格
            try:
                if not self._session:
                    self._session = aiohttp.ClientSession()
                
                url = "https://api.binance.com/api/v3/ticker/price"
                params = {"symbol": f"{coin}USDT"}
                
                async with self._session.get(url, params=params) as resp:
                    data = await resp.json()
                    rate = float(data["price"])
                
                # 更新缓存
                self._rate_cache[cache_key] = ExchangeRate(
                    symbol=cache_key,
                    rate=rate,
                    source="binance",
                    timestamp=int(asyncio.get_event_loop().time() * 1000),
                    ttl=self.cache_ttl
                )
                
                logger.debug(f"获取{coin}/USDT汇率: {rate}")
                return rate
                
            except Exception as e:
                logger.error(f"获取{coin}/USDT汇率失败: {e}")
                return 0.0
    
    def _is_cache_valid(self, rate: ExchangeRate) -> bool:
        """检查缓存是否仍然有效"""
        now = int(asyncio.get_event_loop().time() * 1000)
        return (now - rate.timestamp) < (rate.ttl * 1000)
    
    def clear_cache(self) -> None:
        """清除汇率缓存"""
        self._rate_cache.clear()
        logger.info("清除汇率缓存")
    
    def get_cached_rates(self) -> Dict[str, ExchangeRate]:
        """获取缓存的汇率"""
        return self._rate_cache.copy()
    
    async def batch_convert(self, trades: list) -> list:
        """
        批量转换交易价值
        
        Args:
            trades: 交易列表，每个元素为(symbol, price, quantity)
            
        Returns:
            list: 转换后的USD价值列表
        """
        tasks = [
            self.convert_to_usd(symbol, price, quantity)
            for symbol, price, quantity in trades
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 转换失败时返回0
        return [
            result if isinstance(result, (int, float)) else 0.0
            for result in results
        ]


# 使用示例
"""
# 1. 创建转换器实例
async with PriceConverter(cache_ttl=60) as converter:
    # 2. 单个转换
    usd_value = await converter.convert_to_usd("BTCUSDT", 50000, 10)
    print(f"50000 USDT的BTC价值: ${usd_value:,.2f}")
    
    # 3. 批量转换
    trades = [
        ("BTCUSDT", 50000, 10),
        ("ETHUSDT", 3000, 100),
        ("BTC/ETH", 15, 50)
    ]
    usd_values = await converter.batch_convert(trades)
    print(f"批量转换结果: {usd_values}")
"""
