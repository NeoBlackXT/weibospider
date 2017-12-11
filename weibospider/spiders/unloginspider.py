import logging
import traceback
import random
import time
import json
import re
from urllib import parse

import scrapy
import sys
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Spider
from weibospider.items import WeiboItem, UserItem
from lxml import etree


class UnloginCrawl(CrawlSpider):
    name = 'unlogincrawl'
    allowed_domains = ['weibo.com']

    # 爬取分类
    category = 0
    # 爬取起始页
    page = 1
    # 爬取终止页
    end_page = sys.maxsize

    def start_requests(self):
        while self.page <= self.end_page:
            _rnd = str(int(time.time())) + str(random.randint(100, 999))
            _url = 'https://weibo.com/a/aj/transform/loadingmoreunlogin?ajwvr=6&category=%d&page=%d&lefnav=0&__rnd=%s' \
                   % (self.category, self.page, _rnd)
            yield Request(_url)
            self.page += 1

    def parse_start_url(self, response):
        # _json = response.body.decode('utf-8')
        _json = response.text
        _html = self.jsonp_to_html(_json, 'data')

        html = etree.HTML(_html)

        div_list_a = html.xpath('//div[@class="UG_list_a"]')
        yield from self.parse_div_list_a(div_list_a)
        div_list_b = html.xpath('//div[@class="UG_list_b"]')
        yield from self.parse_div_list_b(div_list_b)
        div_list_v2 = html.xpath('//div[@class="UG_list_v2 clearfix"]')
        yield from self.parse_div_list_v2(div_list_v2)

        for i in div_list_a:
            user_home_url = 'https://weibo.com' + i.xpath('./div[@class="subinfo_box clearfix"]/a[2]/@href')[0]
            yield Request(user_home_url, callback=self.parse_user, cookies={'SUB': 'SUB'})

        for i in div_list_b:
            user_home_url = 'https://weibo.com' + \
                            i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/@href')[0]
            yield Request(user_home_url, callback=self.parse_user, cookies={'SUB': 'SUB'})
        for i in div_list_v2:
            user_home_url = 'https:' + i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/@href')[
                0]
            yield Request(user_home_url, callback=self.parse_user, cookies={'SUB': 'SUB'})

    def parse_div_list_a(self, div_list_a):
        for i in div_list_a:
            Spider.log(self, '-' * 10)
            Spider.log(self, etree.tostring(i, encoding='utf-8', pretty_print=True))
            weibo_item = WeiboItem()
            weibo_item['mid'] = str(i.xpath('./@mid')[0])
            weibo_item['nickname'] = str(i.xpath('./div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0])
            date_str = i.xpath('./div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[0]
            weibo_item['date'] = self.process_datestr(date_str)
            content_div = i.xpath('./*[1]/*')[0]
            weibo_item['content'] = self.process_content(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./@href')[0]
            weibo_item['image_urls'] = [str(u) for u in i.xpath('./div[@class="list_nod clearfix"]/div/img/@src')]
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em[2]/text()')
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            Spider.log(self,'-' * 10)
            yield weibo_item

    def parse_div_list_b(self, div_list_b):
        for i in div_list_b:
            Spider.log(self, '-' * 10)
            Spider.log(self, etree.tostring(i, encoding='utf-8', pretty_print=True).decode())
            weibo_item = WeiboItem()
            weibo_item['mid'] = str(i.xpath('./@mid')[0])
            weibo_item['nickname'] = \
                str(i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0])
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[
                    0]
            weibo_item['date'] = self.process_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*')[0]
            weibo_item['content'] = self.process_content(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./@href')[0]
            weibo_item['image_urls'] = [str(u) for u in i.xpath('./div[1]/img/@src')]
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em['
                '2]/text()')
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            Spider.log(self, '-' * 10)
            yield weibo_item

    def parse_div_list_v2(self, div_list_v2):
        for i in div_list_v2:
            Spider.log(self, '-' * 10)
            Spider.log(self, etree.tostring(i, encoding='utf-8', pretty_print=True).decode())
            weibo_item = WeiboItem()
            weibo_item['mid'] = str(i.xpath('./@mid')[0])
            weibo_item['nickname'] = \
                str(i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0])
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/'
                    'text()')[0]
            weibo_item['date'] = self.process_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*')[0]
            weibo_item['content'] = self.process_content(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./div[@class="vid"]/@href')[0]
            weibo_item['image_urls'] = None
            action_data = i.xpath('./div[@class="vid"]/@action-data')[0]
            video_src = action_data[action_data.index('video_src=') + 10:action_data.index('&cover_img=')]
            weibo_item['video_url'] = parse.unquote(video_src)
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix subinfo_box_btm"]/span[@class="subinfo_rgt '
                'S_txt2"]/em[2]/text()')[0]
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            Spider.log(self, '-' * 10)
            yield weibo_item

    def parse_user(self, response):
        Spider.log(self, "%s\r\nurl: %s" % (response.text, response.request.url))
        Spider.log(self, 'parse_user start')
        try:
            user_item = UserItem()
            _html = response.text
            _json = response.xpath(
                '''/html/script[starts-with(text(),'FM.view({"ns":"pl.header.preloginHead.index",'''
                '''"domid":"Pl_Official_Headerv6') or starts-with(text(),'FM.view({"ns":"pl.header.head.index",'''
                '''"domid":"Pl_Official_Headerv6')]/text()''').extract()[0]
            _html = self.jsonp_to_html(_json)
            _html_ele = etree.HTML(_html)
            user_item['nickname'] = str(_html_ele.xpath('./descendant::h1[@class="username"]/text()')[0])
            Spider.log(self, _html, level=logging.INFO)
            gender_class = \
                _html_ele.xpath('./descendant::i[@class="W_icon icon_pf_female" or @class="W_icon icon_pf_male"]/'
                                '@class')[0]
            user_item['gender'] = gender_class[gender_class.rindex('_') + 1:]
            # vip6的样式W_icon icon_member6
            user_item['is_vip'] = len(_html_ele.xpath('./descendant::a[@href="http://vip.weibo.com/personal?'
                                                      'from=main"]/em[not(contains(@class,"icon_member_dis"))]')) > 0
            user_item['verified'] = len(_html_ele.xpath('./descendant::div[@class="pf_photo"]/a')) > 0
            user_item['introduction'] = _html_ele.xpath('./descendant::div[@class="pf_intro" and 2]/text()')[0].strip()
            _json = response.xpath(
                '''/html/script[starts-with(text(),'FM.view({"ns":"pl.content.homeFeed.index",'''
                '''"domid":"Pl_Core_UserInfo')]/text()''').extract()[0]
            _html = self.jsonp_to_html(_json)
            _html_ele = etree.HTML(_html)
            level_text = _html_ele.xpath('./descendant::a/span/text()')[0]
            user_item['level'] = int(level_text[level_text.index('.') + 1:])
            _json = response.xpath('''/html/script[starts-with(text(),'FM.view({"ns":"","domid":'''
                                   '''"Pl_Core_T8CustomTriColumn')]''').extract()[0]
            _html = self.jsonp_to_html(_json)
            _html_ele = etree.HTML(_html)
            nums = _html_ele.xpath('./descendant::td/descendant::strong/text()')
            user_item['concern_num'] = int(nums[0])
            user_item['fans_num'] = int(nums[1])
            user_item['weibo_num'] = int(nums[2])
            user_item['home_url'] = response.request.url[
                                    :response.request.url.index('?') if response.request.url.count('?') else None]
            Spider.log(self, _html, level=logging.INFO)
            Spider.log(self, 'user_item: %s' % user_item, level=logging.INFO)
            return user_item
        except:
            Spider.log(self, "%s\n%s" % (response.url, _html), logging.ERROR)
            traceback.print_exc()
            input('按任意键继续')

    @staticmethod
    def process_content(content):
        text = content.text if content.text is not None else ""
        for sub_ele in content.itertext():
            text += sub_ele
        return text

    @staticmethod
    def process_datestr(date_str):
        pattern = re.compile(r'(?:(\d+)年)?(\d+)月(\d+)日\s(\d+):(\d+)')
        match = pattern.match(date_str)
        if match:
            if match.group(1):
                time_tuple = time.strptime(date_str, "%Y年%m月%d日 %H:%M")
            else:
                time_tuple = time.strptime(date_str, "%m月%d日 %H:%M")
                time_tuple = time.struct_time((time.localtime().tm_year, time_tuple.tm_mon, time_tuple.tm_mday,
                                               time_tuple.tm_hour, time_tuple.tm_min, 0, -1, -1, -1))
        # 今天 H:M
        elif re.match(r'今天\s\d+:\d+', date_str):
            time_tuple = time.strptime(date_str, "今天 %H:%M")
            time_tuple = time.struct_time((time.localtime().tm_year, time.localtime().tm_mon,
                                           time.localtime().tm_mday, time_tuple.tm_hour, time_tuple.tm_min, 0, -1,
                                           -1, -1))

        # X分钟前
        else:
            match = re.match(r'(\d+)分钟前', date_str)
            if match.group(1):
                passmin = int(match.group(1))
                time_tuple = time.struct_time((time.localtime().tm_year, time.localtime().tm_mon,
                                               time.localtime().tm_mday, time.localtime().tm_hour,
                                               time.localtime().tm_min - passmin, 0, -1,
                                               -1, -1))
            elif re.match(r'\d+秒前', date_str):
                time_tuple = time.struct_time((time.localtime().tm_year, time.localtime().tm_mon,
                                               time.localtime().tm_mday, time.localtime().tm_hour,
                                               time.localtime().tm_min, 0, -1, -1, -1))
            else:
                raise RuntimeError('cant process this date_str: %s' % date_str)

        return time.mktime(time_tuple)

    @staticmethod
    def jsonp_to_dict(jsonp):
        """把jsonp中的json转为dict"""
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

    @staticmethod
    def jsonp_to_html(jsonp, key='html'):
        """把jsonp中键为key的html取出"""
        json_dict = UnloginCrawl.jsonp_to_dict(jsonp)
        _html = json_dict[key]
        _html = re.sub(r'\\\\"', '"', _html)
        _html = re.sub(r'\\\\/', '/', _html)
        _html = re.sub(r'\\r', '\r', _html)
        _html = re.sub(r'\\n', '\n', _html)
        _html = re.sub(r'\\t', '\t', _html)
        _html = re.sub(r"\\'", "'", _html)
        # 非utf-8字符，无法识别
        # _html = re.sub(r'\\x', r'\\\\x', _html)
        # _html = re.sub(r'(\\U\w{8})', r'\\\1', _html)
        return _html
