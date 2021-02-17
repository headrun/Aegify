import os
import time

import scrapyd_api

class Launcher:
    DEFAULT_CRAWL_TIMEOUT_SECONDS = 60

    def __init__(self):
        pass

    def init(self, project, spider, settings, item_model_path, keys, crawl_timeout):
        self.server = os.environ.get('SCRAPYD_SERVER', 'http://localhost:6800')
        self.project = project
        self.spider = spider
        self.settings = settings
        self.item_model_path = item_model_path
        self.keys = keys
        self.crawl_timeout = crawl_timeout

    def crawl(self):
        api = scrapyd_api.ScrapydAPI(self.server)
        job = api.schedule(self.project, self.spider, settings=self.settings, item_model=self.item_model_path, keys=self.keys)

        start_time = time.time()
        sleep_time = max(int(self.crawl_timeout / 10), 1)

        while time.time() < start_time + self.crawl_timeout:
            time.sleep(sleep_time)
            status = api.job_status(self.project, job)
            if scrapyd_api.FINISHED == status:
                break
