from django_cron import cronScheduler, Job
from shuttletxt.views import get_shuttles
import logging

class log_out(Job):
    
    run_every = 2 # seconds
            
    def job(self):
        logging.info('hit server')
        get_shuttles()

cronScheduler.register(log_out)
