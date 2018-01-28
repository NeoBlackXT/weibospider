# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import time
from urllib import parse

from scrapy.exceptions import DropItem

from weibospider import settings
from weibospider.items import WeiboItem, UserItem
import pymysql
from sqlalchemy import *


class WeiboPipelinePymysql(object):

    db_url = settings.DB_URL
    # In[4]:parse.urlparse(DB_URL)
    # Out[4]: ParseResult(scheme='mysql+pymysql', netloc='root:rootroot@localhost', path='/weibo', params='',
    #                     query='charset=utf8mb4', fragment='')
    pr = parse.urlparse(db_url)
    auth, host = pr[1].split('@')
    user, password = auth.split(':')
    db = pr[2][1:]
    query = pr[4].split('&')
    query = dict(zip([i.split('=')[0] for i in query], [i.split('=')[1] for i in query]))
    charset = query['charset']

    def process_item(self, item, spider):
        spider.logger.info(item)
        cls = WeiboPipelinePymysql
        connection = pymysql.connect(host=cls.host, user=cls.user, password=cls.password, db=cls.db,
                                     charset=cls.charset, autocommit=True, cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection as cursor:
                if isinstance(item, WeiboItem):
                    _sql = "INSERT INTO `T_WEIBO` (`mid`,`nickname`,`date`,`content`,`source_url`,`image_urls`,`video_url`,`forwarding_num`,`comment_num`,`praise_num`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(_sql, (
                        item['mid'], item['nickname'], time.strftime('%Y%m%d%H%M%S', time.localtime(item['date'])),
                        item['content'], item['source_url'], ';'.join(item['image_urls'] or ''), item['video_url'] or '',
                        int(item['forwarding_num']), int(item['comment_num']), int(item['praise_num'])))
                elif isinstance(item, UserItem):
                    _sql = "INSERT INTO `T_USER` (`nickname`,`gender`,`is_vip`,`verified`,`introduction`,`level`,`concern_num`,`fans_num`,`weibo_num`,`home_url`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(_sql, (
                        item['nickname'], item['gender'], item['is_vip'], item['verified'], item['introduction'],
                        item['level'],
                        item['concern_num'], item['fans_num'], item['weibo_num'], item['home_url']))
                else:
                    raise RuntimeError('unknown item:{}'.format(item))
        except:
            raise DropItem
        finally:
            connection.close()
        return item


class WeiboPipelineSQLAlchemyCore(object):

    db_url = settings.DB_URL
    db_engine = create_engine(db_url, pool_recycle=3600)

    def process_item(self, item, spider):
        spider.logger.info(item)
        cls = WeiboPipelineSQLAlchemyCore
        try:
            if isinstance(item, WeiboItem):
                _sql = "INSERT INTO `T_WEIBO` (`mid`,`nickname`,`date`,`content`,`source_url`,`image_urls`,`video_url`,`forwarding_num`,`comment_num`,`praise_num`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cls.db_engine.execute(_sql, (
                        item['mid'], item['nickname'], time.strftime('%Y%m%d%H%M%S', time.localtime(item['date'])),
                        item['content'], item['source_url'], ';'.join(item['image_urls'] or ''), item['video_url'] or '',
                        int(item['forwarding_num']), int(item['comment_num']), int(item['praise_num'])))
            elif isinstance(item, UserItem):
                _sql = "INSERT INTO `T_USER` (`nickname`,`gender`,`is_vip`,`verified`,`introduction`,`level`,`concern_num`,`fans_num`,`weibo_num`,`home_url`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cls.db_engine.execute(_sql, (
                    item['nickname'], item['gender'], item['is_vip'], item['verified'], item['introduction'],
                    item['level'],
                    item['concern_num'], item['fans_num'], item['weibo_num'], item['home_url']))
            else:
                raise RuntimeError('unknown item:{}'.format(item))
        except:
            raise DropItem
        return item
