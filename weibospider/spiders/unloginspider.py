import logging
import traceback
import random
import time
import re
from urllib import parse

import scrapy
import sys
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Spider
from weibospider.items import WeiboItem, UserItem
from weibospider.utils import JsonUtil, CookieUtil


class UnloginCrawl(CrawlSpider):
    name = 'unlogincrawl'
    allowed_domains = ['weibo.com']

    # 爬取分类
    category = 0
    # 爬取起始页（从起始页向第一页爬取，最后只刷新第一页）
    page = 1

    def start_requests(self):
        while True:
            _rnd = str(int(time.time())) + str(random.randint(100, 999))
            _url = 'https://weibo.com/a/aj/transform/loadingmoreunlogin?ajwvr=6&category=%d&page=%d&lefnav=0&__rnd=%s' \
                   % (self.category, self.page, _rnd)
            yield Request(_url, dont_filter=True)
            self.page = 1 if self.page <= 1 else self.page - 1

    def parse_start_url(self, response):
        _json = response.text
        _html = JsonUtil.jsonp_to_html(_json, 'data')

        html = HtmlResponse(url=response.url, body=_html, encoding='utf-8')

        div_list_a = html.xpath('//div[@class="UG_list_a"]')
        yield from self._parse_div_list_a(div_list_a)
        div_list_b = html.xpath('//div[@class="UG_list_b"]')
        yield from self._parse_div_list_b(div_list_b)
        div_list_v2 = html.xpath('//div[@class="UG_list_v2 clearfix"]')
        yield from self._parse_div_list_v2(div_list_v2)

        visitor_entry = 'https://passport.weibo.com/visitor/visitor?a=incarnate&t=12UrHziv5snGSE7sCsY2uiRVJ7gRqOQ8XFS6jGwvkyg%3D&w=2&c=095&gc=&cb=cross_domain&from=weibo&_rand={}'.format(
            random.random())

        div_list_a = div_list_a.extract()
        div_list_b = div_list_b.extract()
        div_list_v2 = div_list_v2.extract()

        meta = {'div_list_a': div_list_a, 'div_list_b': div_list_b, 'div_list_v2': div_list_v2}
        # 请求用户页面之前必须获取到Cookies,获取不到就多重试几次
        meta.update({'max_retry_times': 20})
        yield Request(visitor_entry, self._request_user, meta=meta, priority=20)

    def _request_user(self, response):
        # the request cookies. These can be sent in two forms.
        # Using a dict:
        # request_with_cookies = Request(url="http://www.example.com",
        #                                cookies={'currency': 'USD', 'country': 'UY'})
        # Using a list of dicts:
        # request_with_cookies = Request(url="http://www.example.com",
        #                                cookies=[{'name': 'currency',
        #                                         'value': 'USD',
        #                                         'domain': 'example.com',
        #                                         'path': '/currency'}])

        # 只保留SUB和SUBP这两个KEY
        setcookie = response.headers.getlist('Set-Cookie')
        cookies = CookieUtil.convert_setcookie(setcookie)
        cookie_dict = {}
        for cookie in cookies:
            if ('SUB' in cookie) or ('SUBP' in cookie):
                cookie_dict.update(cookie)

        def meta2response(resp, *meta):
            _div = {}
            for m in meta:
                _div[m] = ''.join(resp.meta[m])
                _div[m] = HtmlResponse(url=resp.url, encoding='utf-8', body=_div[m])
                _div[m] = _div[m].xpath('//body/div')
            return _div

        div = meta2response(response, 'div_list_a', 'div_list_b', 'div_list_v2')
        for i in div['div_list_a']:
            user_home_url = 'https://weibo.com' + i.xpath('./div[@class="subinfo_box clearfix"]/a[2]/@href')[
                0].extract()
            yield Request(user_home_url, callback=self._parse_user, cookies=cookie_dict, priority=10)
        for i in div['div_list_b']:
            user_home_url = 'https://weibo.com' + \
                            i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/@href')[
                                0].extract()
            yield Request(user_home_url, callback=self._parse_user, cookies=cookie_dict, priority=10)
        for i in div['div_list_v2']:
            user_home_url = 'https:' + \
                            i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/@href')[
                                0].extract()
            yield Request(user_home_url, callback=self._parse_user, cookies=cookie_dict, priority=10)

    def _parse_div_list_a(self, div_list_a):
        for i in div_list_a:
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0].extract()
            weibo_item['nickname'] = i.xpath('./div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0].extract()
            date_str = i.xpath('./div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[0].extract()
            weibo_item['date'] = self.__process_datestr(date_str)
            content_div = i.xpath('./*[1]/*/descendant-or-self::text()').extract()
            weibo_item['content'] = ''.join(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./@href')[0].extract()
            weibo_item['image_urls'] = i.xpath('./div[@class="list_nod clearfix"]/div/img/@src').extract()
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em[2]/text()').extract()
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            yield weibo_item

    def _parse_div_list_b(self, div_list_b):
        for i in div_list_b:
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0].extract()
            weibo_item['nickname'] = \
                i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0].extract()
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/text()')[
                    0].extract()
            weibo_item['date'] = self.__process_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*/descendant-or-self::text()').extract()
            weibo_item['content'] = ''.join(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./@href')[0].extract()
            weibo_item['image_urls'] = i.xpath('./div[1]/img/@src').extract()
            weibo_item['video_url'] = None
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo_rgt S_txt2"]/em['
                '2]/text()').extract()
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            yield weibo_item

    def _parse_div_list_v2(self, div_list_v2):
        for i in div_list_v2:
            weibo_item = WeiboItem()
            weibo_item['mid'] = i.xpath('./@mid')[0].extract()
            weibo_item['nickname'] = \
                i.xpath('./div[@class="list_des"]/div[@class="subinfo_box clearfix"]/a[2]/span/text()')[0].extract()
            date_str = \
                i.xpath(
                    './div[@class="list_des"]/div[@class="subinfo_box clearfix"]/span[@class="subinfo S_txt2"]/'
                    'text()')[0].extract()
            weibo_item['date'] = self.__process_datestr(date_str)
            content_div = i.xpath('./div[@class="list_des"]/*[1]/*/descendant-or-self::text()').extract()
            weibo_item['content'] = ''.join(content_div)
            weibo_item['source_url'] = 'http:' + i.xpath('./div[@class="vid"]/@href')[0].extract()
            weibo_item['image_urls'] = None
            action_data = i.xpath('./div[@class="vid"]/@action-data')[0].extract()
            video_src = action_data[action_data.index('video_src=') + 10:action_data.index('&cover_img=')]
            weibo_item['video_url'] = parse.unquote(video_src)
            nums = i.xpath(
                './div[@class="list_des"]/div[@class="subinfo_box clearfix subinfo_box_btm"]/span[@class="subinfo_rgt '
                'S_txt2"]/em[2]/text()')[0].extract()
            weibo_item['forwarding_num'] = int(nums[-1])
            weibo_item['comment_num'] = int(nums[-2])
            weibo_item['praise_num'] = int(nums[-3])
            Spider.log(self, weibo_item)
            yield weibo_item

    def _parse_user(self, response):
        try:
            user_item = UserItem()
            _html = response.text
            _json = response.xpath(
                '''/html/script[starts-with(text(),'FM.view({"ns":"pl.header.preloginHead.index",'''
                '''"domid":"Pl_Official_Headerv6') or starts-with(text(),'FM.view({"ns":"pl.header.head.index",'''
                '''"domid":"Pl_Official_Headerv6')]/text()''')[0].extract()
            _html = JsonUtil.jsonp_to_html(_json)
            _html_ele = HtmlResponse(url=response.url, encoding='utf-8', body=_html)
            user_item['nickname'] = _html_ele.xpath('./descendant::h1[@class="username"]/text()')[0].extract()
            gender_class = \
                _html_ele.xpath('./descendant::i[@class="W_icon icon_pf_female" or @class="W_icon icon_pf_male"]/'
                                '@class')[0].extract()
            user_item['gender'] = gender_class[gender_class.rindex('_') + 1:]
            # vip6的样式W_icon icon_member6
            user_item['is_vip'] = len(_html_ele.xpath('./descendant::a[@href="http://vip.weibo.com/personal?'
                                                      'from=main"]/em[not(contains(@class,"icon_member_dis"))]').extract()) > 0
            user_item['verified'] = len(_html_ele.xpath('./descendant::div[@class="pf_photo"]/a').extract()) > 0
            user_item['introduction'] = _html_ele.xpath('./descendant::div[@class="pf_intro" and 2]/text()')[
                0].extract().strip()
            _json = response.xpath(
                '''/html/script[starts-with(text(),'FM.view({"ns":"pl.content.homeFeed.index",'''
                '''"domid":"Pl_Core_UserInfo')]/text()''').extract()[0]
            _html = JsonUtil.jsonp_to_html(_json)
            _html_ele = HtmlResponse(url=response.url, encoding='utf-8', body=_html)
            level_text = _html_ele.xpath('./descendant::a/span/text()')[0].extract()
            user_item['level'] = int(level_text[level_text.index('.') + 1:])
            _json = response.xpath('''/html/script[starts-with(text(),'FM.view({"ns":"","domid":'''
                                   '''"Pl_Core_T8CustomTriColumn')]''').extract()[0]
            _html = JsonUtil.jsonp_to_html(_json)
            _html_ele = HtmlResponse(url=response.url, encoding='utf-8', body=_html)
            nums = _html_ele.xpath('./descendant::td/descendant::strong/text()').extract()
            user_item['concern_num'] = int(nums[0])
            user_item['fans_num'] = int(nums[1])
            user_item['weibo_num'] = int(nums[2])
            user_item['home_url'] = response.url[
                                    :response.url.index('?') if response.url.count('?') else None]
            Spider.log(self, 'user_item: %s' % user_item, level=logging.INFO)
            return user_item
        except:
            Spider.log(self, "%s\n%s" % (response.url, _html), logging.ERROR)
            traceback.print_exc()

    @staticmethod
    def __process_datestr(date_str):
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
