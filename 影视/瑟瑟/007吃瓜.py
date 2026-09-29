# -*- coding: utf-8 -*-
# @name 🌈 91吃瓜中心|终极完美版
# @version 1.0.0

import json
import re
import hashlib
from base64 import b64decode, b64encode
from urllib.parse import urlparse
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pyquery import PyQuery as pq
from spider_runner import OmniBox, run

img_cache = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
}
host = ""
proxies = {}

# 初始化获取可用域名
def init_host():
    global host
    dynamic_urls = ['https://but.vncchqw.cc/']
    for url in dynamic_urls:
        try:
            res = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            if res.status_code == 200:
                host = url
                headers.update({'Origin': host, 'Referer': f"{host}/"})
                return
        except:
            continue
    host = dynamic_urls[0]

init_host()

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载 91吃瓜首页")
    try:
        res = requests.get(host, headers=headers, proxies=proxies, timeout=15)
        data = pq(res.text)
        classes = []

        for sel in ['.category-list ul li', '.nav-menu li', '.menu li', 'nav ul li']:
            for k in data(sel).items():
                link = k('a')
                href = (link.attr('href') or '').strip()
                name = (link.text() or '').strip()
                if href and href != '#' and name:
                    classes.append({"type_id": href, "type_name": name})
            if classes: break

        if not classes:
            classes = [
                {"type_id": "/latest/", "type_name": "最新"},
                {"type_id": "/hot/", "type_name": "热门"}
            ]

        return {"class": classes, "list": getlist(data('#index article, article'))}
    except:
        return {"class": [], "list": []}

# ====================== 分类列表 ======================
async def category(params, context):
    category_id = params.get("categoryId") or ""
    page = params.get("page") or 1
    pg = int(page)

    try:
        if '@folder' in category_id:
            v = getfod(category_id.replace('@folder', ''))
            return {"page": pg, "pagecount": 1, "total": len(v), "list": v}

        if category_id.startswith('http'):
            base = category_id.rstrip('/')
        else:
            path = category_id if category_id.startswith('/') else f"/{category_id}"
            base = f"{host}{path}".rstrip('/')

        url = f"{base}/" if pg == 1 else f"{base}/{pg}/"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        data = pq(res.text)
        videos = getlist(data('#archive article, #index article, article'), category_id)

        return {"page": pg, "pagecount": 9999, "total": 999999, "list": videos}
    except:
        return {"page": pg, "pagecount": 9999, "total": 0, "list": []}

# ====================== 详情 ======================
async def detail(params, context):
    video_id = params.get("videoId")
    if not video_id:
        return {"list": []}

    try:
        url = video_id if video_id.startswith('http') else f"{host}{video_id}"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        data = pq(res.text)
        plist = []
        used = set()

        # 解析 dplayer 视频
        for i, k in enumerate(data('.dplayer').items(), 1):
            try:
                cfg = json.loads(k.attr('data-config'))
                u = cfg.get('video', {}).get('url', '')
                if not u: continue
                name = f"视频{i}"
                plist.append({"name": name, "playId": u})
            except:
                continue

        # 解析页面链接
        if not plist:
            area = data('.post-content, article')
            for i, a in enumerate(area('a').items(), 1):
                txt = a.text().strip()
                href = a.attr('href')
                if href and any(x in txt for x in ['观看', '播放', '视频', '弹']):
                    name = txt.replace('点击观看：', '') or f"视频{i}"
                    if not href.startswith('http'):
                        href = f"{host}{href}" if href.startswith('/') else f"{host}/{href}"
                    plist.append({"name": name, "playId": href})

        if not plist:
            plist = [{"name": "默认线路", "playId": url}]

        return {
            "list": [{
                "vod_id": video_id,
                "vod_name": data('h1').text() or "91吃瓜中心",
                "vod_pic": "",
                "vod_content": data('.post-title').text() or "91吃瓜中心",
                "vod_year": "",
                "vod_remarks": "",
                "vod_douban_score": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_area": "",
                "vod_play_sources": [{
                    "name": "91吃瓜中心",
                    "episodes": plist
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 搜索 ======================
async def search(params, context):
    keyword = (params.get("keyword") or params.get("wd") or "").strip()
    page = int(params.get("page") or 1)
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    try:
        url = f"{host}/search/{keyword}/" if page == 1 else f"{host}/search/{keyword}/{page}/"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        data = pq(res.text)
        videos = getlist(data('article'))
        return {"page": page, "pagecount": 9999, "total": 999999, "list": videos}
    except:
        return {"page": page, "pagecount": 0, "total": 0, "list": []}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    parse = 0 if isVideoFormat(play_id) else 1
    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": headers,
        "parse": parse
    }

# ====================== 工具函数（全部保留） ======================
def isVideoFormat(url):
    return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

def getlist(data, tid=''):
    videos = []
    folder = '/mrdg' in (tid or '')
    for k in data.items():
        a = k if k.is_('a') else k('a').eq(0)
        href = a.attr('href')
        title = k('h2').text() or k('.entry-title').text() or k('.post-title').text() or k.text()
        if not href or not title: continue
        img = getimg('', k, k.outer_html())
        videos.append({
            "vod_id": f"{href}{'@folder' if folder else ''}",
            "vod_name": title.strip(),
            "vod_pic": img,
            "type_id": "",
            "type_name": "",
            "vod_remarks": k('time').text() or "",
            "vod_year": "",
            "vod_douban_score": ""
        })
    return videos

def getfod(id):
    url = f"{host}{id}"
    data = pq(requests.get(url, headers=headers, proxies=proxies).text)
    v = []
    for i, h2 in enumerate(data('.post-content h2').items()):
        pt = data('.post-content p').eq(i*2)
        pi = data('.post-content p').eq(i*2+1)
        v.append({
            "vod_id": pt('a').attr('href'),
            "vod_name": pt.text().strip(),
            "vod_pic": getimg('', pi, pi.outer_html()),
            "type_id": "", "type_name": "",
            "vod_remarks": h2.text().strip(),
            "vod_year": "", "vod_douban_score": ""
        })
    return v

def getimg(t, elem=None, html=''):
    if not html and elem: html = elem.outer_html()
    if m := re.search(r"loadBannerDirect\('([^']+)'", t):
        return proc_url(m.group(1))
    if m := re.search(r'(https?://[^"\'\s]+\.(jpg|png|jpeg|webp))', html, re.I):
        return proc_url(m.group(1))
    return ''

def proc_url(url):
    if not url: return ''
    url = url.strip('\'" ')
    if not url.startswith('http'):
        url = f"{host}{url}" if url.startswith('/') else f"{host}/{url}"
    return url

# ====================== 启动 ======================
if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
