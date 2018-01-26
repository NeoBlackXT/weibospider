import gzip
import json
import random
import re
import base64
import binascii
import rsa
from urllib import request
from urllib import parse
import time
import traceback

from weibospider.captcha.ocrrecog import recognize
from weibospider.utils import JsonUtil

"""
在spiders目录中添加users.txt文件，内容格式为：
每行一个账号，账号密码以空格或Tab隔开，如：
user1 passwd1
user2 passwd2
user3 passwd3
"""


class PostLogin(object):
    __slots__ = ('users', 'prelogin_start')

    def __init__(self):
        self.users = {}
        with open('users.txt', 'r') as f:
            while True:
                line = f.readline()
                if line == '':
                    break
                line = re.sub('\r?\n?', '', line)
                split = re.split('\s+', line)
                self.users[split[0]] = split[1]
            f.close()
            print(self.users)

    def __prelogin(self, username=''):
        """https://login.sina.com.cn/js/sso/ssologin.js 309行
            获取公钥 公钥版本号 一次性数字 服务器时间 执行时间"""
        # sinaSSOController.preloginCallBack({"retcode":0,"servertime":1507570357,"pcid":"gz-73b86cb0f4aee335417b5d1450179a43fa2f","nonce":"GE7P4D","pubkey":"EB2A38568661887FA180BDDB5CABD5F21C7BFD59C090CB2D245A87AC253062882729293E5506350508E7F9AA3BB77F4333231490F915F6D63C55FE2F08A49B353F444AD3993CACC02DB784ABBB8E42A9B1BBFFFB38BE18D78E87A0E41B9B8F73A928EE0CCEE1F6739884B9777E4FE9E88A1BBE495927AC4A799B3181D6442443","rsakv":"1330428213","is_openlock":0,"exectime":13})
        _username = parse.quote(base64.encodebytes(parse.quote(username).encode()).decode().strip())
        _rnd = str(int(time.time())) + str(random.randint(100, 999))
        url = 'https://login.sina.com.cn/sso/prelogin.php?entry=account&callback=' \
              'sinaSSOController.preloginCallBack&su=' \
              '%s&rsakt=mod&client=ssologin.js(v1.4.15)&_=%s' % (_username, _rnd)
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh-HK;q=0.8,zh-TW;q=0.6,zh;q=0.4,en-US;q=0.2,en;q=0.2',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://login.sina.com.cn/signup/signin.php',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/61.0.3163.91 Safari/537.36'}
        prelogin_request = request.Request(url, headers=headers, method='GET', origin_req_host='login.sina.com.cn')
        self.prelogin_start = time.time()
        try:
            urlopen = request.urlopen(prelogin_request)
            if urlopen.getcode() == 200:
                prelogin_dict = JsonUtil.jsonp_to_dict(urlopen.read().decode())
                print(prelogin_dict)
                return prelogin_dict
            else:
                raise RuntimeError('status: %s,url: %s' % (urlopen.getcode(), urlopen.geturl()))
        except:
            traceback.print_exc()

    def get_cookies(self):

        # https://login.sina.com.cn/js/sso/ssologin.js 263行
        # 登录有三种方法：loginByXMLHttpRequest loginByIframe loginByScript
        # 这里使用第一种：loginByXMLHttpRequest(username, password, savestate) 参数为（用户名，密码，记住时间（天））
        # 924行定义了loginByXMLHttpRequest
        #   var loginByXMLHttpRequest = function(username, password, savestate) {
        #     if (typeof XMLHttpRequest == "undefined") {
        #       return false
        #     }
        #     var xhr = new XMLHttpRequest();
        #     if (!"withCredentials" in xhr) {
        #       return false
        #     }
        #     var request = makeXMLRequestQuery(username, password, savestate);
        #     var url = (me.loginType & https) ? ssoLoginUrl.replace(/^http:/, "https:") : ssoLoginUrl;
        #     url = makeURL(url, {
        #       client: me.getClientType(),
        #       _: (new Date()).getTime()
        #     });
        #     try {
        #       xhr.open("POST", url, true);
        #       xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        #       xhr.withCredentials = true;
        #       xhr.onreadystatechange = function() {
        #         if (xhr.readyState == 4 && xhr.status == 200) {
        #           me.loginCallBack(parseJSON(xhr.responseText))
        #         }
        #       };
        #       xhr.send(httpBuildQuery(request))
        #     } catch (e) {
        #       return false
        #     }
        #     return true
        #   };

        for user in self.users:
            try:
                request.urlopen('https://login.sina.com.cn')
                prelogin_dict = self.__prelogin(user)
                if prelogin_dict['retcode'] != 0:
                    raise RuntimeError('预登陆失败!返回的错误信息为： %s' % prelogin_dict)
                else:
                    prelt = int(time.time() - self.prelogin_start - prelogin_dict['servertime'])
                    _rnd = str(int(time.time())) + str(random.randint(100, 999))
                    url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)&_=%s' % _rnd
                    su = parse.quote(base64.encodebytes(parse.quote(user).encode()).decode().strip())
                    sp = self.__rsa2_encode_pw(prelogin_dict['pubkey'], prelogin_dict['servertime'], prelogin_dict['nonce'],
                                               self.users[user])
                    yield self.__login(prelogin_dict, prelt, sp, su, url)
            except:
                traceback.print_exc()

    def __login(self, prelogin_dict, prelt, sp, su, url, cookies=None, door=None):
        headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Origin': 'https://login.sina.com.cn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': '*/*',
            'Referer': 'https://login.sina.com.cn/signup/signin.php',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh-HK;q=0.8,zh-TW;q=0.6,zh;q=0.4,en-US;q=0.2,en;q=0.2',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3163.91 Safari/537.36'
        }
        if cookies:
            headers['Cookie'] = cookies
        data_dict = {
            'cdult': 3,
            'domain': 'sina.com.cn',
            # 'door': 'mbyqu', 验证码 待定
            'encoding': 'UTF-8',
            'entry': 'account',
            'from': 'null',
            'gateway': 1,
            'nonce': prelogin_dict['nonce'],
            'pagerefer': '',
            'prelt': prelt,  # prelogin time
            'pwencode': 'rsa2',
            'returntype': 'TEXT',
            'rsakv': prelogin_dict['rsakv'],
            'savestate': 0,  # 记住天数
            'servertime': prelogin_dict['servertime'],
            'service': 'account',
            'sp': sp,  # 密码
            'sr': '1920*1080',  # 分辨率
            'su': su,  # 用户名
            'useticket': 0,
            'vsnf': 1,
        }
        if door:
            data_dict['door'] = door
        data_str = ''
        for k in data_dict:
            data_str += k + '=' + str(data_dict[k]) + '&'
        data = data_str[:-1].encode()
        post_request = request.Request(url, data=data, headers=headers, origin_req_host='login.sina.com.cn',
                                       method='POST')
        post_resp = request.urlopen(post_request)
        if post_resp.getcode() == 200:
            read = post_resp.read()
            if post_resp.getheader('Content-Encoding') == 'gzip':
                read = gzip.decompress(read)
            rtn_json = read.decode()
            rtn_dict = json.loads(rtn_json)
            cookies_str = ''
            if rtn_dict['retcode'] == '0':
                # 登陆成功
                cookies_str = post_resp.getheader('Set-Cookie')
                cookies_str = self.__process_cookies_str(cookies_str)
            elif rtn_dict['retcode'] == '4049' or rtn_dict['retcode'] == '2070':
                # 需要验证码 或 验证码不正确
                door_headers = headers.copy()
                door_headers['Accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
                door_headers.pop('Origin')
                door_headers.pop('Content-Type')
                door_rnd = random.randint(10000000, 99999999)
                door_url = 'https://login.sina.com.cn/cgi/pin.php?r=%s&s=0' % str(door_rnd)
                door_req = request.Request(door_url, headers=door_headers, origin_req_host='login.sina.com.cn',
                                           method='GET')
                door_resp = request.urlopen(door_req)
                if door_resp.getcode() == 200:
                    cookies_str = door_resp.getheader('Set-Cookie')
                    png = door_resp.read()
                    door = recognize(png)
                    _cookies = self.__process_cookies_str(cookies_str)
                    return self.__login(prelogin_dict, prelt, sp, su, url, _cookies, door)
            else:
                raise RuntimeError('未知错误，返回消息为： %s' % rtn_dict)
            return cookies_str
        else:
            raise RuntimeError('status: %s,url: %s' % (post_resp.getcode(), post_resp.geturl()))

    def __process_cookies_str(self, cookies_str=''):
        # SCF=AtdhDXv4q_7ixicOVdOcP9ZYW7BLse2IlEDhUh78lkYgV85uvVV81K1RkiOF7HuPEGxf8iiXyiGyk24jMTAWGqs.; expires=Saturday, 09-Oct-2027 14:27:08 GMT; path=/; domain=.sina.com.cn; httponly
        cookies_list = re.findall(r'(?:^|, )(\w{3,8}=.+?;)', cookies_str)
        return ' '.join(cookies_list)


    def __rsa2_encode_pw(self, rsa_pubkey='', servertime=0, nonce='', password=''):
        """
        获取加密后的密码
        :param rsa_pubkey:
        :param servertime:
        :param nonce:
        :param password:
        :return:
        """
        # https://login.sina.com.cn/js/sso/ssologin.js 882行
        # 这里有两种加密方式rsa和wsse，这里用到的是rsa
        #  var makeRequest = function(username, password, savestate) {
        #    var request = {
        #      entry: me.getEntry(),
        #      gateway: 1,
        #      from: me.from,
        #      savestate: savestate,
        #      useticket: me.useTicket ? 1 : 0
        #    };
        #    if (me.failRedirect) {
        #      me.loginExtraQuery.frd = 1
        #    }
        #    request = objMerge(request, {
        #      pagerefer: document.referrer || ""
        #    });
        #    request = objMerge(request, me.loginExtraFlag);
        #    request = objMerge(request, me.loginExtraQuery);
        #    request.su = sinaSSOEncoder.base64.encode(urlencode(username));
        #    if (me.service) {
        #      request.service = me.service
        #    }
        #    if ((me.loginType & rsa) && me.servertime && sinaSSOEncoder && sinaSSOEncoder.RSAKey) {
        #      request.servertime = me.servertime;
        #      request.nonce = me.nonce;
        #      request.pwencode = "rsa2";
        #      request.rsakv = me.rsakv;
        #      var RSAKey = new sinaSSOEncoder.RSAKey();
        #      RSAKey.setPublic(me.rsaPubkey, "10001");
        #      password = RSAKey.encrypt([me.servertime, me.nonce].join("\t") + "\n" + password)
        #    } else {
        #      if ((me.loginType & wsse) && me.servertime && sinaSSOEncoder && sinaSSOEncoder.hex_sha1) {
        #        request.servertime = me.servertime;
        #        request.nonce = me.nonce;
        #        request.pwencode = "wsse";
        #        password = sinaSSOEncoder.hex_sha1("" + sinaSSOEncoder.hex_sha1(sinaSSOEncoder.hex_sha1(password)) + me.servertime + me.nonce)
        #      }
        #    }
        #    request.sp = password;
        #    try {
        #      request.sr = window.screen.width + "*" + window.screen.height
        #    } catch (e) {}
        #    return request
        #  };
        n = int(rsa_pubkey, 16)
        e = int('10001', 16)
        key = rsa.PublicKey(n, e)
        msg = str(servertime) + '\t' + nonce + '\n' + password
        encrypt = rsa.encrypt(msg.encode(), key)
        return binascii.b2a_hex(encrypt).decode()


if __name__ == '__main__':
    cookies = PostLogin().get_cookies()
    for cookie in cookies:
        print(cookie)
