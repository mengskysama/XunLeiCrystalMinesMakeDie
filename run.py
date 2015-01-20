#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
import logging
import sys
import requests
import json
import time

import requests.packages.urllib3 as urllib3
urllib3.disable_warnings()

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

user = 'user'
passwd = 'pass'

PACKET_LOGIN = '{"cmdID":1,"verifyCode":"","isCompressed":0,"rsaKey":{"n":"D6F1CFBF4D9F70710527E1B1911635460B1FF9AB7C202294D04A6F135A906E90E2398123C234340A3CEA0E5EFDCB4BCF7C613A5A52B96F59871D8AB9D240ABD4481CCFD758EC3F2FDD54A1D4D56BFFD5C4A95810A8CA25E87FDC752EFA047DF4710C7D67CA025A2DC3EA59B09A9F2E3A41D4A7EFBB31C738B35FFAAA5C6F4E6F","e":"010001"},"businessType":61,"passWord":"%s","loginType":0,"platformVersion":1,"verifyKey":"","sessionID":"","protocolVersion":100,"userName":"%s","extensionList":"","sequenceNo":10000001,"peerID":"%s","clientVersion":"1.0.0"}'
PACKET_LOGIN2 = '{"cmdID":3,"userID":%s,"platformVersion":1,"sessionID":"%s","protocolVersion":100,"isCompressed":0,"businessType":61,"extensionList":["imgURL"],"sequenceNo":10000006,"peerID":"%s","clientVersion":"1.0.0"}'
s = requests.Session()
g_headers = {'User-Agent': 'android-async-http/1.4.3 (http://loopj.com/android-async-http)'}
g_headers2 = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
g_cookies = {}
g_peerid = ''
g_userID = 0
g_totalnum = 0
g_totalbox = 0

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

    data = PACKET_LOGIN2 % (g_cookies['userid'], g_cookies['sessionid'], g_peerid)
    r = requests.post('https://login.mobile.reg2t.sandai.net:443/', data, verify=False, headers=g_headers)

def post_opengitf(id):
    data = 'id=%s' % id
    h = g_headers2.copy()
    h['X-Requested-With'] = 'XMLHttpRequest'
    r = requests.post('https://red.xunlei.com/index.php?r=usr/opengift', data, verify=False, headers=h, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('迅雷服务器小霸王中...')
    js = json.loads(r.text)
    if js['rd'] == 'ok':
        global g_totalnum
        global g_totalbox
        g_totalnum += js['gf']['num']
        g_totalbox += 1
        logging.info(('[领取钻石成功] 获得数量:%s 累计领取:%s 累计开箱:%s' % (js['gf']['num'], g_totalnum, g_totalbox)).decode('utf-8'))

def post_giftbox():
    data = 'p=0&ps=10&ni=&tp=0&t='
    r = requests.post('https://red.xunlei.com/index.php?r=usr/giftbox', data, verify=False, headers=g_headers2, cookies=g_cookies)
    if r.status_code != 200:
        raise Exception('迅雷服务器小霸王中...')
    js = json.loads(r.text)
    if 'ci' not in js:
        return
    for item in js['ci']:
        if item['st'] == 0:
            post_opengitf(item['id'])

login_sleep_min = 60
login_sleep = login_sleep_min
while True:
    try:
        login()
        login_sleep = login_sleep_min
        post_giftbox()
        logging.info(('[%s] 累计领取:%s 累计开箱:%s' % (time.strftime('%H:%M'), g_totalnum, g_totalbox)).decode('utf-8'))
        time.sleep(50 * 60)
    except:
        if login_sleep < 10 * 60:
            login_sleep += 60
        logging.warn(('[登录失败]:睡觉%s秒后再试' % (login_sleep)).decode('utf-8'))
        time.sleep(login_sleep)
