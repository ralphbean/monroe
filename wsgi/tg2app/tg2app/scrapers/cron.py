
import sys
import logging

from tgscheduler import start_scheduler
from tgscheduler.scheduler import add_interval_task, add_single_task

from tg2app.scrapers.propertyinfo import ForeclosureScraper

log = logging.getLogger(__name__)


def testTask(email=None):
    log.info("testTask Called")

def schedule():
    """ start scheduler and setup recurring tasks """

    if "shell" in sys.argv: # disable cron in paster shell mode
        return

    ONE_DAY = 60*60*24

#    add_single_task(
#        action=ForeclosureScraper().go_way_back,
#        taskname="gowayback",
#        initialdelay=0,
#    )
    add_interval_task(
        action=ForeclosureScraper().scrape_data,
        taskname="test1",
        interval=ONE_DAY,
        initialdelay=5
    )

    log.info("Starting Scheduler Manager")
    start_scheduler()

