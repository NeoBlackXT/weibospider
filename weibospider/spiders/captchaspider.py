import scrapy
from scrapy import Request
from scrapy.spiders import CrawlSpider, Spider


class CaptchaSpider(Spider):
    name = 'captchacrawl'
    allowed_domains = ['sina.com.cn']

    def start_requests(self):
        url = 'http://login.sina.com.cn/cgi/pin.php'
        for i in range(6000):
            yield Request(url=url, meta={'ord': i, 'max_retry_times': 20}, dont_filter=True)

    def parse(self, response):
        order = response.request.meta['ord']
        path = 'D:\\captcha\\'
        with open('{}{:04}.png'.format(path, order), 'wb') as f:
            f.write(response.body)
            f.close()
