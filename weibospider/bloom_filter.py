from scrapy.dupefilters import RFPDupeFilter
from scrapy.utils.job import job_dir

from weibospider import general_hash_functions
import redis


class BloomFilter(RFPDupeFilter):
    hash_list = ['rs_hash', 'js_hash', 'pjw_hash', 'elf_hash', 'bkdr_hash', 'sdbm_hash', 'djb_hash', 'dek_hash',
                 'bp_hash', 'fnv_hash', 'ap_hash']

    def __init__(self, path=None, debug=False, host=None, port=6379, db=0, password=None):
        if host is None:
            raise RuntimeError("REDIS_BLOOM_HOST未在settings中配置")
        super(BloomFilter,self).__init__(path=path, debug=debug)
        pool = redis.ConnectionPool(host=host, port=port, db=db, password=password)
        self.r = redis.Redis(connection_pool=pool)
        self.hash_list = BloomFilter.hash_list

    def filter(self, name='bloom', text=''):
        """
        检测给定文本是否重复
        :param name: redis中的位数组的name，默认值=bloom
        :param text: 被检测的文本
        :return: 返回真时表示该文本重复
        """
        flag = 1
        for hash_name in self.hash_list:
            hash_func = getattr(general_hash_functions, hash_name)
            hash_value = hash_func(text)
            offset = hash_value % (1 << 32)
            flag &= self.r.setbit(name=name, offset=offset, value=1)
        return flag == 1

    @classmethod
    def from_settings(cls, settings):
        debug = settings.getbool('DUPEFILTER_DEBUG')
        host = settings.get('REDIS_BLOOM_FILTER_HOST')
        port = settings.getint('REDIS_BLOOM_FILTER_PORT')
        db = settings.getint('REDIS_BLOOM_FILTER_DB')
        password = settings.get('REDIS_BLOOM_FILTER_PASSWORD')
        return cls(job_dir(settings), debug, host, port, db, password)

    def request_seen(self, request):
        return self.filter(text=request.url)
