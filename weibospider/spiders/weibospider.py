# -*- coding: utf-8 -*-
import scrapy
from datetime import date
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from weibospider.items import WeiboItem
import json
import re


class WeiboCrawl(CrawlSpider):
    name = 'weibocrawl'
    allowed_domains = ['weibo.com', 'passport.weibo.com', 'data.weibo.com', 'photo.weibo.com', 't.cn']
    start_urls = ['http://weibo.com/login.php']

    # rules = (
    #     Rule(link_extractor=LinkExtractor(allow='.*'), callback='parse_item'),
    # )

    # r'/a/aj/transform/'

    def parse_item(response):
        str0 = response.body.decode('utf-8')
        print(str0)
        item = WeiboItem()
        item['username'] = ''
        item['content'] = str0
        date0 = date()
        item['date'] = date0.ctime()
        item['date'] = 'r'
        return item

    def parse_start_url(self, response):
        _str = response.body.decode('utf-8')
        # print (_str)

        _text = response.xpath('/html/script[@charset="utf-8"]/text()').extract()

        def jsonp_to_json(jsonp):
            jsonp = repr(jsonp)
            # patten = re.compile(ur'{(?:.*[\u4E00-\u9FA5]*.*)*}')
            patten = re.compile(r'{(?u).*}')
            result = re.search(patten, jsonp)
            if result:
                _json = result.group()
                _json = re.sub(r'\\\\"', r'\\"', _json)
                _json = re.sub(r'\\\\/', r'/', _json)
                # 非utf-8字符，无法识别
                _json = re.sub(r'\\x', r'\\\\x', _json)
                _json = re.sub(r'(\\U\w{8})', r'\\\1', _json)
                # _json = re.sub(r"\\\\n", r"\n", _json)
                # _json = re.sub(r"\\\\r", r"\r", _json)
                # _json = re.sub(r"\\\\t", r"\t", _json)
                _json = re.sub(r"\\'", r"'", _json)
                json_load = json.loads(_json)
                return json_load
            else:
                raise RuntimeError('No json found!')

        for i in _text:
            _json1 = jsonp_to_json(i)
            if 'html' in _json1 and _json1['html'] != '':
                print('_________________________________')
                print(_json1.keys())
                if 'domid' in _json1:
                    print('domid:' + _json1['domid'])
                if 'pid' in _json1:
                    print('pid:' + _json1['pid'])
                if 'ns' in _json1:
                    print('ns:' + _json1['ns'])
                print('html:' + _json1['html'])
                print('_________________________________')
