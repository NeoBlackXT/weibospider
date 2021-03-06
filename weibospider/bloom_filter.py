import logging
import time

from scrapy.dupefilters import BaseDupeFilter
from scrapy.utils.request import request_fingerprint

from scrapy_redis import defaults
from scrapy_redis.connection import get_redis_from_settings

from weibospider import general_hash_functions as hf
from weibospider import settings
import redis

logger = logging.getLogger(__name__)
hash_list = ['rs_hash', 'js_hash', 'pjw_hash', 'elf_hash', 'bkdr_hash', 'sdbm_hash', 'djb_hash', 'dek_hash',
             'dek_hash', 'bp_hash', 'fnv_hash']


class RFPDupeFilter(BaseDupeFilter):
    """Redis-based request duplicates filter.

    This class can also be used with default Scrapy's scheduler.

    """

    logger = logger

    def __init__(self, server, key, debug=False):
        """Initialize the duplicates filter.

        Parameters
        ----------
        server : redis.StrictRedis
            The redis server instance.
        key : str
            Redis key Where to store fingerprints.
        debug : bool, optional
            Whether to log filtered requests.

        """
        self.server = server
        self.key = key
        self.debug = debug
        self.logdupes = True
        # 由于scrapy_redis模块的调度器直接调用过滤器的__init__()方法，
        # 不通过from_settings()导入设置，所以在此处读取设置
        try:
            hash_num = settings.BLOOM_HASH_NUM
        except AttributeError:
            logger.info('未配置BLOOM_HASH_NUM，使用默认值8')
            hash_num = 8
        if hash_num > 11:
            logger.warning('BLOOM_HASH_NUM最大值为11，已使用最大值11')
            hash_num = 11
        try:
            bit_array_size = settings.BLOOM_BIT_ARRAY_SIZE
        except AttributeError:
            logger.info('未配置BLOOM_BIT_ARRAY_SIZE，使用默认值2^32')
            bit_array_size = 1 << 32
        if bit_array_size > 1 << 32:
            logger.warning('BLOOM_BIT_ARRAY_SIZE最大值为2^32，已使用最大值2^32')
            bit_array_size = 1 << 32
        self.hash_list = [getattr(hf, hash_name) for hash_name in hash_list][:hash_num+1]
        self.bit_array_size = bit_array_size
        self.max_offset = self.bit_array_size - 1

    @classmethod
    def from_settings(cls, settings):
        """Returns an instance from given settings.

        This uses by default the key ``dupefilter:<timestamp>``. When using the
        ``scrapy_redis.scheduler.Scheduler`` class, this method is not used as
        it needs to pass the spider name in the key.

        Parameters
        ----------
        settings : scrapy.settings.Settings

        Returns
        -------
        RFPDupeFilter
            A RFPDupeFilter instance.


        """
        server = get_redis_from_settings(settings)
        # XXX: This creates one-time key. needed to support to use this
        # class as standalone dupefilter with scrapy's default scheduler
        # if scrapy passes spider on open() method this wouldn't be needed
        # TODO: Use SCRAPY_JOB env as default and fallback to timestamp.
        key = defaults.DUPEFILTER_KEY % {'timestamp': int(time.time())}
        debug = settings.getbool('DUPEFILTER_DEBUG')
        return cls(server, key=key, debug=debug)

    @classmethod
    def from_crawler(cls, crawler):
        """Returns instance from crawler.

        Parameters
        ----------
        crawler : scrapy.crawler.Crawler

        Returns
        -------
        RFPDupeFilter
            Instance of RFPDupeFilter.

        """
        return cls.from_settings(crawler.settings)

    def request_seen(self, request):
        """Returns True if request was already seen.

        Parameters
        ----------
        request : scrapy.http.Request

        Returns
        -------
        bool

        """
        fp = self.request_fingerprint(request)
        return self.setbit(fp)

    def request_fingerprint(self, request):
        """Returns a fingerprint for a given request.

        Parameters
        ----------
        request : scrapy.http.Request

        Returns
        -------
        str

        """
        return request_fingerprint(request)

    def setbit(self, fingerprint):
        """
        根据请求指纹设置布隆过滤器的标记位
        :param fingerprint:
        :return:
        """
        flag = 1
        for hash_func in self.hash_list:
            offset = hash_func(fingerprint) & self.max_offset
            flag &= self.server.setbit(self.key, offset, 1)
        # 全部标记位为1时表示该请求已重复
        return flag == 1

    def close(self, reason=''):
        """Delete data on close. Called by Scrapy's scheduler.

        Parameters
        ----------
        reason : str, optional

        """
        self.clear()

    def clear(self):
        """Clears fingerprints data."""
        self.server.delete(self.key)

    def log(self, request, spider):
        """Logs given request.

        Parameters
        ----------
        request : scrapy.http.Request
        spider : scrapy.spiders.Spider

        """
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
            self.logdupes = False
