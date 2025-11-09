import threading
from os import getenv
from time import sleep
import asyncio

from .alert_processes import CEXAlertProcess, TechnicalAlertProcess
from .alert_processes.large_order import LargeOrderMonitorProcess
from .alert_processes.taker_order import TakerOrderAlertProcess
from .config import (
    LARGE_ORDER_MONITOR_ENABLED,
    LARGE_ORDER_THRESHOLD_USDT,
    LARGE_ORDER_TIME_WINDOW_MINUTES,
    LARGE_ORDER_COOLDOWN_MINUTES,
    LARGE_ORDER_MONITORED_SYMBOLS,
    LARGE_ORDER_DATA_PATH,
    TAKER_ORDER_MONITOR_ENABLED,
)
from .telegram import TelegramBot
from .user_configuration import get_whitelist
from .utils import handle_env
from .indicators import TaapiioProcess
from .logger import logger
from .setup import do_setup

if __name__ == "__main__":
    # Process environment variables
    handle_env()

    # Do the setup process if the bot is not set up
    if len(get_whitelist()) == 0:
        do_setup()
        logger.info("Waiting for initialization ...")
        sleep(5)

    taapiio_process = None
    if getenv("TAAPIIO_APIKEY"):
        # Create global Taapi.io process for the aggregator and telegram bot to sync calls
        taapiio_process = TaapiioProcess(taapiio_apikey=getenv("TAAPIIO_APIKEY"))

    # Create the Telegram bot to listen to commands and send messages
    telegram_bot = TelegramBot(
        bot_token=getenv("TELEGRAM_BOT_TOKEN"), taapiio_process=taapiio_process
    )

    # Run the TG bot in a daemon thread
    threading.Thread(target=telegram_bot.run, daemon=True).start()

    # Initialize and start Large Order Monitor
    if LARGE_ORDER_MONITOR_ENABLED:
        logger.info("Initializing Large Order Monitor...")
        large_order_monitor = LargeOrderMonitorProcess(
            telegram_bot=telegram_bot,
            symbols=LARGE_ORDER_MONITORED_SYMBOLS,
            threshold_usd=LARGE_ORDER_THRESHOLD_USDT,
            window_minutes=LARGE_ORDER_TIME_WINDOW_MINUTES,
            cooldown_minutes=LARGE_ORDER_COOLDOWN_MINUTES
        )
        # Run in daemon thread
        threading.Thread(target=asyncio.run, args=(large_order_monitor.run(),), daemon=True).start()
        logger.info("Large Order Monitor started")
    else:
        large_order_monitor = None
        logger.info("Large Order Monitor is disabled")

    # Initialize and start Taker Order Monitor
    if TAKER_ORDER_MONITOR_ENABLED:
        logger.info("Initializing Taker Order Monitor...")
        taker_order_monitor = TakerOrderAlertProcess(bot=telegram_bot)
        # Run in daemon thread
        threading.Thread(target=taker_order_monitor.run, daemon=True).start()
        logger.info("Taker Order Monitor started")
    else:
        logger.info("Taker Order Monitor is disabled")

    # Run the CEXAlertProcess in a daemon thread
    threading.Thread(
        target=CEXAlertProcess(telegram_bot=telegram_bot).run, daemon=True
    ).start()

    if taapiio_process:
        # Run the Taapi.io process in a daemon thread
        threading.Thread(target=taapiio_process.run, daemon=True).start()

        # Run the TechnicalAlertProcess in a daemon thread
        threading.Thread(
            target=TechnicalAlertProcess(telegram_bot=telegram_bot).run, daemon=True
        ).start()

    # Keep the main thread alive to listen to interrupt
    logger.info("Bot started - use Ctrl+C to stop the bot.")
    while True:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
            exit(1)
