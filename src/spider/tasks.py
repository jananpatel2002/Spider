from celery import Celery, Task
from spider.config import config
from spider.spider import Spider
import asyncio
import logging
from spider.plugin import PluginManager
from spider.plugins.entity_extraction import EntityExtractionPlugin

celery_app = Celery(
    'crawler',
    broker=config['celery']['broker_url'],
    backend=config['celery']['result_backend']
)

class CrawlTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 5}
    name = 'crawl_task'

@celery_app.task(bind=True, base=CrawlTask)
def crawl_task(self, url: str) -> str:
    """
    Celery task to initiate the crawling of a given URL.

    :param self: The task instance.
    :param url: The URL to crawl.
    :return: A confirmation message.
    """
    try:
        plugin_manager = PluginManager()
        entity_plugin = EntityExtractionPlugin()
        plugin_manager.register(entity_plugin)
        
        crawler = Spider(url, config, plugin_manager)
        asyncio.run(crawler.crawl())
        
        logging.info(f"Successfully crawled {url}")
        return f"Crawled {url}"
    except Exception as e:
        logging.exception(f"Error crawling {url}: {e}")
        raise self.retry(exc=e)
