from tgscheduler import start_scheduler
from tgscheduler.scheduler import add_interval_task, add_weekday_task, add_single_task
import sys
import logging
log = logging.getLogger(__name__)

def testTask(email=None):
    log.info("testTask Called")

def schedule():
    """ start scheduler and setup recurring tasks """

    if "shell" in sys.argv: # disable cron in paster shell mode
        return

    log.info("Starting Scheduler Manager")
    start_scheduler()

    add_interval_task(action=testTask, taskname="test1",
                      interval=5, initialdelay=5)
