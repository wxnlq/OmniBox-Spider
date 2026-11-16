# -*- coding: utf-8 -*-
# @name 🌈 51吸瓜
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/91西瓜[瑟瑟].py
# @version 1.0.3
# @dependencies base64,urllib.parse,html

import html
import json
import os
import random
import re
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import quote, urljoin, urlparse

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pyquery import PyQuery as pq

try:
    from spider_runner import OmniBox, run
except ImportError:  # 本地调试用,真正跑在 OmniBox 里时这段不会触发
    OmniBox = None
    run = None

# ====================== 可调配置 ======================

# 图片输出模式:
#   "data"  —— 脚本自己下载 + AES 解密 + base64,直接返回 data:image/...;base64,xxx
#              零部署,客户端只要认 data URI 就能显示(推荐先试这个)
#   "proxy" —— 返回 {IMG_PROXY}?u=<base64url>,由你部署的解密代理出图(图片多时更快更省内存)
#   "raw"   —— 返回原始加密地址(仅用于排查,正常会显示空白)
IMG_MODE = os.environ.get("XGUA_IMG_MODE", "data")
IMG_PROXY = os.environ.get("XGUA_IMG_PROXY", "")   # 例:https://img.example.com/i
IMG_WORKERS = 8
IMG_TIMEOUT = 10

# 【🔧修复】加密参数:与站点前端 image.20261030.min.js 里的一致(原脚本 aesimg() 里也有,但没被调用)
AES_KEY = b'f5d965df75336270'
AES_IV = b'97b60394abc2fbe1'

# 封面地址在页面上的属性,按优先级从新到旧排列
IMG_ATTRS = (
    'x-bg-loader-url',        # 首页卡片(当前线上版本)
    'z-image-loader-url',     # 详情页正文图(当前线上版本)
    'data-xkrkllgl',          # 旧版属性,保留兼容
    'data-src', 'data-original', 'source-url',
)

# ====================== 全局会话 ======================

proxies = {}

_session = requests.Session()
_session.headers.update({
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

_host_cache = {"host": "", "ts": 0}


def _probe_host(url):
    try:
        res = _session.get(url, proxies=proxies, timeout=(6, 12))
        # 【🔧修复】requests 会自动跟随重定向,res.url 才是真正可用的域名
        if res.status_code == 200 and len(pq(res.text)('article')) > 0:
            return res.url.rstrip('/')
    except Exception:
        pass
    return ''


def get_working_host():
    """【🔧修复】原来三个域名串行探测、各 8 秒,站点一慢启动就卡 20 多秒。
    改为并发探测,总耗时最多一个超时。"""
    urls = [
        'https://ago.tksfrive.cc',
        'https://area.tksfrive.cc',
        'https://battery.tksfrive.cc',
    ]
    with ThreadPoolExecutor(max_workers=len(urls)) as ex:
        for h in ex.map(_probe_host, urls):
            if h:
                return h, ''
    return urls[0], ''


host, _first_page = get_working_host()
_session.headers.update({'Origin': host, 'Referer': f"{host}/"})


# ====================== 基础工具 ======================

def getpq(data):
    try:
        return pq(data)
    except Exception:
        return pq(data.encode('utf-8'))


def e64(text):
    try:
        return b64encode(text.encode()).decode()
    except Exception:
        return ""


def d64(encoded):
    """【🔧修复】URL-safe base64 带 - _、缺 = 补位,原版直接 b64decode 会失败。"""
    if not encoded:
        return ""
    try:
        s = encoded.replace('-', '+').replace('_', '/').strip()
        s += '=' * (-len(s) % 4)
        return b64decode(s).decode('utf-8', 'ignore')
    except Exception:
        return ""


def abs_url(url):
    """【🔧修复】把 /xx.jpg、//cdn/xx.jpg 这类相对地址补成完整 https 地址。"""
    if not url:
        return ''
    url = url.strip().replace('\\/', '/')
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return host.rstrip('/') + url
    if url.startswith('http'):
        return url
    return urljoin(host.rstrip('/') + '/', url)


def isVideoFormat(url):
    """【🔧修复】原版用 in 判断,'/stats/' 也会命中 '.ts'。改成看路径结尾。"""
    path = urlparse(url or '').path.lower()
    return any(path.endswith(ext) for ext in ('.m3u8', '.mp4', '.m4v', '.ts'))


# ====================== 图片解密(本次核心) ======================

def _mime_of(raw):
    if not raw:
        return None
    if raw[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if raw[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if raw[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return 'image/webp'
    return None


def decrypt_image(raw):
    """AES-128-CBC + PKCS7 解密;已经是明文图片就原样返回。
    (站点前端是 CryptoJS.AES.decrypt(base64密文, key, {iv, CBC, Pkcs7}),
     等价于对二进制密文做一次 AES-CBC 解密)"""
    if not raw:
        return None
    if _mime_of(raw):
        return raw
    if len(raw) % 16 != 0:          # 不是 16 的倍数,不可能是这种加密格式
        return raw
    try:
        plain = AES.new(AES_KEY, AES.MODE_CBC, AES_IV).decrypt(raw)
        try:
            plain = unpad(plain, AES.block_size)
        except ValueError:
            pass                     # 少数图省了 padding,直接返回
        return plain if _mime_of(plain) else raw
    except Exception:
        return raw


@lru_cache(maxsize=512)
def to_data_uri(url):
    """下载 → 解密 → base64,返回可直接显示的 data URI;失败时返回空串。"""
    if not url:
        return ''
    try:
        res = _session.get(url, proxies=proxies, timeout=IMG_TIMEOUT)
        if res.status_code != 200 or not res.content:
            return ''
        dec = decrypt_image(res.content)
        mime = _mime_of(dec)
        if not mime:
            return ''
        return f"data:{mime};base64," + b64encode(dec).decode()
    except Exception:
        return ''


def img_url(raw):
    """把页面上的图片地址转成客户端能直接显示的地址。"""
    u = abs_url(raw)
    if not u:
        return ''
    if IMG_MODE == 'proxy' and IMG_PROXY:
        # 【🔧修复】原版是 f"{getProxyUrl()}&url=..." —— 代理为空时拼出以 & 开头的非法地址
        return f"{IMG_PROXY}?u={quote(b64encode(u.encode()).decode(), safe='')}"
    if IMG_MODE == 'data':
        return to_data_uri(u) or u
    return u


def build_pics(urls):
    """并发批量处理,避免一页 20 张图串行下载把列表拖到打不开。"""
    if IMG_MODE != 'data' or not urls:
        return [img_url(u) for u in urls]
    with ThreadPoolExecutor(max_workers=IMG_WORKERS) as ex:
        return list(ex.map(img_url, urls))


def image_from_node(node, text=''):
    """【🔧修复】旧的 loadBannerDirect 正则已失效,改成属性优先 + 多层兜底。"""
    # 1) 【🔧修复】站点同一页里混用 x-bg-loader-url / z-bg-loader-url / z-image-loader-url
    #    几种前缀,写死属性名一定会漏大半个列表,这里按后缀通配。
    for el in node.items():
        elem = el[0] if len(el) else None
        attrs = getattr(elem, 'attrib', None) or {}
        for k, v in list(attrs.items()):
            if k.endswith('loader-url') and v and not v.startswith('data:'):
                return v
    # 1.5) 自身 HTML 里再兜一次(有些节点是懒加载,属性在更深层)
    m = re.search(r'[a-z0-9_-]*loader-url="([^"]+)"', node.html() or '')
    if m:
        return m.group(1)
    # 2) 固定属性
    for attr in IMG_ATTRS:
        v = node.attr(attr)
        if v:
            return v
    # 2) 子孙节点的属性
    for attr in IMG_ATTRS:
        v = node(f'[{attr}]').attr(attr)
        if v:
            return v
    # 3) 真实 img 标签
    img = node('img')
    for attr in ('src', 'data-src', 'data-original'):
        v = img.attr(attr)
        if v and not v.startswith('data:'):
            return v
    # 4) 旧版内联脚本写法,留作兼容
    m = re.search(r"loadBannerDirect\('([^']+)'", text or '')
    if m:
        return m.group(1)
    return ''


# ====================== 列表解析 ======================

def getlist(data, tid=''):
    l = '/mrdg' in tid
    items = []
    seen = set()

    # 【🔧修复】原来按 a 标签遍历,改版后一个卡片里有多个 a,容易重复;
    #           改成以 article 为单位,取到卡片链接和标题再取图。
    nodes = data('#index article, #archive article')
    if len(nodes) == 0:
        nodes = data('article')

    for art in nodes.items():
        # 【🔧修复】页面上混着推广位(class 含 ad-item),它们指向外部广告站,必须跳过
        cls = (art.attr('class') or '').lower()
        if 'ad' in cls.split() or 'ad-item' in cls:
            continue
        a = art('a[href]').eq(0)
        href = a.attr('href') or art.attr('data-url') or ''
        if href.startswith('http') and host not in href:   # 站外链接同样跳过
            continue
        name = (art('h2').text() or art('.post-card-title').text() or '').strip()
        if not href or not name:
            continue
        key = href.split('?')[0]
        if key in seen:
            continue
        seen.add(key)

        date = (art('span[itemprop="datePublished"]').text()
                or art('.post-card-meta').text()
                or art('time').text() or '').strip()
        date = re.sub(r'\s+', ' ', date)[:20]

        items.append({
            "vod_id": f"{href}{'@folder' if l else ''}",
            "vod_name": re.sub(r'\s+', ' ', name),
            "vod_pic": image_from_node(art),          # 先存原始地址,下面统一并发处理
            "vod_remarks": date,
            "type_id": "", "type_name": "",
            "vod_year": "", "vod_douban_score": ""
        })

    # 【🔧修复】统一并发解密出图
    pics = build_pics([v['vod_pic'] for v in items])
    for v, p in zip(items, pics):
        v['vod_pic'] = p
    return items


def getfod(id, page_html=None):
    """分类目录式条目(旧的 /mrdg 路径)"""
    url = f"{host}{id}"
    text = page_html or _session.get(url, proxies=proxies, timeout=15).text
    data = getpq(text)
    vdata = data('.post-content[itemprop="articleBody"]')
    for sel in ['.txt-apps', '.line', 'blockquote', '.tags', '.content-tabs']:
        vdata.remove(sel)

    videos = []
    # 【🔧修复】原版用 p.eq(c+1) 硬算索引,页面多一个空 <p> 就整体错位 → 取到 None。
    #           改成「h2 后面的第一个 img / 带图片属性的节点」。
    for x in vdata('h2').items():
        h2 = x
        node = h2.next()
        pic = ''
        for _ in range(4):
            if not node or not node.length:
                break
            pic = image_from_node(node)
            if pic:
                break
            node = node.next()
        title = h2.text().strip()
        href = h2('a').attr('href') or ''
        if not href:
            n2 = h2.next()
            for _ in range(3):
                if not n2 or not n2.length:
                    break
                href = n2('a').attr('href') or ''
                if href:
                    break
                n2 = n2.next()
        if not href or not title:
            continue
        videos.append({
            "vod_id": href,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": "",
            "type_id": "", "type_name": "",
            "vod_year": "", "vod_douban_score": ""
        })
    pics = build_pics([v['vod_pic'] for v in videos])
    for v, p in zip(videos, pics):
        v['vod_pic'] = p
    return videos


# ====================== 首页 ======================

async def home(params, context):
    if OmniBox:
        await OmniBox.log("info", "加载51吸瓜")
    try:
        res = _session.get(host, proxies=proxies, timeout=15)
        data = getpq(res.text)
        classes = []
        seen_tid = set()      # 【🔧修复】同一批链接会在多个选择器里重复命中,去重
        for s in ['.category-list ul li', '.nav-menu li', '.menu li', 'nav ul li']:
            for k in data(s).items():
                link = k('a')
                href = link.attr('href') or ''
                name = link.text().strip() or ''
                if href and href != '#' and name and href not in seen_tid:
                    seen_tid.add(href)
                    classes.append({"type_name": name, "type_id": href})
            if classes:
                break
        if not classes:
            classes = [
                {"type_name": "首页", "type_id": "/"},
                {"type_name": "最新", "type_id": "/latest/"},
                {"type_name": "热门", "type_id": "/hot/"},
            ]
        return {"class": classes, "list": getlist(data)}
    except Exception:
        return {"class": [], "list": []}


# ====================== 分类 ======================

async def category(params, context):
    tid = params.get("categoryId", "/")
    pg = int(params.get("page", 1) or 1)
    try:
        if '@folder' in tid:
            videos = getfod(tid.replace('@folder', ''))
        else:
            # 【🔧修复】原版 tid 不以 / 结尾时会拼成 /mrdgpage/2/ 这种不存在的路径
            if tid.startswith('/'):
                base = tid if tid.endswith('/') else tid + '/'
                url = f"{host}{base}page/{pg}/" if pg != 1 else f"{host}{base}"
            else:
                url = f"{host}/{tid}"
            res = _session.get(url, proxies=proxies, timeout=15)
            videos = getlist(getpq(res.text), tid)
        return {
            "page": pg,
            "pagecount": 1 if '@folder' in tid else 99999,
            "total": 999999,
            "list": videos
        }
    except Exception:
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}


# ====================== 详情 ======================

async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}
    try:
        url = vid if vid.startswith('http') else f"{host}{vid}"
        res = _session.get(url, proxies=proxies, timeout=15)
        data = getpq(res.text)

        clist = []
        for k in data('.tags .keywords a').items():
            t = k.text()
            if t:
                clist.append(t)
        content = ' '.join(clist) or data('.post-title').text() or '51吸瓜视频'

        # 【🔧修复】详情页封面原来恒为 "" → 取正文第一张图并解密
        pic = ''
        body = data('.post-content[itemprop="articleBody"]')
        if not body.length:
            body = data('.post-content')
        pic = image_from_node(body if body.length else data, res.text)
        if pic:
            pic = img_url(pic)

        episodes = []
        used = set()
        for i, k in enumerate(data('.dplayer').items(), 1):
            cfg = k.attr('data-config')
            if not cfg:
                continue
            try:
                # 【🔧修复】data-config 里是 &quot; 实体,不还原 json.loads 必失败 → 每集都被跳过
                cfg = html.unescape(cfg)
                u = json.loads(cfg)['video']['url']
                if not u:
                    continue
                u = abs_url(u) if not u.startswith('http') else u
                n = f"视频{i}"
                while n in used:
                    n = f"视频{i}_{random.randint(10, 99)}"
                used.add(n)
                episodes.append({"name": n, "playId": u})
            except Exception:
                continue
        if not episodes:
            episodes.append({"name": "默认", "playId": url})

        return {
            "list": [{
                "vod_id": vid,
                "vod_name": data('.post-title').text() or "视频",
                "vod_pic": pic,
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
    except Exception:
        return {"list": []}


# ====================== 搜索 ======================

async def search(params, context):
    key = (params.get("keyword") or params.get("wd") or "").strip()
    pg = int(params.get("page", 1) or 1)
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    try:
        # 【🔧修复】中文关键词没做 URL 编码,一搜就 404
        kw = quote(key)
        url = f"{host}/search/{kw}/{pg}/" if pg != 1 else f"{host}/search/{kw}/"
        res = _session.get(url, proxies=proxies, timeout=15)
        videos = getlist(getpq(res.text))
        return {"page": pg, "pagecount": 1, "total": len(videos), "list": videos}
    except Exception:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}


# ====================== 播放 ======================

async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    url = play_id
    # 站点 m3u8 是标准 HLS(hls 里自带 #EXT-X-KEY 的 AES-128 分片加密,播放器自己会处理)
    # 这里只需要保证地址是绝对的,不需要我们再包一层代理。
    url = abs_url(url) if not url.startswith('http') else url
    return {
        "urls": [{"name": "播放", "url": url}],
        "flag": "play",
        # 【🔧修复】原来把整个浏览器请求头(含 Cache-Control、Connection)全塞给播放器,
        #           部分播放器会因此取流失败,这里只给必要的三项。
        "header": {
            "User-Agent": _session.headers.get('User-Agent'),
            "Referer": f"{host}/",
            "Origin": host,
        },
        "parse": 1 if not isVideoFormat(url) else 0
    }


# ====================== 启动 ======================
if __name__ == "__main__" and run:
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
