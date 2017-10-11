# weibospider
基于scrapy框架的微博爬虫

### Feature
* selenium模拟登陆
* POST模拟登陆
* 获取首页推送微博
  * 获取微博mid号
  * 获取微博作者
  * 获取发表时间
  * 获取微博文字内容
  * 获取来源页
  * 获取图片地址
  * 获取视频地址
  * 获取转发数、评论数、点赞数
* 获取用户信息
  * 获取用户名
  * 性别
  * 是否是vip
  * 是否是大V认证
  * 简介
  * 等级
  * 关注数、粉丝数、微博数
  * 主页地址

### Known Issue
* phantomjs浏览器截图中未出现验证码，换成chrome却没有出现此问题