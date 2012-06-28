from django_cron import cronScheduler, Job
import logging

class update_shuttles(Job):
    """
    Keep live track of shuttles
    """
    # run every 10 seconds
    run_every = 10
            
    def job(self):
        logging.debug('yes1!!!#131!!')

cronScheduler.register(update_shuttles)
