# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random

from scrapy import signals
from scrapy_redis import get_redis_from_settings

from weibospider.utils import IPProxyUtil


class RandomUserAgentMiddleware(object):
    def __init__(self, ualist):
        self.ualist = ualist

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('USER_AGENT_POOL'))

    def process_request(self, request, spider):
        ua = random.choice(self.ualist)
        request.headers.setdefault(b'User-Agent', ua)
        spider.log('User-Agent: %s' % ua)


class RandomProxyMiddleware(object):
    def __init__(self, settings):
        self.settings = settings
        self.server = get_redis_from_settings(settings)
        # 默认代理池URL为http://127.0.0.1:5010
        self.proxy_pool_url = settings.get('PROXY_POOL_URL', 'http://127.0.0.1:5010')
        # 默认请求失败5次视为代理失效
        self.proxy_times_banned_max = settings.getint('PROXY_TIMES_BANNED_MAX', 5)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if request.meta.get('retry_times', 0) > 0:
            banned_proxy = request.meta.get('proxy', None)
            if banned_proxy:
                name = '%s:bannedproxy' % spider.name
                # hget返回为bytes
                times = int(self.server.hget(name, banned_proxy) or 0)
                if times >= self.proxy_times_banned_max:
                    # 不删除redis中失效的代理，如果代理池中再次出现原来已失效的代理可再次过滤
                    # self.server.hdel(name, banned_proxy)
                    IPProxyUtil.delete_proxy(banned_proxy, self.proxy_pool_url)
                    spider.log('删除失效代理: %s' % banned_proxy)
                else:
                    self.server.hset(name, banned_proxy, times + 1)
        while True:
            proxy = IPProxyUtil.get_proxy(self.proxy_pool_url)
            times = int(self.server.hget(name, proxy) or 0)
            if times < self.proxy_times_banned_max:
                request.meta['proxy'] = proxy
                spider.log('proxy: %s' % proxy)
                break


class WeiboSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
