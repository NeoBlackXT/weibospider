import sys
import json
import logging
import re
import random
import requests
from requests import ConnectTimeout


class JsonUtil:
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
        json_dict = JsonUtil.jsonp_to_dict(jsonp)
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


class IPProxyUtil:
    __POOL_URL = 'http://127.0.0.1:5010'
    __retry_times = 0

    @staticmethod
    def get_proxy(pool_url=__POOL_URL):
        try:
            ip_port = requests.get("{}/get/".format(pool_url), timeout=10).text
            return 'http://{}'.format(ip_port)
        except ConnectTimeout:
            IPProxyUtil.get_proxy(pool_url)
            IPProxyUtil.__retry_times += 1
        finally:
            if IPProxyUtil.__retry_times >= 3:
                IPProxyUtil.__retry_times = 0
                logging.error('代理池无法连接，pool_url: %s' % pool_url)

    @staticmethod
    def delete_proxy(proxy, pool_url=__POOL_URL):
        requests.get("{}/delete/?proxy={}".format(pool_url, proxy[7:]), timeout=10)


class CookieUtil:

    @staticmethod
    def convert_setcookie(setcookie):
        if isinstance(setcookie, list):
            lst = []
            for i in setcookie:
                if isinstance(i, bytes):
                    i = i.decode()
                index = i.index(';')
                i = i[:index]
                cookie = i.split('=')
                lst.append({cookie[0]: cookie[1]})
            return lst
        else:
            raise RuntimeError('setcookie类型不为列表')


class TailRecurseException(BaseException):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


class TailRecursion:
    # This program shows off a python decorator(
    # which implements tail call optimization. It
    # does this by throwing an exception if it is
    # it's own grandparent, and catching such
    # exceptions to recall the stack.

    def tail_call_optimized(g):
        """
        This function decorates a function with tail call
        optimization. It does this by throwing an exception
        if it is it's own grandparent, and catching such
        exceptions to fake the tail call optimization.

        This function fails if the decorated
        function recurses in a non-tail context.
        """

        def func(*args, **kwargs):
            f = sys._getframe()
            if f.f_back and f.f_back.f_back \
                    and f.f_back.f_back.f_code == f.f_code:
                raise TailRecurseException(args, kwargs)
            else:
                while 1:
                    try:
                        return g(*args, **kwargs)
                    except TailRecurseException as e:
                        args = e.args
                        kwargs = e.kwargs

        func.__doc__ = g.__doc__
        return func
