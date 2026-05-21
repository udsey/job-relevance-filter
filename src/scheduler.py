from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.run import run
from src.setup import config

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    cron = config.cron
    scheduler.add_job(run, CronTrigger.from_crontab(cron))
    scheduler.start()
