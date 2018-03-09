#coding=utf-8

import base64
import utils
import json
import hashlib
import urllib, urllib2
import re
import os
import time
import tempfile
import random
import xml.dom.minidom as minidom
from cookielib import MozillaCookieJar
import requests
# from bs4 import BeautifulSoup
from bilibili_config import *
from xbmcswift2 import xbmc

class Bilibili():
    def __init__(self, appkey = APPKEY, appsecret = APPSECRET):
        self.appkey = appkey
        self.appsecret = appsecret
        self.is_login = False
        cookie_path = os.path.dirname(os.path.abspath(__file__)) + '/.cookie'
        self.cj = MozillaCookieJar(cookie_path)
        if os.path.isfile(cookie_path):
            self.cj.load()
            if requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
                self.is_login = True
                self.mid = str(requests.utils.dict_from_cookiejar(self.cj)['DedeUserID'])
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)

    def get_captcha(self, path = None):
        if not requests.utils.dict_from_cookiejar(self.cj).has_key('sid'):
            utils.get_page_content(LOGIN_CAPTCHA_URL.format(random.random()),
                                   headers = {'Referer':'https://passport.bilibili.com/login'})
        result = utils.get_page_content(LOGIN_CAPTCHA_URL.format(random.random()),
                                        headers = {'Referer':'https://passport.bilibili.com/login'})
        if path == None:
            path = tempfile.gettempdir() + '/captcha.jpg'
        with open(path, 'wb') as f:
            f.write(result)
        return path

    def get_encryped_pwd(self, pwd):
        import rsa
        result = json.loads(utils.get_page_content(LOGIN_HASH_URL.format(random.random()),
                                                   headers={'Referer':'https://passport.bilibili.com/login'}))
        pwd = result['hash'] + pwd
        key = result['key']
        pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(key)
        pwd = rsa.encrypt(pwd.encode('utf-8'), pub_key)
        pwd = base64.b64encode(pwd)
        pwd = urllib.quote(pwd)
        return pwd

    def api_sign(self, params):
        params['appkey']=self.appkey
        data = ""
        keys = params.keys()
        keys.sort()
        for key in keys:
            if data != "":
                data += "&"
            value = params[key]
            if type(value) == int:
                value = str(value)
            data += key + "=" + str(urllib.quote(value))
        if self.appsecret == None:
            return data
        m = hashlib.md5()
        m.update(data + self.appsecret)
        return data + '&sign=' + m.hexdigest()

    # def get_category_from_web_page(self):
    #     category_dict = {'0': {'title': u'全部', 'url': HOME_URL, 'subs':[]}}
    #     node = category_dict['0']
    #     url = node['url']
    #     result = BeautifulSoup(utils.get_page_content(url), "html.parser").findAll('li', {'class': 'm-i'})
    #     for item in result:
    #         if len(item['class']) != 1:
    #             continue
    #         tid = item['data-tid']
    #         title = item.em.contents[0]
    #         url = 'http:' + item.a['href']
    #         category_dict[tid] = {'title': title, 'url': url, 'subs':[]}
    #         node['subs'].append(tid)

    #     #Fix video and movie
    #     if '11' not in category_dict['0']['subs']:
    #         category_dict['0']['subs'].append('11')
    #     if '23' not in category_dict['0']['subs']:
    #         category_dict['0']['subs'].append('23')
    #     category_dict['11'] = {'title': u'电视剧', 'url': 'http://bangumi.bilibili.com/tv/', 'subs': []}
    #     category_dict['23'] = {'title': u'电影', 'url': 'http://bangumi.bilibili.com/movie/', 'subs': []}

    #     for sub in category_dict['0']['subs']:
    #         node = category_dict[sub]
    #         url = node['url']
    #         result = BeautifulSoup(utils.get_page_content(url), "html.parser").select('ul.n_num li')
    #         for item in result[1:]:
    #             if not item.has_attr('tid'):
    #                 continue
    #             if not hasattr(item, 'a'):
    #                 continue
    #             if item.has_attr('class'):
    #                 continue
    #             tid = item['tid']
    #             title = item.a.contents[0]
    #             if item.a['href'][:2] == '//':
    #                 url = 'http:' + item.a['href']
    #             else:
    #                 url = HOME_URL + item.a['href']
    #             category_dict[tid] = {'title': title, 'url': url, 'subs':[]}
    #             node['subs'].append(tid)
    #     return category_dict

    # def get_category(self, tid = '0'):
    #     items = [{tid: {'tit19le': '全部', 'url': CATEGORY[tid]['url'], 'subs': []}}]
    #     for sub in CATEGORY[tid]['subs']:
    #         items.append({sub: CATEGORY[sub]})
    #     return items

    # def get_category_name(self, tid):
    #     return CATEGORY[str(tid)]['title']

    # def get_order(self):
    #     return ORDER

    # def get_category_list(self, tid = 0, order = 'default', days = 30, page = 1, pagesize = 10):
    #     params = {'tid': tid, 'order': order, 'days': days, 'page': page, 'pagesize': pagesize}
    #     url = LIST_URL.format(self.api_sign(params))
    #     result = json.loads(utils.get_page_content(url))
    #     xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
    #     results = []
    #     for i in range(pagesize):
    #         if result['list'].has_key(str(i)):
    #             results.append(result['list'][str(i)])
    #         else:
    #             break
    #     return results, result['pages']

    # def get_my_info(self):
    #     if self.is_login == False:
    #         return []
    #     result = json.loads(utils.get_page_content(MY_INFO_URL))
    #     xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
    #     return result['data']

    def get_bangumi_chase(self, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = BANGUMI_CHASE_URL.format(self.mid, page, pagesize)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result['data']['result'], result['data']['pages']

    def get_bangumi_detail(self, season_id):
        url = BILIPLUS_BANGUMI_URL.format(season_id)
        result = utils.get_page_content(url)
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        xbmc.log('---------------from season id: '+str(season_id), xbmc.LOGWARNING)
        # if result[0] != '{':
        #     start = result.find('(') + 1
        #     end = result.find(');')
        #     result = result[start:end]
        result = json.loads(result)
        return result['result']

    def get_history(self, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = HISTORY_URL.format(page, pagesize)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        if len(result['data']) >= int(pagesize):
            total_page = int(page) + 1
        else:
            total_page = int(page)
        return result['data'], total_page

    def get_watch_later(self, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = WATCH_LATER_URL.format(page, pagesize, int(time.time() * 1000))
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        total_page = result['data']['count'] / pagesize + 1
        return result['data']['list'], total_page

    def get_dynamic(self, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = DYNAMIC_URL.format(pagesize, page)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        total_page = int((result['data']['page']['count'] + pagesize - 1) / pagesize)
        return result['data']['feeds'], total_page

    def get_attention(self, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = ATTENTION_URL.format(self.mid, page, pagesize)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        url2 = STAT_URL.format(self.mid)
        result2 = json.loads(utils.get_page_content(url2))
        xbmc.log('---------------2'+json.dumps(result2), xbmc.LOGWARNING)
        total_page = result2['data']['following'] / pagesize + 1
        return result['data']['list'], total_page

    def get_attention_video(self, mid, tid = 0, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = ATTENTION_VIDEO_URL.format(mid, page, pagesize, tid)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result['data'], result['data']['pages']

    # def get_attention_channel(self, mid):
    #     if self.is_login == False:
    #         return []
    #     url = ATTENTION_CHANNEL_URL.format(mid)
    #     result = json.loads(utils.get_page_content(url))
    #     xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
    #     return result['data']['list']

    # def get_attention_channel_list(self, mid, cid, page = 1, pagesize = 10):
    #     if self.is_login == False:
    #         return []
    #     url = ATTENTION_CHANNEL_LIST_URL.format(mid, cid, page, pagesize)
    #     result = json.loads(utils.get_page_content(url))
    #     xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
    #     return result['data']['list'], result['data']['total']

    def get_fav_box(self):
        if self.is_login == False:
            return []
        url = FAV_BOX_URL.format(self.mid)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result['data']['list']

    def get_fav(self, fav_box, page = 1, pagesize = 10):
        if self.is_login == False:
            return []
        url = FAV_URL.format(self.mid, page, pagesize, fav_box)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result['data']['vlist'], result['data']['pages']

    def login(self, userid, pwd, captcha):
        #utils.get_page_content('http://www.bilibili.com')
        if self.is_login == True:
            return True, ''
        pwd = self.get_encryped_pwd(pwd)
        data = 'cType=2&vcType=1&captcha={}&user={}&pwd={}&keep=true&gourl=http://www.bilibili.com/'.format(captcha, userid, pwd)
        result = utils.get_page_content(LOGIN_URL, data,
                                        {'Origin':'https://passport.bilibili.com',
                                         'Referer':'https://passport.bilibili.com/login'})
        if not requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
            return False, LOGIN_ERROR_MAP[json.loads(result)['code']]
        self.cj.save()
        self.is_login = True
        self.mid = str(requests.utils.dict_from_cookiejar(self.cj)['DedeUserID'])
        return True, ''

    def logout(self):
        self.cj.clear()
        self.cj.save()
        self.is_login = False

    def get_av_detail(self, aid, page = 1):
        params = {'id': aid, 'page': page}
        url = VIEW_URL.format(self.api_sign(params))
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result

    def get_av_list(self, aid):
        url = AV_URL.format(aid)
        result = json.loads(utils.get_page_content(url))
        xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        return result

    def get_av_pages_info(self, aid):
        url = BILIPLUS_VIEW_URL.format(str(aid))
        xml = utils.get_page_content(url)
        try:
            result = json.loads(xml)
            xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        except:
            xbmc.log('---------------'+xml, xbmc.LOGWARNING)
            xbmc.executebuiltin('Notification(BiliPlus API Error,Something\'s wrong. Retry later.,5000)')
            time.sleep(5)
            return
        return result['v2_app_api']['pages']

    def get_video_urls(self, aid, page, vtype):    # switched over to biliplus api for getting the direct video links
        code = self.vtype_code(aid, page, vtype)
        # if code not in [0, 1, 2, None]:
        #     return [self.get_biliplus_video_url(code)]
        url = BILIPLUS_GETURL_URL.format(str(aid), page, str(code))
        xml = utils.get_page_content(url)
        try:
            result = json.loads(xml)
            xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
        except:
            xbmc.log('---------------'+xml, xbmc.LOGWARNING)
            xbmc.executebuiltin('Notification(BiliPlus API Error,Something\'s wrong. Retry later.,5000)')
            time.sleep(5)
            return []
        maximum_quality = 720 # 1080, 720, 480, 360, 240
        data = result['data']
        for x in data:
            x['quality'] = int(re.search('x(\d+)', x['info']).group(1))
        data = sorted(data, key=(lambda x: x['quality']), reverse=True)
        for item in data:
            if item['quality'] <= maximum_quality:
                if item['type'] == 'split':
                    video_urls = map((lambda x: x['url']), item['parts'])
                elif item['type'] == 'single':
                    video_urls = [item['url']]
                else:
                    video_urls = []
                return video_urls
        return []

    def vtype_code(self, aid, page, type_text):
        if type_text == u'vupload':
          return 0
        elif type_text == u'bangumi':
          return 1
        elif type_text == u'movie':
          return 2
        elif type_text == u'null':
            url = BILIPLUS_VIEW_URL.format(str(aid))
            xml = utils.get_page_content(url)
            try:
                result = json.loads(xml)
                xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
            except:
                xbmc.log('---------------'+xml, xbmc.LOGWARNING)
                xbmc.executebuiltin('Notification(BiliPlus API Error,Something\'s wrong. Retry later.,5000)')
                time.sleep(5)
                return None
            # if result['v2_app_api']['rights']['pay'] == 1:
            #     for item in result['v2_app_api']['pages']:
            #         if item['page'] == 1:
            #             return int(re.search('(\d+).xml',item['dmlink']).group(1))
            for item in result['v2_app_api']['pages']:
                if item['page'] == int(page):
                    return self.vtype_code(aid, page, item['from'])
        return None

    # def get_biliplus_video_url(self, cid):
    #     url = BILIPLUS_PLAYURL_URL.format(str(cid))
    #     xml = utils.get_page_content(url)
    #     xbmc.log('---------------'+xml, xbmc.LOGWARNING)
    #     return re.search('<a href="([^"]*)', xml).group(1)


    # def add_history(self, aid, cid):
    #     url = ADD_HISTORY_URL.format(str(cid), str(aid))
    #     utils.get_page_content(url)

    # def get_av_num_info(self, aid):
    #     url = BILIPLUS_VIEW_URL.format(str(aid))
    #     xml = utils.get_page_content(url)
    #     try:
    #         result = json.loads(xml)
    #         xbmc.log('---------------'+json.dumps(result), xbmc.LOGWARNING)
    #     except:
    #         xbmc.log('---------------'+xml, xbmc.LOGWARNING)
    #         xbmc.executebuiltin('Notification(BiliPlus API Error,Something\'s wrong. Retry later.,5000)')
    #         return

    #     item = {
    #         'thumbnail': result['v2_app_api']['pic'],
    #         'label': result['v2_app_api']['title'],
    #         'pages': []
    #         }
    #     item['info'] = {
    #         'genre': result['v2_app_api']['tname'],
    #         'plot': result['v2_app_api']['desc'],
    #         'duration': result['v2_app_api']['duration'],
    #         'writer': result['v2_app_api']['owner']['name'],
    #         'year': int((result['created_at'].split('/'))[0])
    #         }
    #     for page in result['v2_app_api']['pages']:
    #         d = {
    #             'page': page['page'],
    #             'label': page['part'],
    #             'vtype': self.vtype_code(aid, page['page'], page['from'])
    #             }
    #         try:
    #             d['duration'] = page['duration']
    #         except:
    #             pass
    #         item['pages'].append(d)
    #     return item


if __name__ == '__main__':
    b = Bilibili()
    #if b.is_login == False:
    #    b.get_captcha('')
    #    captcha = raw_input('Captcha: ')
    #    print b.login(u'catro@foxmail.com', u'123456', captcha)
    #print b.get_fav(49890104)
    #print b.get_av_list(8163111)
    #print b.add_history(8163111, 13425238)
    #print b.get_video_urls(12821893)
    #print b.get_category_list('32')
    #print b.get_dynamic('2')[1]
    #print b.get_category()
    #print b.get_bangumi_chase()
    #print b.get_attention()
    #print b.get_attention_video('7349', 0, 1, 1)
    #print b.get_attention_channel('7349')
    #print json.dumps(b.get_bangumi_detail('5800'), indent=4, ensure_ascii=False)
    #print b.get_bangumi_detail('5800')
    #print b.get_history(1)
    #with open('bilibili_config.py', 'a') as f:
    #    f.write('\nCATEGORY = ')
    #    f.write(json.dumps(b.get_category_from_web_page(), indent=4, ensure_ascii=False).encode('utf8'))
