
import sys
import logging

from tgscheduler import start_scheduler
from tgscheduler.scheduler import add_interval_task

from tg2app.scrapers.propertyinfo import ForeclosureScraper

log = logging.getLogger(__name__)


def testTask(email=None):
    log.info("testTask Called")

def schedule():
    """ start scheduler and setup recurring tasks """

    if "shell" in sys.argv: # disable cron in paster shell mode
        return

    log.info("Starting Scheduler Manager")
    start_scheduler()

    HOUR = 60*60

    add_interval_task(
        action=ForeclosureScraper().scrape_data,
        taskname="test1",
        interval=HOUR,
        initialdelay=0
    )
