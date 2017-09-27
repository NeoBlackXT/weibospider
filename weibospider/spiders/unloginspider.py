from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from weibospider.items import WeiboItem
from weibospider.items import UserItem
import random
from lxml import etree
import scrapy
import time
from urllib import parse
import json
import re


class UnloginCrawl(CrawlSpider):
    name = 'unlogincrawl'
    allowed_domains = ['weibo.com']
    category = 0
    page = 1
    end_page = 3

    def start_requests(self):
        while self.page <= self.end_page:
            _rnd = str(int(time.time())) + str(random.randint(100, 999))
            _url = 'http://weibo.com/a/aj/transform/loadingmoreunlogin?ajwvr=6&category=%d&page=%d&lefnav=0&__rnd=%s' \
                   % (self.category, self.page, _rnd)
            yield Request(_url)
            self.page += 1

    def parse(self, response):
        _json = str(eval(response.body.decode('utf-8')))
        _html = _json[_json.index("'data': '") + 9: _json.rindex("'}")].strip()
        _html = re.sub(r'\\\\"', '"', _html)
        _html = re.sub(r'\\\\/', '/', _html)
        _html = re.sub(r'\\r', '\r', _html)
        _html = re.sub(r'\\n', '\n', _html)
        _html = re.sub(r'\\t', '\t', _html)
        _html = re.sub(r"\\'", "'", _html)
        # 非utf-8字符，无法识别
        # _html = re.sub(r'\\x', r'\\\\x', _html)
        # _html = re.sub(r'(\\U\w{8})', r'\\\1', _html)
        html = etree.HTML(_html)

        div_list_a = html.xpath('//div[@class="UG_list_a"]')
        yield from self.parse_div_list_a(div_list_a)
        div_list_b = html.xpath('//div[@class="UG_list_b"]')
        yield from self.parse_div_list_b(div_list_b)
        div_list_v2 = html.xpath('//div[@class="UG_list_v2 clearfix"]')
        yield from self.parse_div_list_v2(div_list_v2)

    def parse_div_list_v2(self, div_list_v2):
        for i in div_list_v2:
            print('------------------')
            print(etree.tostring(i, encoding='utf-8', pretty_print=True).decode())
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0]
            weibo_item['nickname'] = \
                i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0]
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[
                    0]
            weibo_item['date'] = self.parse_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*')[0]
            weibo_item['content'] = self.parse_content_div(content_div)
            weibo_item['source_url'] = i.xpath('./div[@class="vid"]/@href')[0]
            weibo_item['image_urls'] = None
            action_data = i.xpath('./div[@class="vid"]/@action-data')[0]
            video_src = action_data[action_data.index('video_src=') + 10:action_data.index('&cover_img=')]
            print(video_src)
            weibo_item['video_url'] = parse.unquote(video_src)
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix subinfo_box_btm"]/span[@class="subinfo_rgt '
                'S_txt2"]/em[2]/text()')[0]
            weibo_item['forwarding_num'] = nums[-1]
            weibo_item['comment_num'] = nums[-2]
            weibo_item['praise_num'] = nums[-3]
            print(weibo_item)
            print('------------------')
            yield weibo_item

    def parse_div_list_b(self, div_list_b):
        for i in div_list_b:
            print('------------------')
            print(etree.tostring(i, encoding='utf-8', pretty_print=True).decode())
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0]
            weibo_item['nickname'] = \
                i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0]
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[
                    0]
            weibo_item['date'] = self.parse_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*')[0]
            weibo_item['content'] = self.parse_content_div(content_div)
            weibo_item['source_url'] = i.xpath('./@href')[0]
            weibo_item['image_urls'] = i.xpath('./div[1]/img/@src')
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em['
                '2]/text()')
            weibo_item['forwarding_num'] = nums[-1]
            weibo_item['comment_num'] = nums[-2]
            weibo_item['praise_num'] = nums[-3]
            print(weibo_item)
            print('------------------')
            yield weibo_item

    def parse_div_list_a(self, div_list_a):
        for i in div_list_a:
            print('------------------')
            print(etree.tostring(i, encoding='utf-8', pretty_print=True).decode())
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0]
            weibo_item['nickname'] = i.xpath('./div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0]
            date_str = i.xpath('./div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[0]
            weibo_item['date'] = self.parse_datestr(date_str)
            content_div = i.xpath('./*[1]/*')[0]
            weibo_item['content'] = self.parse_content_div(content_div)
            weibo_item['source_url'] = i.xpath('./@href')[0]
            weibo_item['image_urls'] = i.xpath('./div[@class="list_nod clearfix"]/div/img/@src')
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em[2]/text()')
            weibo_item['forwarding_num'] = nums[-1]
            weibo_item['comment_num'] = nums[-2]
            weibo_item['praise_num'] = nums[-3]
            print(weibo_item)
            print('------------------')
            yield weibo_item

    @staticmethod
    def parse_content_div(content_div):
        text = content_div.text if content_div.text is not None else ""
        for sub_ele in content_div.itertext():
            text += sub_ele
        return text

    @staticmethod
    def parse_datestr(date_str):
        pattern = re.compile(r'(?:(\d+)\w)?(\d+)\w(\d+)\w\s(\d+):(\d+)')
        match = pattern.match(date_str)
        if match:
            if match.group(1):
                time_tuple = time.strptime(date_str, "%Y年%m月%d日 %H:%M")
            else:
                time_tuple = time.strptime(date_str, "%m月%d日 %H:%M")
                time_tuple = time.struct_time((time.localtime().tm_year, time_tuple.tm_mon, time_tuple.tm_mday,
                                               time_tuple.tm_hour, time_tuple.tm_min, 0, -1, -1, -1))
        # 今天 H:M
        else:
            time_tuple = time.strptime(date_str, "今天 %H:%M")
            time_tuple = time.struct_time((time.localtime().tm_year, time.localtime().tm_mon,
                                           time.localtime().tm_mday, time_tuple.tm_hour, time_tuple.tm_min, 0, -1,
                                           -1, -1))
        return time.mktime(time_tuple)

    @staticmethod
    def jsonp_to_json(jsonp):
        patten = re.compile(r'{(?u).*}')
        result = re.search(patten, jsonp)
        if result:
            _json = result.group()
            _json = re.sub(r'\\\\"', r'\\"', _json)
            _json = re.sub(r'\\\\/', r'/', _json)
            # 非utf-8字符，无法识别
            _json = re.sub(r'\\x', r'\\\\x', _json)
            _json = re.sub(r'(\\U\w{8})', r'\\\1', _json)
            _json = re.sub(r"\\'", r"'", _json)
            json_load = json.loads(_json)
            return json_load
        else:
            raise RuntimeError('No json found!')