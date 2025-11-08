import threading
from os import getenv
from time import sleep

from .alert_processes import CEXAlertProcess, TechnicalAlertProcess
from .config import (
    LARGE_ORDER_MONITOR_ENABLED,
    LARGE_ORDER_THRESHOLD_USDT,
    LARGE_ORDER_TIME_WINDOW_MINUTES,
    LARGE_ORDER_COOLDOWN_MINUTES,
    LARGE_ORDER_MONITORED_SYMBOLS,
    LARGE_ORDER_DATA_PATH,
)
from .monitor.large_orders import LargeOrderMonitor
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
        large_order_monitor = LargeOrderMonitor(
            telegram_bot=telegram_bot,
            symbols=LARGE_ORDER_MONITORED_SYMBOLS,
            threshold_usdt=LARGE_ORDER_THRESHOLD_USDT,
            time_window_minutes=LARGE_ORDER_TIME_WINDOW_MINUTES,
            cooldown_minutes=LARGE_ORDER_COOLDOWN_MINUTES,
            storage_path=LARGE_ORDER_DATA_PATH
        )
        large_order_monitor.start()
    else:
        large_order_monitor = None
        logger.info("Large Order Monitor is disabled")

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
