# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import traceback

import time

from weibospider.items import WeiboItem, UserItem
import pymysql


class WeiboPipeline(object):
    def process_item(self, item, spider):
        spider.logger.info('pipeline started')
        connection = pymysql.connect(host='localhost', user='root', password='root', db='weibo', charset='utf8',
                                     cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                spider.logger.info('Item type: %s' % type(item))
                if isinstance(item, WeiboItem):
                    # sql = "INSERT INTO `WEIBO` (`mid`,`nickname`,`date`,`content`,`source_url`,`image_urls`,`video_url`,`forwarding_num`,`comment_num`,`praise_num`) VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',%d,%d,%d)" % (item['mid'],item['nickname'],time.strftime('%Y%m%d%H%M%S',time.localtime(item['date'])),item['content'],item['source_url'],';'.join(item['image_urls'] or ''),item['video_url'] or '',item['forwarding_num'],item['comment_num'],item['praise_num'])
                    # spider.logger.info('SQL: %s'%sql)
                    # cursor.execute(sql)
                    sql = "INSERT INTO `T_WEIBO` (`mid`,`nickname`,`date`,`content`,`source_url`,`image_urls`,`video_url`,`forwarding_num`,`comment_num`,`praise_num`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    spider.logger.info(item)
                    spider.logger.info('%s %s %s'%(item['forwarding_num'],item['comment_num'],item['praise_num']))
                    cursor.execute(sql, (
                        item['mid'], item['nickname'], time.strftime('%Y%m%d%H%M%S', time.localtime(item['date'])),
                        item['content'], item['source_url'], ';'.join(item['image_urls'] or ''), item['video_url'] or '',
                        int(item['forwarding_num']), int(item['comment_num']), int(item['praise_num'])))
                else:
                    sql = "INSERT INTO `T_USER` (`nickname`,`gender`,`is_vip`,`verified`,`introduction`,`level`,`concern_num`,`fans_num`,`weibo_num`,`home_url`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(sql, (
                        item['nickname'], item['gender'], item['is_vip'], item['verified'], item['introduction'],
                        item['level'],
                        item['concern_num'], item['fans_num'], item['weibo_num'], item['home_url']))
                connection.commit()
        except:
                traceback.print_exc()
        finally:
                connection.close()
        return item
