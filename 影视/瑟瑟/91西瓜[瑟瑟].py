# -*- coding: utf-8 -*-
# @name 🌈 51吸瓜
# @version 1.0.0

import json
import random
import re
import threading
import time
from base64 import b64decode, b64encode
from urllib.parse import urlparse

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pyquery import PyQuery as pq
from spider_runner import OmniBox, run

# ====================== 全局配置 ======================
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
}
proxies = {}

def get_working_host():
    dynamic_urls = [
        'https://artist.vgwtswi.xyz',
        'https://ability.vgwtswi.xyz',
        'https://am.vgwtswi.xyz'
    ]
    for url in dynamic_urls:
        try:
            res = requests.get(url, headers=headers, proxies=proxies, timeout=8)
            if res.status_code == 200:
                if len(pq(res.text)('#index article a')) > 0:
                    return url
        except:
            continue
    return dynamic_urls[0]

host = get_working_host()
headers.update({'Origin': host, 'Referer': f"{host}/"})

# ====================== 工具函数 ======================
def getpq(data):
    try:
        return pq(data)
    except:
        return pq(data.encode('utf-8'))

def e64(text):
    try:
        return b64encode(text.encode()).decode()
    except:
        return ""

def d64(encoded):
    try:
        return b64decode(encoded).decode()
    except:
        return ""

def aesimg(word):
    key = b'f5d965df75336270'
    iv = b'97b60394abc2fbe1'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(word), AES.block_size)

def getProxyUrl():
    return ""

def proxy(data, typ='m3u8'):
    if data and proxies:
        return f"{getProxyUrl()}&url={e64(data)}&type={typ}"
    return data

def isVideoFormat(url):
    return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

def getimg(text):
    match = re.search(r"loadBannerDirect\('([^']+)'", text)
    if match:
        return f"{getProxyUrl()}&url={match.group(1)}&type=img"
    return ''

def getlist(data, tid=''):
    videos = []
    l = '/mrdg' in tid
    for k in data.items():
        a = k.attr('href')
        b = k('h2').text()
        c = k('span[itemprop="datePublished"]').text() or k('.post-meta, .entry-meta, time').text()
        if a and b:
            videos.append({
                "vod_id": f"{a}{'@folder' if l else ''}",
                "vod_name": b.replace('\n', ' '),
                "vod_pic": getimg(k('script').text()),
                "vod_remarks": c or '',
                "type_id": "", "type_name": "",
                "vod_year": "", "vod_douban_score": ""
            })
    return videos

def getfod(id):
    url = f"{host}{id}"
    data = getpq(requests.get(url, headers=headers, proxies=proxies).text)
    vdata = data('.post-content[itemprop="articleBody"]')
    for i in ['.txt-apps','.line','blockquote','.tags','.content-tabs']:
        vdata.remove(i)
    p = vdata('p')
    videos = []
    for i, x in enumerate(vdata('h2').items()):
        c = i*2
        videos.append({
            "vod_id": p.eq(c)('a').attr('href'),
            "vod_name": p.eq(c).text(),
            "vod_pic": f"{getProxyUrl()}&url={p.eq(c+1)('img').attr('data-xkrkllgl')}&type=img",
            "vod_remarks": x.text(),
            "type_id": "", "type_name": "",
            "vod_year": "", "vod_douban_score": ""
        })
    return videos

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载51吸瓜")
    try:
        res = requests.get(host, headers=headers, proxies=proxies, timeout=15)
        data = getpq(res.text)
        classes = []
        for s in ['.category-list ul li', '.nav-menu li', '.menu li', 'nav ul li']:
            for k in data(s).items():
                link = k('a')
                href = link.attr('href') or ''
                name = link.text().strip() or ''
                if href and href != '#' and name:
                    classes.append({"type_name": name, "type_id": href})
            if classes: break
        if not classes:
            classes = [
                {"type_name": "首页", "type_id": "/"},
                {"type_name": "最新", "type_id": "/latest/"},
                {"type_name": "热门", "type_id": "/hot/"}
            ]
        return {"class": classes, "list": getlist(data('#index article a'))}
    except:
        return {"class": [], "list": []}

# ====================== 分类 ======================
async def category(params, context):
    tid = params.get("categoryId", "/")
    pg = params.get("page", 1)
    try:
        if '@folder' in tid:
            videos = getfod(tid.replace('@folder', ''))
        else:
            if tid.startswith('/'):
                url = f"{host}{tid}page/{pg}/" if pg != 1 else f"{host}{tid}"
            else:
                url = f"{host}/{tid}"
            res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            data = getpq(res.text)
            videos = getlist(data('#archive article a, #index article a'), tid)
        return {
            "page": int(pg),
            "pagecount": 1 if '@folder' in tid else 99999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}

# ====================== 详情（新版标准格式） ======================
async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}
    try:
        url = f"{host}{vid}" if not vid.startswith('http') else vid
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        data = getpq(res.text)

        clist = []
        for k in data('.tags .keywords a').items():
            t = k.text()
            if t: clist.append(t)
        content = ' '.join(clist) or data('.post-title').text() or '51吸瓜视频'

        episodes = []
        used = set()
        for i, k in enumerate(data('.dplayer').items(), 1):
            cfg = k.attr('data-config')
            if not cfg: continue
            try:
                u = json.loads(cfg)['video']['url']
                n = f"视频{i}"
                while n in used:
                    n = f"视频{i}_{random.randint(10,99)}"
                used.add(n)
                episodes.append({"name": n, "playId": u})
            except:
                continue
        if not episodes:
            episodes.append({"name": "默认", "playId": url})

        return {
            "list": [{
                "vod_id": vid,
                "vod_name": data('.post-title').text() or "视频",
                "vod_pic": "",
                "vod_content": content,
                "vod_year": "", "vod_remarks": "",
                "vod_douban_score": "", "vod_actor": "",
                "vod_director": "", "vod_area": "",
                "vod_play_sources": [{
                    "name": "51吸瓜",
                    "episodes": episodes
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 搜索 ======================
async def search(params, context):
    key = (params.get("keyword") or params.get("wd") or "").strip()
    pg = params.get("page", 1)
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    try:
        url = f"{host}/search/{key}/{pg}" if pg != 1 else f"{host}/search/{key}/"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        data = getpq(res.text)
        videos = getlist(data('#archive article a, #index article a'))
        return {"page": int(pg), "pagecount": 1, "total": len(videos), "list": videos}
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    url = play_id
    p = 1
    if isVideoFormat(url):
        if '.m3u8' in url:
            url = proxy(url)
        p = 0

    return {
        "urls": [{"name": "播放", "url": url}],
        "flag": "play",
        "header": headers,
        "parse": p
    }

# ====================== 启动 ======================
if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
