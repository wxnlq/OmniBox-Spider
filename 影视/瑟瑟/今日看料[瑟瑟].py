# -*- coding: utf-8 -*-
# @name 🌈 今日看料
# @version 1.0.0
# 修复：数据正常 + 每个视频显示真实封面

import json
import random
import re
import time
from base64 import b64decode, b64encode
from urllib.parse import urlparse, quote
import requests
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

# ====================== 自动优选可用域名 ======================
def get_working_host():
    dynamic_urls = [
        'https://kanliao25.com/',
        'https://kanliao7.org/',
        'https://kanliao7.net/',
        'https://kanliao14.com/'
    ]
    for url in dynamic_urls:
        try:
            res = requests.get(url, headers=headers, proxies=proxies, timeout=8)
            if res.status_code == 200:
                if len(pq(res.text)('#index article a')) > 0:
                    return url.rstrip('/')
        except:
            continue
    return dynamic_urls[0].rstrip('/')

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

def isVideoFormat(url):
    return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

def is_advertisement(elem):
    hot = elem.find('.wraps')
    for i in hot.items():
        if '热搜HOT' in i.text():
            return True
    title = (elem('h2').text() or elem('.post-card-title').text() or '').lower()
    ad = ['热搜hot', 'dns', 'wifi', '手机链接']
    if any(k in title for k in ad):
        return True
    return False

# ====================== ✅ 唯一修复：封面抓取 ======================
def get_article_img(elem):
    try:
        html = str(elem)
        match = re.search(r'https?://[^"\']+/usr/uploads/[^"\']+\.(jpg|png|webp)', html)
        if match:
            return match.group(0)
            
        match = re.search(r'/usr/uploads/[^"\']+\.(jpg|png|webp)', html)
        if match:
            return host + match.group(0)
    except:
        pass
    return ""
# ====================== 列表（完全恢复你原本能跑的代码） ======================
def getlist(data):
    v = []
    for k in data.items():
        if is_advertisement(k):
            continue
        a = k.attr('href')
        b = k('h2').text() or k('.post-card-title').text() or k.text()
        c = k('span[itemprop="datePublished"]').text() or k('.post-meta').text()
        if a and b:
            vid = a if a.startswith('http') else ('/' + a.lstrip('/'))
            v.append({
                "vod_id": vid,
                "vod_name": b.replace('\n', ' ').strip(),
                "vod_pic": get_article_img(k),
                "vod_remarks": c.strip() if c else '',
                "type_id": "", "type_name": "",
                "vod_year": "", "vod_douban_score": ""
            })
    return v

def detect_page_count(data):
    nums = []
    for s in ['.page-navigator a', '.pagination a', '.page-numbers a']:
        for i in data(s).items():
            h = i.attr('href')
            t = i.text().strip()
            m = re.search(r'/(\d+)/?$', h.rstrip('/'))
            if m:
                nums.append(int(m.group(1)))
            if t and t.isdigit():
                nums.append(int(t))
    if nums:
        return max(nums)
    if data('.next,.next-page,a:contains("下一页")'):
        return 99999
    return 99999

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载 今日看料")
    try:
        res = requests.get(host, headers=headers, proxies=proxies, timeout=15)
        doc = getpq(res.text)
        cls = []
        for s in ['#navbarCollapse .nav-link', '.navbar-nav .nav-link']:
            for i in doc(s).items():
                h = i.attr('href') or ''
                n = i.text().strip()
                if h and n and '/category/' in h:
                    cls.append({"type_name": n, "type_id": h})
        if not cls:
            cls = [
                {"type_name": "热点关注", "type_id": "/category/rdgz/"},
                {"type_name": "抖音", "type_id": "/category/dy/"},
                {"type_name": "快手", "type_id": "/category/ks/"},
                {"type_name": "斗鱼", "type_id": "/category/douyu/"},
                {"type_name": "虎牙", "type_id": "/category/hy/"},
            ]
        return {"class": cls, "list": getlist(doc('#index article a,#archive article a'))}
    except:
        return {"class": [], "list": []}

# ====================== 分类 ======================
async def category(params, context):
    tid = params.get("categoryId", "")
    pg = params.get("page", 1)
    try:
        url = f"{host}{tid.rstrip('/')}/{pg}/" if pg != 1 else f"{host}{tid}"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        doc = getpq(res.text)
        v = getlist(doc('#archive article a,#index article a,.post-card'))
        pc = detect_page_count(doc)
        return {
            "page": int(pg),
            "pagecount": pc,
            "total": 999999,
            "list": v
        }
    except:
        return {"page":1,"pagecount":1,"total":0,"list":[]}

# ====================== 搜索 ======================
async def search(params, context):
    key = (params.get("keyword") or "").strip()
    pg = params.get("page", 1)
    if not key:
        return {"list": []}
    try:
        url = f"{host}/tag/{quote(key)}/{pg}/"
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        doc = getpq(res.text)
        v = getlist(doc('#archive article a,#index article a'))
        return {"list": v, "page": int(pg)}
    except:
        return {"list": []}

# ====================== 详情 ======================
async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}
    try:
        url = host + vid if not vid.startswith("http") else vid
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        doc = getpq(res.text)
        title = doc('.post-title,h1.entry-title').text().strip() or '今日看料视频'
        content = doc('.post-content').text() or title
        eps = []

        for i, p in enumerate(doc('.dplayer').items(), 1):
            cfg = p.attr('data-config')
            if cfg:
                u = json.loads(cfg).get('video', {}).get('url', '')
                if u:
                    eps.append({"name": f"视频{i}", "playId": u})

        if not eps:
            for s in ['video source', 'video', 'iframe[src*=video]', 'a[href*=m3u8]']:
                for i, e in enumerate(doc(s).items(), 1):
                    u = e.attr('src') or e.attr('href')
                    if u:
                        eps.append({"name": f"视频{i}", "playId": u})

        if not eps:
            eps.append({"name": "正片", "playId": url})

        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": get_article_img(doc),
                "vod_content": content,
                "vod_year": "", "vod_remarks": "",
                "vod_douban_score": "", "vod_actor": "",
                "vod_director": "", "vod_area": "",
                "vod_play_sources": [{
                    "name": "今日看料",
                    "episodes": eps
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 播放 ======================
async def play(params, context):
    pid = params.get("playId", "")
    if not pid:
        raise ValueError("playId 不能为空")

    p = 1
    u = pid
    if isVideoFormat(u):
        if '.m3u8' in u:
            u = f"/proxy?url={e64(u)}&type=m3u8"
        p = 0

    return {
        "urls": [{"name": "播放", "url": u}],
        "flag": "play",
        "header": headers,
        "parse": p
    }

# ====================== 本地代理 ======================
async def local_proxy(params):
    typ = params.get("type")
    url = d64(params.get("url", ""))
    try:
        if typ == "img":
            r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            return [200, r.headers.get("Content-Type", "image/jpeg"), r.content]
        elif typ == "m3u8":
            r = requests.get(url, headers=headers, proxies=proxies)
            txt = r.text
            lines = txt.split("\n")
            base = url[:url.rfind("/")]
            new = []
            for line in lines:
                if "#EXT" not in line and line.strip():
                    if not line.startswith("http"):
                        line = base + "/" + line
                    line = f"/proxy?url={e64(line)}&type={line.split('.')[-1].split('?')[0]}"
                new.append(line)
            return [200, "application/vnd.apple.mpegurl", "\n".join(new)]
        else:
            r = requests.get(url, headers=headers, proxies=proxies, stream=True)
            return [200, r.headers.get("Content-Type", "video/MP2T"), r.content]
    except:
        return [404, "", ""]

# ====================== 启动 ======================
if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play,
        "local_proxy": local_proxy
    })
