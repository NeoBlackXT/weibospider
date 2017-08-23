# -*- coding: utf-8 -*-
import traceback

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class WeibologinSpider:
    def __init__(self):

        self.users = {}
        with open('users.txt', 'rb') as f:
            while True:
                line = f.readline()
                if line == '':
                    break
                line = re.sub('\r?\n?', '', line)
                split = re.split('\s+', line)
                self.users[split[0]] = split[1]
            f.close()
            self.iteritems = self.users.iteritems()
            print(self.users)

    def get_cookies(self):
        options = webdriver.ChromeOptions()
        options.binary_location = 'C:/Users/admin/AppData/Local/Google/Chrome SxS/Application/chrome.exe'

        # 获取一条账号信息
        for i in self.iteritems:
            username = i[0]
            password = i[1]

            try:
                # driver = webdriver.Chrome(executable_path='d:/dev/phantomjs/bin/chromedriver.exe',
                # chrome_options=options)

                # 设置phantomjs的ua
                dcap = dict(DesiredCapabilities.PHANTOMJS)
                dcap[
                    "phantomjs.page.settings.userAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                                                           "AppleWebKit/537.36 (KHTML, like Gecko) " \
                                                           "Chrome/61.0.3157.3 Safari/537.36"

                driver = webdriver.PhantomJS(executable_path='d:/dev/phantomjs/bin/phantomjs.exe',
                                             desired_capabilities=dcap)
                driver.get('https://login.sina.com.cn')
                WebDriverWait(driver, 10). \
                    until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//input[@class="W_btn_a btn_34px"]')))

                driver.find_element_by_xpath('//*[@id="username"]').click()
                driver.find_element_by_xpath('//*[@id="username"]').send_keys(username)
                driver.find_element_by_xpath('//*[@id="username"]').send_keys(Keys.ENTER)
                time.sleep(0.5)
                driver.find_element_by_xpath('//*[@id="password"]').click()
                driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
                time.sleep(0.5)
                driver.find_element_by_xpath('//input[@class="W_btn_a btn_34px"]').click()

                print('登录信息输入完毕')
                WebDriverWait(driver, 10). \
                    until(expected_conditions.title_contains(u'我的新浪'))

                print('登录完毕')
                _cookies = driver.get_cookies()
                print('cookie:' + str(_cookies[0]))
                yield cookies[0]
            except TimeoutException as ei:
                print('用户名或密码错误 ' + i[0] + ':' + i[1])
                ecstr = traceback.format_exc()
                print(ecstr)
            finally:
                driver.close()


if __name__ == '__main__':
    cookies = WeibologinSpider().get_cookies()
    for cookie in cookies:
        print(cookie)
