# -*- coding: utf-8 -*-
# @name AV3698
# @version 1.0.0
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/AV3698[瑟瑟].py

import json
import re
import urllib.parse
import urllib.request

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    requests = None

try:
    import sys
    sys.path.append('..')
    from base.spider import Spider as BaseSpider
except ImportError:
    BaseSpider = object

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
HOST = 'https://av3698.cc'
FALLBACK_HOSTS = [
    'https://av3698.cc',
    'https://www.av3698.cc',
]

FALLBACK_CLASSES = [
    ('日韩无码', 54, '54'),
    ('国产主播', 55, '55'),
    ('日韩精品', 57, '57'),
    ('欧美劲爆', 58, '58'),
    ('成人动漫', 59, '59'),
    ('自拍偷拍', 60, '60'),
    ('伦理影片', 61, '61'),
    ('视频二区', 69, '69'),
    ('巨乳尤物', 70, '70'),
    ('颜射系列', 71, '71'),
    ('口交视频', 72, '72'),
    ('自慰系列', 73, '73'),
    ('教师学生', 74, '74'),
    ('群P换妻', 75, '75'),
    ('AI换脸', 76, '76'),
    ('视频三区', 56, '56'),
    ('中文字幕', 62, '62'),
    ('人妻系列', 63, '63'),
    ('制服诱惑', 64, '64'),
    ('强奸乱伦', 65, '65'),
    ('无码流出', 66, '66'),
    ('主播诱惑', 67, '67'),
    ('在线观看', 68, '68'),
    ('视频四区', 77, '77'),
    ('熟女专区', 78, '78'),
    ('欧美专区', 79, '79'),
    ('调教捆绑', 80, '80'),
    ('情趣丝袜', 81, '81'),
]

_session = None


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
    return _session


def _http_get(url, timeout=15):
    """GET 页面内容，优先 requests，失败后回退 urllib"""
    if requests is not None:
        try:
            return _get_session().get(url, timeout=timeout, verify=False).text
        except Exception:
            pass
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


class Spider(BaseSpider):
    host = HOST
    name = 'AV3698'

    def init(self, cfg):
        pass

    def getName(self):
        return self.name

    def isVideoFormat(self, url):
        if not url:
            return False
        return '.m3u8' in url or '.mp4' in url

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def localProxy(self, param):
        if not param or not param.startswith('http'):
            return [500, 'text/plain', '']
        try:
            req = urllib.request.Request(param, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=20)
            data = resp.read()
            ctype = resp.headers.get('Content-Type', 'application/octet-stream')
            return [200, ctype, data]
        except Exception as e:
            return [502, 'text/plain', str(e).encode()]

    def _get_host(self):
        for h in FALLBACK_HOSTS:
            try:
                html = _http_get(h + '/', timeout=5)
                if html:
                    return h
            except Exception:
                continue
        return HOST

    def _cat_id(self, tid):
        try:
            tid = int(str(tid).split(':')[-1])
        except Exception:
            return None
        for _, cid, ckey in FALLBACK_CLASSES:
            if cid == tid or ckey == str(tid):
                return str(ckey)
        return None

    def _parse_cards(self, html):
        items = []
        for m in re.finditer(r'<article class="media-card">([\s\S]*?)</article>', html):
            box = m.group(1)
            href_match = re.search(r'href="(/xwatch/\d+)"', box)
            if not href_match:
                continue
            vid = href_match.group(1)
            title_match = re.search(r'class="card-title"[^>]*>([^<]+)</a>', box)
            title = title_match.group(1).strip() if title_match else vid
            pic_match = re.search(r'<img[^>]+src="([^"]+)"', box)
            pic = pic_match.group(1) if pic_match else ''
            remark_match = re.search(r'class="duration"[^>]*>([^<]+)<', box)
            remark = remark_match.group(1).strip() if remark_match else ''
            if 'cached-thumb?url=' in pic:
                u = re.search(r'url=([^&"]+)', pic)
                if u:
                    pic = urllib.parse.unquote(u.group(1))
            items.append({
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': remark,
            })
        return items

    def homeContent(self, filter=False):
        host = self._get_host()
        classes = [{'type_id': str(cid), 'type_name': name} for name, cid, _ in FALLBACK_CLASSES]
        html = _http_get(host + '/')
        items = self._parse_cards(html)
        if not items:
            html = _http_get(host + '/?source=external&category=54')
            items = self._parse_cards(html)
        return {'class': classes, 'filters': {}, 'list': items}

    def homeVideoContent(self):
        host = self._get_host()
        html = _http_get(host + '/')
        return {'list': self._parse_cards(html)}

    def categoryContent(self, tid, pg=1, filter=False, extend=''):
        host = self._get_host()
        cat_id = self._cat_id(tid)
        if cat_id is None:
            return {'list': [], 'page': 1, 'pagecount': 1}

        url = f'{host}/?q=&source=external&category={cat_id}&page={pg}'
        html = _http_get(url)
        items = self._parse_cards(html)

        pagecount = 1
        m = re.search(r'第\s*(\d+)\s*/\s*(\d+)\s*页', html)
        if m:
            pagecount = max(1, int(m.group(2)))

        return {'list': items, 'page': int(pg), 'pagecount': pagecount}

    def detailContent(self, ids):
        host = self._get_host()
        try:
            did = str(ids[0] if isinstance(ids, list) else ids)
        except Exception:
            return {'list': []}
        if not did.startswith('/'):
            did = '/xwatch/' + did
        html = _http_get(host + did)
        if not html:
            return {'list': []}

        title_match = re.search(r'<title>([^<]+)', html)
        title = title_match.group(1).replace(' · av3698.cc', '').strip() if title_match else did

        stream = ''
        m = re.search(r'data-stream="([^"]+)"', html)
        if m:
            stream = m.group(1)
        if not stream:
            m2 = re.search(r'https?://[^"\'\s\\]+\.m3u8[^"\'\s\\]*', html)
            if m2:
                stream = m2.group(0)

        pic = ''
        pm = re.search(r'poster="([^"]+)"', html)
        if pm:
            pic = pm.group(1)

        if not stream:
            return {'list': []}

        vod = {
            'vod_id': did,
            'vod_name': title or did,
            'vod_pic': pic,
            'vod_content': title or did,
            'vod_play_from': 'av3698',
            'vod_play_url': f'直链${stream}',
            'vod_remarks': 'M3U8',
        }
        return {'list': [vod]}

    def searchContent(self, key, quick=False, pg=1):
        host = self._get_host()
        kw = urllib.parse.quote(key)
        url = f'{host}/?q={kw}'
        html = _http_get(url)
        items = self._parse_cards(html)
        if not items:
            url = f'{host}/?source=home&q={kw}'
            html = _http_get(url)
            items = self._parse_cards(html)
        return {'list': items}

    def playerContent(self, flag, id, vipFlags=None):
        return {
            'parse': 0,
            'url': id,
            'jx': 0,
            'header': {
                'User-Agent': UA,
                'Referer': HOST + '/',
            }
        }


if __name__ == '__main__':
    sp = Spider()
    print('=== 分类 ===')
    print(len(sp.homeContent(True)['class']))
    print('=== 分类列表 ===')
    cc = sp.categoryContent('54', 1, {}, '')
    print('count=', len(cc['list']), 'pagecount=', cc['pagecount'])
    if cc['list']:
        print(cc['list'][0]['vod_name'])
        d = sp.detailContent([cc['list'][0]['vod_id']])
        print(d['list'][0]['vod_play_url'][:80] if d['list'] else 'no detail')
