# -*- coding: utf-8 -*-
# @name 丝袜乐土
# @version 1.0.0
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/丝袜乐土[瑟瑟].py
# 官网: https://d1drd.swwlt78.cfd/

import base64
import html as html_lib
import random
import re
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from Crypto.Cipher import AES

from spider_runner import OmniBox, run

# ====================== 配置 ======================
SITE_HOSTS = [
    "https://d1drd.swwlt78.cfd",
]
# 站点首页会随机生成 5 位子域做备用域名，主域失效时用这个后缀补一个
HOST_SUFFIX = "swwlt78.cfd"

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

CACHE_HOST_KEY = "swlt:host"
COVER_CACHE_KEY = "swlt:cover"
SEARCH_ID_KEY = "swlt:sid"

# 首页取这几个分类拼（分类 id 会变，运行时优先从页面导航里现抓）
HOME_TIDS = ["6097633", "6107633", "6257643"]
HOME_PER_TID = 6

_host_value = ""
_host_lock = threading.Lock()
_cover_cache = {}      # video_id -> cover url（进程内缓存）
_sid_cache = {}        # keyword -> 搜索结果集 id


# ====================== 页面解密 ======================
def _b64(blob):
    """页面里的 base64 可能带 \\/ 转义，补齐 padding 再解码。"""
    blob = blob.replace("\\/", "/").strip()
    blob += "=" * (-len(blob) % 4)
    return base64.b64decode(blob)


def decode_page(text):
    """把站点的 AES-GCM 加密页还原成明文 HTML；本来就是明文则原样返回。"""
    if "document.write" not in text:
        return text

    arrays = {}
    for m in re.finditer(r"([A-Za-z0-9_$]+)\s*=\s*(\[\[.*?\]\])", text, re.S):
        parts = re.findall(r'\[(\d+),\s*"([^"]*)"\]', m.group(2))
        if not parts:
            continue
        parts.sort(key=lambda x: int(x[0]))
        try:
            arrays[m.group(1)] = _b64("".join(p[1] for p in parts))
        except Exception:
            continue
    if not arrays:
        return None

    ordered = sorted(arrays.items(), key=lambda kv: len(kv[1]))
    cipher_text = ordered[-1][1]
    small = ordered[:-1]
    keys = [v for _, v in small if len(v) == 32]

    def js_var(kind):
        # 直接读 JS 里 nonce / additionalData 引用的变量名，不靠长度猜
        m = re.search(kind + r":\s*[A-Za-z0-9_$]+\(\s*[A-Za-z0-9_$]+\(\s*([A-Za-z0-9_$]+)", text)
        return arrays.get(m.group(1)) if m else None

    iv = js_var("nonce")
    aad = js_var("additionalData")
    if iv is None or aad is None or len(keys) != 2:
        rest = [v for _, v in small if len(v) not in (32, 12)]
        iv = iv or next((v for _, v in small if len(v) == 12), None)
        aad = aad or (rest[0] if rest else None)
    if iv is None or aad is None or len(keys) != 2:
        return None

    key = bytes(a ^ b for a, b in zip(keys[0], keys[1]))
    try:
        box = AES.new(key, AES.MODE_GCM, nonce=iv)
        box.update(aad)
        return box.decrypt_and_verify(cipher_text[:-16], cipher_text[-16:]).decode("utf-8", "replace")
    except Exception:
        return None


# ====================== 域名 ======================
def _rand_host():
    return "https://%s.%s" % (
        "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5)),
        HOST_SUFFIX,
    )


def _probe(url):
    try:
        r = requests.get(url + "/", headers=BASE_HEADERS, timeout=8)
        if r.status_code == 200 and ("document.write" in r.text or "vod-card" in r.text):
            return url
    except Exception:
        pass
    return ""


def detect_host():
    for host in SITE_HOSTS:
        got = _probe(host)
        if got:
            return got
    for i in range(3):
        got = _probe(_rand_host())
        if got:
            return got
    return SITE_HOSTS[0]


async def ensure_host():
    global _host_value
    if _host_value:
        return _host_value
    with _host_lock:
        if _host_value:
            return _host_value
        try:
            cached = await OmniBox.getCache(CACHE_HOST_KEY) or ""
        except Exception:
            cached = ""
        _host_value = cached or detect_host()
        try:
            await OmniBox.setCache(CACHE_HOST_KEY, _host_value, 3600)
        except Exception:
            pass
    return _host_value


# ====================== 请求 ======================
def _headers(host):
    d = dict(BASE_HEADERS)
    d["Referer"] = host + "/"
    return d


def get_page(url, host, retry=2):
    last = ""
    for _ in range(retry + 1):
        try:
            r = requests.get(url, headers=_headers(host), timeout=18)
            r.encoding = "utf-8"
            page = decode_page(r.text)
            if page:
                return page
            last = "解密失败(%d)" % r.status_code
        except Exception as exc:
            last = str(exc)
        time.sleep(0.6)
    raise RuntimeError(last or "请求失败")


def abs_url(host, u):
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return host + u
    return u


# ====================== 解析 ======================
CARD_RE = re.compile(r'<li class="vod-card">(.*?)</li>', re.S)
LINK_RE = re.compile(r'href="(/video\.php\?id=(\d+))"')
IMG_RE = re.compile(r'data-original="([^"]+)"')
IMG_SRC_RE = re.compile(r'<img[^>]*?\ssrc="([^"]+)"')
TITLE_RE = re.compile(r'class="card-title"><a[^>]*>(.*?)</a>', re.S)
CAT_RE = re.compile(r'class="card-cat">([^<]*)<')
NAV_RE = re.compile(r'<a href="/list\.php\?id=(\d+)&page=1"[^>]*class="nav-item"[^>]*>([^<]+)</a>')
PAGE_RE = re.compile(r"共\s*(\d+)\s*条.*?第\s*(\d+)\s*/\s*(\d+)\s*页", re.S)
SID_RE = re.compile(r"location\.href='/list\.php\?id=(\d+)&page='")


def parse_cards(page, host):
    """返回 [(vid, title, pic, cat)]，自动剔掉推荐位广告卡。"""
    out, seen = [], set()
    for block in CARD_RE.findall(page):
        link = LINK_RE.search(block)
        if not link:
            continue
        vid = link.group(2)
        if vid in seen:
            continue
        seen.add(vid)
        title_m = TITLE_RE.search(block)
        title = html_lib.unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).strip() if title_m else ""
        img_m = IMG_RE.search(block) or IMG_SRC_RE.search(block)
        pic = abs_url(host, img_m.group(1)) if img_m else ""
        if pic.endswith("loading.svg"):
            pic = ""
        cat_m = CAT_RE.search(block)
        cat = cat_m.group(1).strip() if cat_m else ""
        if not title:
            continue
        out.append((vid, title, pic, cat))
        if pic:
            _cover_cache[vid] = pic
    return out


def parse_classes(page):
    classes, seen = [], set()
    for cid, name in NAV_RE.findall(page):
        if cid in seen:
            continue
        seen.add(cid)
        classes.append({"type_id": cid, "type_name": html_lib.unescape(name).strip()})
    return classes


def parse_pagecount(page):
    m = PAGE_RE.search(page)
    return int(m.group(3)) if m else 1


def parse_total(page):
    m = PAGE_RE.search(page)
    return int(m.group(1)) if m else 0


def parse_player(page, host):
    """从详情页取播放地址（HLS m3u8 明文写在 script 里）。"""
    urls = []
    for pat in (r"hls\.loadSource\(\s*['\"]([^'\"]+)['\"]",
                r"video\.src\s*=\s*['\"]([^'\"]+)['\"]",
                r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"',
                r"<iframe[^>]+src=\"([^\"]+)\""):
        for m in re.finditer(pat, page):
            u = html_lib.unescape(m.group(1))
            if u and u not in urls:
                urls.append(u)
    if not urls:
        m = re.search(r"(https?://[^'\"\s]+\.m3u8[^'\"\s]*)", page)
        if m:
            urls.append(m.group(1))
    return [abs_url(host, u) for u in urls]


def city(txt):
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", txt or ""))).strip()


# ====================== 封面补全（详情页本身不带封面） ======================
def lookup_cover(host, vid, title):
    """详情页没有本片封面：用标题回搜索页按 id 精确捞一张。"""
    if not title:
        return ""
    clean = re.sub(r"[\[\]【】()（）<>《》?？!！,，.。]", " ", title)
    keys = []
    for k in (title[:40], clean[:20], clean[:10]):
        k = k.strip()
        if k and k not in keys:
            keys.append(k)
    for key in keys:
        try:
            page = get_page(host + "/search.php?content=" + quote(key), host)
        except Exception:
            continue
        for block in CARD_RE.findall(page):
            link = LINK_RE.search(block)
            if not link or link.group(2) != vid:
                continue
            img_m = IMG_RE.search(block) or IMG_SRC_RE.search(block)
            if img_m:
                pic = abs_url(host, img_m.group(1))
                if pic and not pic.endswith("loading.svg"):
                    _cover_cache[vid] = pic
                    return pic
    return ""


async def cover_for(host, vid, title):
    if vid in _cover_cache:
        return _cover_cache[vid]
    try:
        cached = await OmniBox.getCache("%s:%s" % (COVER_CACHE_KEY, vid)) or ""
    except Exception:
        cached = ""
    if cached:
        _cover_cache[vid] = cached
        return cached
    pic = lookup_cover(host, vid, title)
    if pic:
        try:
            await OmniBox.setCache("%s:%s" % (COVER_CACHE_KEY, vid), pic, 86400)
        except Exception:
            pass
    return pic


# ====================== 组装列表项 ======================
def build_item(vid, title, pic, cat, tid=""):
    return {
        "vod_id": vid,
        "vod_name": title,
        "vod_pic": pic,
        "type_id": tid or "",
        "type_name": cat or "",
        "vod_remarks": cat or "",
        "vod_year": "",
        "vod_douban_score": "",
    }


# ====================== 五个标准 handler ======================
async def home(params, context):
    host = await ensure_host()
    try:
        first = get_page(host + "/", host)
        classes = parse_classes(first)
    except Exception as exc:
        await OmniBox.log("error", "[home] 首页失败: %s" % exc)
        return {"class": [], "list": []}

    def fetch(tid):
        try:
            page = get_page("%s/list.php?id=%s&page=1" % (host, tid), host)
            return tid, parse_cards(page, host)[:HOME_PER_TID]
        except Exception:
            return tid, []

    items = []
    with ThreadPoolExecutor(max_workers=len(HOME_TIDS)) as pool:
        for tid, cards in pool.map(fetch, HOME_TIDS):
            for vid, title, pic, cat in cards:
                items.append(build_item(vid, title, pic, cat, tid))
    await OmniBox.log("info", "[home] 分类 %d 个 / 影片 %d 条" % (len(classes), len(items)))
    return {"class": classes, "list": items}


async def category(params, context):
    tid = str(params.get("categoryId") or "").strip()
    page_no = int(params.get("page") or 1)
    host = await ensure_host()
    if not tid or tid == "/":
        data = await home(params, context)
        return {"page": 1, "pagecount": 1, "total": len(data.get("list") or []),
                "list": data.get("list") or []}
    try:
        page = get_page("%s/list.php?id=%s&page=%d" % (host, tid, page_no), host)
        cards = parse_cards(page, host)
        items = [build_item(v, t, p, c, tid) for v, t, p, c in cards]
        total_page = parse_pagecount(page)
        await OmniBox.log("info", "[category] %s p%d -> %d 条 / 共 %d 页" % (tid, page_no, len(items), total_page))
        return {"page": page_no, "pagecount": total_page, "total": parse_total(page), "list": items}
    except Exception as exc:
        await OmniBox.log("error", "[category] 失败: %s" % exc)
        return {"page": page_no, "pagecount": 1, "total": 0, "list": []}


async def detail(params, context):
    vid = str(params.get("videoId") or "").strip()
    if not vid:
        return {"list": []}
    host = await ensure_host()
    if "id=" in vid:
        vid = vid.split("id=")[-1].split("&")[0]
    try:
        page = get_page("%s/video.php?id=%s" % (host, vid), host)
        m = re.search(r'<h1 class="video-title">(.*?)</h1>', page, re.S)
        if not m or not city(m.group(1)):
            await OmniBox.log("warn", "[detail] %s 无内容（可能已下架）" % vid)
            return {"list": []}
        title = city(m.group(1))
        pic = await cover_for(host, vid, title)
        notice = re.search(r'class="video-notice">(.*?)</div>', page, re.S)
        content = city(notice.group(1)) if notice else ""
        urls = parse_player(page, host)
        episodes = [{"name": "正片" if len(urls) == 1 else "线路%d" % (i + 1), "playId": u}
                    for i, u in enumerate(urls)]
        if not episodes:
            episodes = [{"name": "正片", "playId": "%s/video.php?id=%s" % (host, vid)}]
        await OmniBox.log("info", "[detail] %s -> %s / 播放 %d 条" % (vid, title[:20], len(episodes)))
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_content": content or title,
                "vod_year": "",
                "vod_remarks": "",
                "vod_douban_score": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_area": "",
                "vod_play_sources": [{"name": "丝袜乐土", "episodes": episodes}],
            }]
        }
    except Exception as exc:
        await OmniBox.log("error", "[detail] 失败: %s" % exc)
        return {"list": []}


async def search(params, context):
    key = (params.get("keyword") or params.get("wd") or "").strip()
    page_no = int(params.get("page") or 1)
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    host = await ensure_host()
    try:
        sid = ""
        if page_no > 1:
            sid = _sid_cache.get(key, "")
            if not sid:
                try:
                    sid = await OmniBox.getCache("%s:%s" % (SEARCH_ID_KEY, key)) or ""
                except Exception:
                    sid = ""
        if sid:
            url = "%s/list.php?id=%s&page=%d" % (host, sid, page_no)
        else:
            url = "%s/search.php?content=%s" % (host, quote(key))
        page = get_page(url, host)

        m = SID_RE.search(page)
        if m:
            sid = m.group(1)
            _sid_cache[key] = sid
            try:
                await OmniBox.setCache("%s:%s" % (SEARCH_ID_KEY, key), sid, 1800)
            except Exception:
                pass

        cards = parse_cards(page, host)
        items = [build_item(v, t, p, c) for v, t, p, c in cards]
        total_page = parse_pagecount(page)
        await OmniBox.log("info", "[search] %s p%d -> %d 条 / 共 %d 页" % (key, page_no, len(items), total_page))
        return {"page": page_no, "pagecount": total_page, "total": parse_total(page), "list": items}
    except Exception as exc:
        await OmniBox.log("error", "[search] 失败: %s" % exc)
        return {"page": page_no, "pagecount": 0, "total": 0, "list": []}


async def play(params, context):
    play_id = (params.get("playId") or "").strip()
    flag = params.get("flag") or "play"
    if not play_id:
        raise ValueError("playId 不能为空")
    host = await ensure_host()
    url = abs_url(host, play_id)
    direct = bool(re.search(r"\.(m3u8|mp4|flv)(\?|$)", url, re.I))
    return {
        "urls": [{"name": "播放", "url": url}],
        "flag": flag,
        "header": {"User-Agent": UA, "Referer": host + "/", "Origin": host},
        "parse": 0 if direct else 1,
    }


if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play,
    })
