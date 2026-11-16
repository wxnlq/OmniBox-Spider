# -*- coding: utf-8 -*-
# @name 桃花坞
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/桃花坞[瑟瑟].py
# @version 1.0.0
# @dependencies urllib.request,urllib.parse,json,re
# @description 桃花坞(thw1034.lol) OmniBox 爬虫源：首页 / 分类 / 详情 / 搜索 / 播放。MacCMS 结构，封面明文直连。

import gzip
import json
import re
import ssl
import urllib.parse
import urllib.request

from spider_runner import OmniBox, run

# ====================== 站点配置 ======================
# 主域名 + 备用域名（站点换域名时把新的加进来即可，脚本会自动挑一个能通的）
HOSTS = [
    "https://thw1034.lol",
    "https://www.taohuawu147.lol",
    "https://taohuawu147.lol",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

TIMEOUT = 15

# 分类（站点导航实测 12 个）
CLASSES = [
    {"type_id": "1", "type_name": "国产精品"},
    {"type_id": "2", "type_name": "华语AV"},
    {"type_id": "3", "type_name": "黑料吃瓜"},
    {"type_id": "4", "type_name": "欧美"},
    {"type_id": "5", "type_name": "禁漫"},
    {"type_id": "6", "type_name": "学生"},
    {"type_id": "7", "type_name": "乱伦"},
    {"type_id": "8", "type_name": "探花"},
    {"type_id": "9", "type_name": "日本无码"},
    {"type_id": "10", "type_name": "日本有码"},
    {"type_id": "11", "type_name": "主播网红"},
    {"type_id": "12", "type_name": "日本素人"},
]

_host = None


# ====================== 基础请求 ======================
def _ssl_ctx():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return None


def http_get(url, referer=None):
    """标准库取页面，自动处理 gzip 与编码。"""
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_ctx()) as resp:
        raw = resp.read()
        if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
            try:
                raw = gzip.decompress(raw)
            except Exception:
                pass
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "ignore")


def to_int(v, default=0):
    try:
        return int(str(v).strip())
    except Exception:
        return default


async def ensure_host():
    """挑一个当前能通的域名，整个进程内缓存。"""
    global _host
    if _host:
        return _host
    for h in HOSTS:
        try:
            html = http_get(h + "/")
            if "vod/play/id/" in html or "vod/type/id/" in html:
                _host = h
                await OmniBox.log("info", "站点可用: %s" % h)
                return h
        except Exception as e:
            await OmniBox.log("warn", "站点不可用 %s: %s" % (h, e))
            continue
    _host = HOSTS[0]
    return _host


def abs_url(h, u):
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("http"):
        return u
    if u.startswith("/"):
        return h + u
    return h + "/" + u.lstrip("./")


def unescape(s):
    """站里标题/属性常带 HTML 实体。"""
    if not s:
        return ""
    s = (
        s.replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
    )
    return re.sub(r"\s+", " ", s).strip()


# ====================== 列表解析 ======================
# 卡片：<a href="/index.php/vod/play/id/148083/sid/1/nid/1.html"> <img class="lazyload" src=占位 data-src=真实图 alt=标题>
_CARD_RE = re.compile(
    r'<a[^>]*href="(/index\.php/vod/play/id/(\d+)/sid/(\d+)/nid/(\d+)\.html)"[^>]*>(.*?)</a>',
    re.S,
)


def _attr(tag, name):
    m = re.search(name + r'\s*=\s*"([^"]*)"', tag or "")
    if not m:
        m = re.search(name + r"\s*=\s*'([^']*)'", tag or "")
    return unescape(m.group(1)) if m else ""


def parse_cards(html):
    """列表卡片 → [{vod_id, path, title, pic, remarks}]，按 id 去重。"""
    rows = []
    seen = set()
    for m in _CARD_RE.finditer(html or ""):
        path, vid, sid, nid, inner = m.groups()
        if vid in seen:
            continue
        title, pic = "", ""
        img = re.search(r"<img[^>]*>", inner or "")
        if img:
            tag = img.group(0)
            title = _attr(tag, "alt")
            pic = _attr(tag, "data-src") or _attr(tag, "data-original") or _attr(tag, "src")
            if not pic or "placeholder" in pic or pic.startswith("data:"):
                pic = _attr(tag, "data-src") or _attr(tag, "data-original")
        if not title:
            t = re.search(r"<h\d[^>]*>(.*?)</h\d>", inner or "", re.S)
            if t:
                title = unescape(re.sub(r"<[^>]+>", "", t.group(1)))
        if not title or not pic:
            # 广告位/空卡片/导航位：没有标题或没有图的都不算作品
            if not title:
                continue
        label = re.search(r'<span class="label">([^<]*)</span>', inner or "")
        seen.add(vid)
        rows.append(
            {
                "vod_id": vid,
                "sid": sid,
                "nid": nid,
                "path": path,
                "vod_name": title,
                "vod_pic": abs_url(_host or HOSTS[0], pic),
                "vod_remarks": unescape(label.group(1)) if label else "",
            }
        )
    return rows


def build_item(row, type_id="", type_name=""):
    return {
        "vod_id": row["vod_id"],
        "vod_name": row["vod_name"],
        "vod_pic": row["vod_pic"],
        "type_id": type_id,
        "type_name": type_name,
        "vod_remarks": row.get("vod_remarks") or "HD",
        "vod_year": "",
        "vod_douban_score": "",
    }


def max_page(html):
    """
    分页总数。两种写法都兼容：
      分类 /index.php/vod/type/id/2/page/395.html
      搜索 /index.php/vod/search/page/20/wd/xxx.html
    """
    pages = [to_int(x) for x in re.findall(r"/page/(\d+)(?:/|\.html)", html or "")]
    pages = [p for p in pages if p > 0]
    return max(pages) if pages else 1


# ====================== 首页 ======================
def parse_home(html, h):
    """首页是若干板块（国产传媒/日本无码/…），逐个板块解析后合并去重。"""
    marks = list(re.finditer(r"<h2[^>]*>\s*([^<]{1,30}?)\s*</h2>", html or ""))
    rows = []
    seen = set()
    for i, m in enumerate(marks):
        name = unescape(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(html)
        seg = html[m.end():end]
        for row in parse_cards(seg):
            if row["vod_id"] in seen:
                continue
            seen.add(row["vod_id"])
            row["type_name"] = name
            rows.append(row)
    if not rows:  # 结构变化时兜底：整页抓
        rows = parse_cards(html)
    return rows


async def home(params, context):
    h = await ensure_host()
    try:
        html = http_get(h + "/", h + "/")
        rows = parse_home(html, h)
        items = [build_item(r, "", r.get("type_name", "")) for r in rows]
        await OmniBox.log("info", "[home] %d 条" % len(items))
        return {"class": CLASSES, "list": items}
    except Exception as e:
        await OmniBox.log("error", "[home] 失败: %s" % e)
        return {"class": CLASSES, "list": []}


# ====================== 分类 ======================
def category_url(h, tid, page):
    """
    实测规则：
      /index.php/vod/type/id/2.html           第 1 页
      /index.php/vod/type/id/2/page/2.html    第 N 页
    """
    tid = re.sub(r"[^\d]", "", str(tid or "")) or "1"
    if page <= 1:
        return "%s/index.php/vod/type/id/%s.html" % (h, tid)
    return "%s/index.php/vod/type/id/%s/page/%d.html" % (h, tid, page)


async def category(params, context):
    tid = params.get("categoryId") or params.get("tid") or "1"
    page = to_int(params.get("page"), 1) or 1
    h = await ensure_host()
    tid_digits = re.sub(r"[^\d]", "", str(tid)) or "1"
    type_name = next((c["type_name"] for c in CLASSES if c["type_id"] == tid_digits), "")
    try:
        html = http_get(category_url(h, tid_digits, page), h + "/")
        rows = parse_cards(html)
        items = [build_item(r, tid_digits, type_name) for r in rows]
        pagecount = max(max_page(html), page)
        await OmniBox.log("info", "[category] tid=%s p%s -> %d 条 / 共 %s 页" % (tid_digits, page, len(items), pagecount))
        return {
            "page": page,
            "pagecount": pagecount,
            "total": pagecount * max(len(items), 1),
            "list": items,
        }
    except Exception as e:
        await OmniBox.log("error", "[category] 失败: %s" % e)
        return {"page": page, "pagecount": 1, "total": 0, "list": []}


# ====================== 详情 ======================
def find_pic(html, vid):
    """详情页本身不显示封面，先从页面里的卡片找同 id 的那张。"""
    for row in parse_cards(html):
        if row["vod_id"] == str(vid) and row["vod_pic"]:
            return row["vod_pic"]
    return ""


def search_pic(h, title, vid):
    """再兜底：拿标题搜一次，命中的第一条就是它。"""
    if not title:
        return ""
    try:
        q = urllib.parse.quote(title[:24])
        html = http_get("%s/index.php/vod/search.html?wd=%s" % (h, q), h + "/")
        for row in parse_cards(html):
            if row["vod_id"] == str(vid) and row["vod_pic"]:
                return row["vod_pic"]
    except Exception:
        pass
    return ""


async def detail(params, context):
    raw = str(params.get("videoId") or params.get("vod_id") or "").strip()
    if not raw:
        return {"list": []}
    vid, sid, nid = raw, "1", "1"
    m = re.search(r"/id/(\d+)/sid/(\d+)/nid/(\d+)", raw)
    if m:
        vid, sid, nid = m.group(1), m.group(2), m.group(3)
    elif not raw.isdigit():
        d = re.search(r"(\d+)", raw)
        vid = d.group(1) if d else raw

    h = await ensure_host()
    url = "%s/index.php/vod/play/id/%s/sid/%s/nid/%s.html" % (h, vid, sid, nid)
    try:
        html = http_get(url, h + "/")

        # 标题
        title = ""
        for pat in (
            r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>',
            r"<h1[^>]*>(.*?)</h1>",
        ):
            t = re.search(pat, html, re.S)
            if t:
                title = unescape(re.sub(r"<[^>]+>", "", t.group(1)))
                if title:
                    break
        if not title:
            t = re.search(r"<title>(.*?)</title>", html, re.S)
            title = unescape(re.sub(r"<[^>]+>", "", t.group(1))) if t else ("视频 %s" % vid)
            title = re.sub(r"\s*第\d+集\s*$", "", title).strip()

        # 日期 / 年份
        year = ""
        d = re.search(r"<span[^>]*>\s*(\d{4})-\d{2}-\d{2}\s*</span>", html)
        if d:
            year = d.group(1)

        # 封面
        pic = find_pic(html, vid) or search_pic(h, title, vid)

        # 剧集：同 id 的所有 sid/nid 组合（该站基本单片，多集自动识别）
        combos = []
        for s, n in re.findall(
            r"/index\.php/vod/play/id/%s/sid/(\d+)/nid/(\d+)\.html" % re.escape(str(vid)), html
        ):
            key = (s, n)
            if key not in combos:
                combos.append(key)
        if not combos:
            combos = [(sid, nid)]
        episodes = [
            {"name": "正片" if len(combos) == 1 else "第%d集" % (i + 1), "playId": "%s|%s|%s" % (vid, s, n)}
            for i, (s, n) in enumerate(combos)
        ]

        content = "桃花坞 · %s" % title
        if year:
            content = "桃花坞 · %s · %s" % (year, title)
        if len(episodes) > 1:
            content += " · 共 %d 集" % len(episodes)

        await OmniBox.log("info", "[detail] %s 封面=%s 集数=%d" % (vid, bool(pic), len(episodes)))
        return {
            "list": [
                {
                    "vod_id": str(vid),
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_content": content,
                    "vod_year": year,
                    "vod_remarks": "HD" if len(episodes) == 1 else "全%d集" % len(episodes),
                    "vod_actor": "",
                    "vod_director": "",
                    "vod_area": "",
                    "vod_play_sources": [{"name": "桃花坞", "episodes": episodes}],
                }
            ]
        }
    except Exception as e:
        await OmniBox.log("error", "[detail] %s 失败: %s" % (vid, e))
        return {"list": []}


# ====================== 搜索 ======================
async def search(params, context):
    key = unescape(str(params.get("keyword") or params.get("wd") or "")).strip()
    page = to_int(params.get("page"), 1) or 1
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}
    h = await ensure_host()
    q = urllib.parse.quote(key)
    try:
        # 实测分页规则：/index.php/vod/search/page/1/wd/<关键词>.html
        url = "%s/index.php/vod/search/page/%d/wd/%s.html" % (h, page, q)
        html = http_get(url, h + "/")
        rows = parse_cards(html)
        items = [build_item(r) for r in rows]
        pagecount = max(max_page(html), page)
        await OmniBox.log("info", "[search] %s p%s -> %d 条 / 共 %s 页" % (key, page, len(items), pagecount))
        return {
            "page": page,
            "pagecount": pagecount,
            "total": pagecount * max(len(items), 1),
            "list": items,
        }
    except Exception as e:
        await OmniBox.log("error", "[search] %s 失败: %s" % (key, e))
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


# ====================== 播放 ======================
def parse_player(html):
    """页面里 var player_aaaa={...} 带真实播放地址。"""
    m = re.search(r"player_aaaa\s*=\s*(\{.*?\})\s*</script>", html or "", re.S)
    if not m:
        m = re.search(r"player_aaaa\s*=\s*(\{.*?\});", html or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        try:
            return json.loads(unescape(m.group(1)))
        except Exception:
            return {}


async def play(params, context):
    pid = str(params.get("playId") or params.get("videoId") or "").strip()
    flag = params.get("flag") or "play"
    if not pid:
        raise ValueError("playId 不能为空")

    vid, sid, nid = pid, "1", "1"
    m = re.match(r"^(\d+)\|(\d+)\|(\d+)$", pid)
    if m:
        vid, sid, nid = m.groups()
    else:
        m2 = re.search(r"/id/(\d+)/sid/(\d+)/nid/(\d+)", pid)
        if m2:
            vid, sid, nid = m2.groups()

    h = await ensure_host()
    page_url = "%s/index.php/vod/play/id/%s/sid/%s/nid/%s.html" % (h, vid, sid, nid)
    header = {"User-Agent": UA, "Referer": h + "/", "Origin": h}

    try:
        html = http_get(page_url, h + "/")
        info = parse_player(html)
        url = abs_url(h, str(info.get("url") or ""))
        if url:
            direct = bool(re.search(r"\.(m3u8|mp4|flv)(\?|$)", url, re.I))
            await OmniBox.log("info", "[play] %s -> %s" % (vid, url[:90]))
            return {
                "urls": [{"name": "播放", "url": url}],
                "flag": info.get("flag") or flag,
                "header": header,
                "parse": 0 if direct else 1,
            }
    except Exception as e:
        await OmniBox.log("error", "[play] %s 失败: %s" % (vid, e))

    # 解析不到直链就交回客户端自己嗅探（ok影视 支持 parse=1）
    return {
        "urls": [{"name": "播放", "url": page_url}],
        "flag": flag,
        "header": header,
        "parse": 1,
    }


# ====================== 启动 ======================
if __name__ == "__main__":
    run(
        {
            "home": home,
            "category": category,
            "detail": detail,
            "search": search,
            "play": play,
        }
    )
