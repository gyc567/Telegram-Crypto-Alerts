"""
告警调度器
负责格式化并发送Telegram告警消息
"""
import asyncio
from typing import Optional, List, Callable, Dict
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LargeOrderAlert:
    """大额订单告警"""
    symbol: str
    direction: str  # "买入" or "卖出" or "双向"
    total_volume: float
    buy_volume: float
    sell_volume: float
    trade_count: int
    threshold_usd: float
    window_minutes: int
    timestamp: datetime
    exchange: str = "Binance"
    formatted_message: Optional[str] = None


class AlertDispatcher:
    """
    告警调度器
    
    负责：
    1. 格式化告警消息
    2. 发送Telegram消息
    3. 管理告警队列
    4. 速率限制
    5. 错误处理和重试
    """
    
    def __init__(
        self,
        telegram_bot=None,
        rate_limit_per_minute: int = 12
    ):
        self.telegram_bot = telegram_bot
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limiter = RateLimiter(max_calls=rate_limit_per_minute, period=60)
        
        # 告警队列
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.sending = False
        
        # 统计信息
        self.stats = {
            "alerts_received": 0,
            "alerts_sent": 0,
            "alerts_failed": 0,
            "alerts_queued": 0,
            "messages_sent": 0
        }
        
        logger.info(f"初始化告警调度器：{rate_limit_per_minute}条/分钟")
    
    async def dispatch_alert(self, alert: LargeOrderAlert) -> bool:
        """
        发送告警
        
        Args:
            alert: 告警对象
            
        Returns:
            bool: 是否成功发送
        """
        try:
            self.stats["alerts_received"] += 1
            
            # 格式化消息
            message = await self.format_message(alert)
            alert.formatted_message = message
            
            # 检查速率限制
            if not self.rate_limiter.try_acquire():
                logger.warning(f"速率限制触发，推送告警到队列")
                await self.alert_queue.put(alert)
                self.stats["alerts_queued"] += 1
                return False
            
            # 发送消息
            success = await self.send_message(message, alert)
            
            if success:
                self.stats["alerts_sent"] += 1
                logger.info(f"告警发送成功: {alert.symbol} ${alert.total_volume:,.0f}")
            else:
                self.stats["alerts_failed"] += 1
                logger.error(f"告警发送失败: {alert.symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送告警失败: {e}", exc_info=True)
            self.stats["alerts_failed"] += 1
            return False
    
    async def format_message(self, alert: LargeOrderAlert) -> str:
        """
        格式化告警消息
        
        Args:
            alert: 告警对象
            
        Returns:
            str: 格式化的消息
        """
        try:
            # 格式化时间
            time_str = alert.timestamp.strftime("%H:%M:%S")
            
            # 格式化金额（添加千分位分隔符）
            volume_str = f"${alert.total_volume:,.0f}"
            
            # 格式化交易对（转换为常见格式 BTC/USDT）
            symbol_display = self.format_symbol(alert.symbol)
            
            # 构建消息
            message = (
                f"🚨 大额主动{alert.direction}\n\n"
                f"📈 交易对: {symbol_display}\n"
                f"💰 金额: {volume_str}\n"
                f"⚖️ 方向: {alert.direction}\n"
                f"🕐 时间: {time_str}\n"
                f"🏦 交易所: {alert.exchange}\n\n"
                f"📊 详情:\n"
                f"  • 买入量: ${alert.buy_volume:,.0f}\n"
                f"  • 卖出量: ${alert.sell_volume:,.0f}\n"
                f"  • 交易笔数: {alert.trade_count}\n"
                f"  • 窗口: {alert.window_minutes}分钟\n"
                f"  • 阈值: ${alert.threshold_usd:,.0f}"
            )
            
            return message
            
        except Exception as e:
            logger.error(f"格式化消息失败: {e}", exc_info=True)
            return f"大额订单告警: {alert.symbol} ${alert.total_volume:,.0f}"
    
    def format_symbol(self, symbol: str) -> str:
        """
        格式化交易对显示
        
        Args:
            symbol: 原始交易对（e.g., "BTCUSDT"）
            
        Returns:
            str: 格式化后的交易对（e.g., "BTC/USDT"）
        """
        try:
            # 移除连字符
            symbol = symbol.replace("-", "")
            
            # 尝试分离基础货币和计价货币
            for length in [4, 5, 6]:
                if len(symbol) >= length:
                    base = symbol[:-length]
                    quote = symbol[-length:]
                    return f"{base}/{quote}"
            
            # 如果无法分离，使用原始值
            return symbol
            
        except Exception as e:
            logger.error(f"格式化交易对失败: {e}", exc_info=True)
            return symbol
    
    async def send_message(self, message: str, alert: LargeOrderAlert) -> bool:
        """
        发送Telegram消息
        
        Args:
            message: 消息内容
            alert: 告警对象
            
        Returns:
            bool: 是否成功发送
        """
        try:
            if not self.telegram_bot:
                logger.warning("未配置Telegram Bot，模拟发送")
                self.stats["messages_sent"] += 1
                print(f"\n📢 告警消息:\n{message}\n")
                return True
            
            # 发送到Telegram
            # TODO: 替换为实际的发送逻辑
            # self.telegram_bot.send_message(chat_id, message)
            
            self.stats["messages_sent"] += 1
            logger.info(f"Telegram消息已发送")
            return True
            
        except Exception as e:
            logger.error(f"发送Telegram消息失败: {e}", exc_info=True)
            return False
    
    async def start_queue_processor(self) -> None:
        """启动队列处理器"""
        if self.sending:
            return
        
        self.sending = True
        asyncio.create_task(self._process_queue())
        logger.info("告警队列处理器已启动")
    
    async def stop_queue_processor(self) -> None:
        """停止队列处理器"""
        self.sending = False
        logger.info("告警队列处理器已停止")
    
    async def _process_queue(self) -> None:
        """处理告警队列"""
        while self.sending:
            try:
                # 从队列获取告警
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                
                # 等待速率限制
                if not self.rate_limiter.try_acquire():
                    # 重新放回队列末尾
                    await self.alert_queue.put(alert)
                    await asyncio.sleep(5)  # 等待5秒再试
                    continue
                
                # 发送告警
                success = await self.send_message(
                    alert.formatted_message or await self.format_message(alert),
                    alert
                )
                
                if success:
                    self.stats["alerts_sent"] += 1
                else:
                    self.stats["alerts_failed"] += 1
                    # 失败后重试一次
                    await asyncio.sleep(10)
                    await self.alert_queue.put(alert)
                
            except asyncio.TimeoutError:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"处理队列错误: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.alert_queue.qsize()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "queue_size": self.get_queue_size(),
            "rate_limit_per_minute": self.rate_limit_per_minute
        }


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def try_acquire(self) -> bool:
        """
        尝试获取令牌
        
        Returns:
            bool: 是否成功获取
        """
        async with self.lock:
            now = datetime.now()
            
            # 清理过期调用
            self.calls = [call_time for call_time in self.calls 
                         if (now - call_time).total_seconds() < self.period]
            
            # 检查是否达到限制
            if len(self.calls) >= self.max_calls:
                return False
            
            # 记录此次调用
            self.calls.append(now)
            return True
    
    def get_remaining_calls(self) -> int:
        """获取剩余调用次数"""
        now = datetime.now()
        recent_calls = sum(1 for call_time in self.calls 
                          if (now - call_time).total_seconds() < self.period)
        return max(0, self.max_calls - recent_calls)
    
    def get_reset_time(self) -> Optional[datetime]:
        """获取重置时间"""
        if not self.calls:
            return None
        return min(self.calls) + timedelta(seconds=self.period)
