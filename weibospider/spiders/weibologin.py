import traceback

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class WeibologinSpider(object):
    def __init__(self):

        self.users = {}
        self.iteritems = {}
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

    def get_cookies(self):
        # options = webdriver.ChromeOptions()
        # Chrome canary的默认安装路径
        # options.binary_location = 'C:/Users/admin/AppData/Local/Google/Chrome SxS/Application/chrome.exe'

        # 获取一条账号信息
        for i in self.users.keys():
            username = i
            password = self.users.get(i)

            try:
                # driver = webdriver.Chrome(executable_path='d:/dev/phantomjs/bin/chromedriver.exe',
                # chrome_options=options)
                # driver = webdriver.Chrome(executable_path='d:/dev/phantomjs/bin/chromedriver.exe')

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
                driver.find_element_by_xpath('//*[@id="username"]').clear()
                driver.find_element_by_xpath('//*[@id="username"]').send_keys(username)
                driver.find_element_by_xpath('//*[@id="username"]').send_keys(Keys.ENTER)
                time.sleep(0.5)
                driver.find_element_by_xpath('//*[@id="password"]').click()
                driver.find_element_by_xpath('//*[@id="password"]').clear()
                driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
                time.sleep(0.5)
                driver.find_element_by_xpath('//input[@class="W_btn_a btn_34px"]').click()
                time.sleep(1)
                try:
                    xpath = driver.find_element_by_xpath('//img[@id="check_img"]')
                    if xpath:
                        png = driver.get_screenshot_as_png()
                        with open("d:\\screenshot.png","wb") as ss:
                            ss.write(png)
                            ss.close()
                        captcha = input('请输入验证码')
                        driver.find_element_by_xpath('//input[@id="door"]').click()
                        driver.find_element_by_xpath('//input[@id="door"]').clear()
                        driver.find_element_by_xpath('//input[@id="door"]').send_keys(captcha)

                except NoSuchElementException:
                    print('没有验证码')
                else:
                    driver.find_element_by_xpath('//input[@class="W_btn_a btn_34px"]').click()
                print('登录信息输入完毕')
                WebDriverWait(driver, 10). \
                    until(expected_conditions.title_contains(u'我的新浪'))

                print('登录完毕')
                _cookies = driver.get_cookies()
                print('cookie:' + str(_cookies[0]))
                yield _cookies[0]
            except TimeoutException:
                print('用户名或密码错误 ' + username + ':' + password)
                ecstr = traceback.format_exc()
                print(ecstr)
            finally:
                driver.close()


if __name__ == '__main__':
    cookies = WeibologinSpider().get_cookies()
    for cookie in cookies:
        print(cookie)
