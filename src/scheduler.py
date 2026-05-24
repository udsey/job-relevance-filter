from datetime import date, datetime

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from src.run import run
from src.setup import config

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    cron = config.cron
    logger.info(f"Scheduler started, last run: {config.last_run}")
    scheduler.add_job(run, CronTrigger.from_crontab(cron))
    scheduler.start()

    cron_hour = int(cron.split()[1])
    last_run = config.last_run


    if last_run != date.today() and datetime.now().hour > cron_hour:
        logger.info("Missed today's run, executing now")
        scheduler.add_job(run, DateTrigger(run_date=datetime.now()))