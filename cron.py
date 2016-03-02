#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
import logging
import sys
import requests
import json
import time
import sys, traceback

import requests.packages.urllib3 as urllib3
urllib3.disable_warnings()

logging.getLogger("requests").setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

## 迅雷用户名、密码
user = 'user'
passwd = 'passwd'

##水晶API
shuijing_api = '1-api-red.xunlei.com'

##增加是否自动开宝箱的开关(0表示关闭，1表示开启)
gift_open = 1
##增加开宝箱耗费水晶上限(0表示只开免费原石，500表示只开<=500的原石)
cnum = 0
##增加转盘游戏自动开关(0表示关闭，1表示打开)
turntable = 1

PACKET_LOGIN = '{"cmdID":1,"isCompressed":0,"rsaKey":{"n":"D6F1CFBF4D9F70710527E1B1911635460B1FF9AB7C202294D04A6F135A906E90E2398123C234340A3CEA0E5EFDCB4BCF7C613A5A52B96F59871D8AB9D240ABD4481CCFD758EC3F2FDD54A1D4D56BFFD5C4A95810A8CA25E87FDC752EFA047DF4710C7D67CA025A2DC3EA59B09A9F2E3A41D4A7EFBB31C738B35FFAAA5C6F4E6F","e":"010001"},"businessType":61,"passWord":"%s","loginType":0,"appName":"ANDROID-com.xunlei.redcrystalandroid","platformVersion":1,"sessionID":"","protocolVersion":101,"userName":"%s","extensionList":"","sequenceNo":10000001,"peerID":"%s","clientVersion":"1.0.0"}'
PACKET_LOGIN2 = 'sessionid=%s;userid=%s;origin=1;nickname=%s'
s = requests.Session()
g_headers = {'User-Agent': 'android-async-http/1.4.3 (http://loopj.com/android-async-http)'}
g_headers2 = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
g_cookies = {}
g_peerid = ''
g_userID = 0
g_totalnum = 0
g_totalbox = 0
g_unget= 0

n = '00D6F1CFBF4D9F70710527E1B1911635460B1FF9AB7C202294D04A6F135A906E90E2398123C234340A3CEA0E5EFDCB4BCF7C613A5A52B96F59871D8AB9D240ABD4481CCFD758EC3F2FDD54A1D4D56BFFD5C4A95810A8CA25E87FDC752EFA047DF4710C7D67CA025A2DC3EA59B09A9F2E3A41D4A7EFBB31C738B35FFAAA5C6F4E6F'
e = '010001'

import hashlib

def modpow(b, e, m):
    result = 1
    while (e > 0):
        if e & 1:
            result = (result * b) % m
        e = e >> 1
        b = (b * b) % m
    return result

def str_to_int(string):
    str_int = 0
    for i in range(len(string)):
        str_int = str_int << 8
        str_int += ord(string[i])
    return str_int

def rsa(data):
    result = modpow(str_to_int(data), long(e, 16), long(n, 16))
    return hex(result).upper()[2:-1]

def gen_passwd(passwd):
    return rsa(hashlib.md5(passwd).hexdigest())

def gen_peerID():
    return string.join(random.sample('ABCDEF0123456789', 16)).replace(' ', '')

g_peerid = gen_peerID()

def login():
    global g_headers
    global g_cookies
    global g_peerid
    data = PACKET_LOGIN % (gen_passwd(passwd), user, g_peerid)
    r = requests.post('https://login.mobile.reg2t.sandai.net:443/', data, verify=False, headers=g_headers)
    if r.status_code != 200:
        logging.warn('status code %s' % r.status_code)
        raise Exception('迅雷服务器小霸王中...')
    ret = json.loads(r.text)
    if 'nickName' not in ret:
        logging.info('[登录失败]'.decode('utf-8'))
        raise Exception('login faild...')
    logging.info(('[登录成功:%s]' % ret['nickName'].encode('utf-8')).decode('utf-8'))

    g_userID = ret['userID']
    g_cookies['sessionid'] = ret['sessionID']
    g_cookies['userid'] = str(ret['userID']).encode('utf-8')
    g_cookies['origin'] = '1'

    ## 解决昵称为中文时的异常错误
    #g_cookies['nickname'] = ('%s' % ret['nickName'].encode('utf-8')).decode('utf-8')


## 获取宝箱信息
## 修改所有获取api地址为最新 @modify by wangchll
def has_something_to_open():
    r = requests.post('http://%s/?r=mine/info' % shuijing_api,verify=False, headers=g_headers2, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('query gift and crystal failed')
    print r.text
    js = json.loads(r.text)
    gif = js['b_unget']
    crystal = js['td_not_in_a']
    return gif,crystal


## fetch crystal
def post_crystal():
     r = requests.post('http://%s/?r=mine/collect' % shuijing_api,verify=False, headers=g_headers2, cookies=g_cookies)
     if r.status_code != 200:
        raise Exception('fetch crystal failed')


def post_opengift(id):
    #增加切原石方向参数(1，左切；2，右切；3，竖切)
    side = random.randint(1,3)
    data = 'v=1&id=%s&side=%s' % (id, side)
    h = g_headers2.copy()
    h['X-Requested-With'] = 'XMLHttpRequest'
    r = requests.post('http://%s/index.php?r=usr/openStone' % shuijing_api, data, verify=False, headers=h, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('迅雷服务器小霸王中...')
    js = json.loads(r.text)
    if js['r'] == 0:
        global g_totalnum
        global g_totalbox
        g_totalnum += js['get']['num']
        g_totalbox += 1
        logging.info(('[领取钻石成功] 获得数量:%s 累计领取:%s 累计开箱:%s' % (js['get']['num'], g_totalnum, g_totalbox)).decode('utf-8'))

def post_giftbox():
    data = 'v=2&cmid=-1&p=0&ps=60&tp=0&t='
    r = requests.post('http://%s/index.php?r=usr/giftbox' % shuijing_api, data, verify=False, headers=g_headers2, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('迅雷服务器小霸王中...')
    js = json.loads(r.text)
    print js
    if 'ci' not in js:
        return
    for item in js['ci']:
        if item['st'] == 0:
            if item['cnum'] <= cnum:
                post_opengift(item['id'])
            else:
                logging.info(('原石ID:%s 打开需要耗费水晶:%s,超过设定的自动开箱子值:%s 自动放弃！' % (item['id'], item['cnum'], cnum)).decode('utf-8'))

def post_turntable():
    r = requests.post('http://%s/index.php?r=turntable/getaward' % shuijing_api,verify=False, headers=g_headers2, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('转盘游戏运行失败...')
    js = json.loads(r.text)
    print js
    logging.info('转盘结果:%s' % (js['rd'].encode('utf-8')))

#login_sleep_min = 60
#login_sleep = login_sleep_min
#while True:
try:
    login()
    #login_sleep = login_sleep_min
    gift,crystal = has_something_to_open()

    if gift_open > 0:
        if gift > 0:
            post_giftbox()
            logging.info(u'>>>> open gift success <<<<')
        else:
            logging.info(u'>>>> no gift box to open <<<<')
    else:
        logging.info(u'>>>> pass open gift <<<<')

    if crystal > 0 :
        post_crystal()
        logging.info(u'>>>> fetch crystal success <<<<')
    else:
         logging.info(u'>>>>  no crystal to fetch <<<<')

    if turntable > 0 :
        post_turntable()
        logging.info(u'>>>> turn table success <<<<')
    else:
         logging.info(u'>>>>  turntable off <<<<')

    logging.info(u'sleep && waiting for next work')
    #time.sleep(50 * 60)
except Exception , e:
    '''
    if login_sleep < 10 * 60:
        login_sleep += 60
    logging.warn(('[登录失败]:睡觉%s秒后再试' % (login_sleep)).decode('utf-8'))
    '''
    print e
    #time.sleep(login_sleep)
