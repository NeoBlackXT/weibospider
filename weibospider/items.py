# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    mid = scrapy.Field()
    nickname = scrapy.Field()
    date = scrapy.Field()
    content = scrapy.Field()
    source_url = scrapy.Field()
    image_urls = scrapy.Field()
    video_url = scrapy.Field()
    forwarding_num = scrapy.Field()
    comment_num = scrapy.Field()
    praise_num = scrapy.Field()


class UserItem(scrapy.Item):
    nickname = scrapy.Field()
    gender = scrapy.Field()
    is_vip = scrapy.Field()
    verified = scrapy.Field()
    introduction = scrapy.Field()
    level = scrapy.Field()
    concern_num = scrapy.Field()
    fans_num = scrapy.Field()
    weibo_num = scrapy.Field()
    home_url = scrapy.Field()
