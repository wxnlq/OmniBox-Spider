# -*- coding: utf-8 -*-
# @name 桃花坞
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/桃花坞[瑟瑟].py
# @version 1.0.1
# @dependencies urllib.request,urllib.parse,json,re
# @description 桃花坞(thw1034.lol) OmniBox 爬虫源：首页 / 分类 / 详情 / 搜索 / 播放。MacCMS 结构，封面明文直连。

import base64
import html as html_lib
import json
import os
import re
from urllib.parse import quote, unquote, urljoin

try:
    # OmniBox 正式环境：SDK 由 spider_runner 提供
    from spider_runner import OmniBox, run
except ImportError:  # pragma: no cover - 仅供本地调试
    # 本地没有 spider_runner 时的最小 fallback：用 urllib 实现 request/log，
    # run() 从 stdin 读一个 JSON 请求 {"method", "params", "context"} 并分发。
    import asyncio
    import sys
    import urllib.request

    class _LocalOmniBox:
        @staticmethod
        async def request(url, options=None):
            options = options or {}
            req = urllib.request.Request(
                url,
                method=options.get("method") or "GET",
                headers=options.get("headers") or {},
                data=(options.get("body").encode("utf-8")
                      if options.get("body") else None),
            )
            loop = asyncio.get_running_loop()

            def _fetch():
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read()
                    charset = resp.headers.get_content_charset() or "utf-8"
                    return {"statusCode": resp.status,
                            "headers": dict(resp.headers),
                            "body": raw.decode(charset, errors="ignore")}

            return await loop.run_in_executor(None, _fetch)

        @staticmethod
        async def log(level, message):
            print(f"[{level}] {message}", file=sys.stderr)

    OmniBox = _LocalOmniBox()

    def run(handlers):
        payload = json.loads(sys.stdin.read() or "{}")
        handler = handlers.get(payload.get("method") or "")
        if handler is None:
            print(json.dumps({"error": "unknown method"}, ensure_ascii=False))
            return
        result = asyncio.run(
            handler(payload.get("params") or {}, payload.get("context") or {}))
        print(json.dumps(result, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("THW_BASE_URL", "https://thw1034.lol").rstrip("/")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Referer": BASE_URL + "/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 分类 id -> 分类名（以分类页实测 <h1> 为准）
CATEGORIES = [
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
CATEGORY_NAMES = {c["type_id"]: c["type_name"] for c in CATEGORIES}

PAGE_SIZE = 16  # 分类/搜索页实测每页 16 条

# 排序筛选（对应 /vod/show/by/{sort}/id/...，time 为默认排序，走 type 路由即可）
SORT_FILTER = {
    "key": "sort",
    "name": "排序",
    "init": "time",
    "value": [
        {"name": "最近更新", "value": "time"},
        {"name": "最高人气", "value": "hits"},
        {"name": "最多点赞", "value": "up"},
    ],
}


# ---------------------------------------------------------------------------
# 正则
# ---------------------------------------------------------------------------

# 播放链接：/index.php/vod/play/id/149605/sid/1/nid/1.html
PLAY_HREF_RE = re.compile(
    r"/index\.php/vod/play/id/(\d+)/sid/(\d+)/nid/(\d+)\.html")
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.S)
TITLE_TAG_RE = re.compile(r"<title>([^<]+)</title>", re.S)
H6_TITLE_RE = re.compile(r"<h6[^>]*>\s*<a[^>]*>([^<]+)</a>", re.S)
CATEGORY_LINK_RE = re.compile(
    r'<a[^>]+href="[^"]*/index\.php/vod/type/id/(\d+)\.html"[^>]*>([^<]+)</a>',
    re.S)
DATE_RE = re.compile(r"(20\d{2}-\d{1,2}-\d{1,2})")
SHORT_DATE_RE = re.compile(r"\d{1,2}-\d{1,2}")
TAG_LINK_RE = re.compile(r"/index\.php/vod/search/wd/([^\"'<>]+)\.html")
PLAYER_AAAA_RE = re.compile(
    r"player_aaaa\s*=\s*(\{.*\})\s*(?:;|</script>)", re.S)
# 实测（2026-11-17，id 149605）：页面写的是 player_aaaa={...}</script>，
# 无 var、无分号，且 url 为 https:\/\/thm3u8.co\/...\/index.m3u8（encrypt=0）。
# 上面的惰性正则会停在 vod_data 子对象的第一个 } 处导致 JSON 解析失败，
# 因此 _player_aaaa_urls() 改用花括号配对扫描，不再依赖该正则的分组。
IFRAME_SRC_RE = re.compile(
    r'<iframe\b[^>]+src=["\']([^"\']+)["\']', re.S | re.I)
M3U8_RE = re.compile(
    r"https?://[^\"'\s<>\\]+\.m3u8(?:\?[^\"'\s<>\\]*)?", re.I)
MP4_RE = re.compile(
    r"https?://[^\"'\s<>\\]+\.mp4(?:\?[^\"'\s<>\\]*)?", re.I)
OG_IMAGE_RE = re.compile(
    r'<meta\b[^>]+property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.S | re.I)
OG_IMAGE_RE2 = re.compile(
    r'<meta\b[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.S | re.I)


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def _clean(text):
    """去 HTML 标签/实体/多余空白。"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _abs_url(url):
    if not url:
        return ""
    url = html_lib.unescape(url.strip()).replace("\\/", "/")
    if url.startswith("data:") or url.startswith("javascript:"):
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urljoin(BASE_URL + "/", url)


def _is_placeholder_pic(url):
    """过滤懒加载占位图/透明 gif。"""
    if not url or url.startswith("data:"):
        return True
    low = url.lower()
    return ("placeholder" in low or "loading" in low
            or low.endswith(".gif") and "blank" in low)


def _img_pic(img_tag):
    """按懒加载属性优先级取图片地址：data-original > data-src > src。"""
    for attr in ("data-original", "data-src", "data-lazy-src",
                 "data-url", "src"):
        m = re.search(r'%s=["\']([^"\']+)["\']' % attr, img_tag)
        if m:
            url = _abs_url(m.group(1))
            if url and not _is_placeholder_pic(url):
                return url
    return ""


def _img_alt(img_tag):
    m = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
    return _clean(m.group(1)) if m else ""


async def _fetch(url):
    """GET 取页面 HTML，失败返回空串并记日志。"""
    try:
        resp = await OmniBox.request(url, {"method": "GET", "headers": HEADERS})
        if (resp or {}).get("statusCode") != 200:
            await OmniBox.log(
                "warn", "请求失败 %s status=%s"
                % (url, (resp or {}).get("statusCode")))
            return ""
        return (resp or {}).get("body") or ""
    except Exception as exc:  # noqa: BLE001 - 爬虫要容错，记日志后返回空
        await OmniBox.log("warn", "请求异常 %s: %s" % (url, exc))
        return ""


def _last_page(html_text, pattern):
    """从分页栏的“最后 »”链接取总页数；找不到返回 None。"""
    pages = [int(n) for n in re.findall(pattern, html_text or "")]
    return max(pages) if pages else None


# ---------------------------------------------------------------------------
# 列表解析（首页 / 分类 / 搜索共用同一卡片结构）
# ---------------------------------------------------------------------------

def parse_vod_list(html_text, default_type_id="", default_type_name=""):
    """解析视频卡片列表。

    卡片结构（实测）：外层 <a href="播放页"> 内含 <img src 封面 alt 标题>、
    日期（MM-DD）和 HD 徽标；其后 <h6><a>标题</a></h6>。
    """
    items = []
    seen = set()
    text = html_text or ""
    matches = list(PLAY_HREF_RE.finditer(text))
    for idx, m in enumerate(matches):
        vod_id, sid, nid = m.group(1), m.group(2), m.group(3)
        if vod_id in seen:
            continue
        seen.add(vod_id)
        # 卡片内容在 href 之后、下个卡片之前，窗口截到下个播放链接处
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        window = text[m.start():min(end, m.start() + 3000)]

        title = ""
        pic = ""
        img_m = IMG_TAG_RE.search(window)
        if img_m:
            pic = _img_pic(img_m.group(0))
            title = _img_alt(img_m.group(0))
        if not title:
            h6_m = H6_TITLE_RE.search(window)
            if h6_m:
                title = _clean(h6_m.group(1))
        # 标题里可能带日期后缀（如 "xxx 11-17"），去掉
        title = re.sub(r"\s*\d{1,2}-\d{1,2}\s*$", "", title).strip()
        if not title:
            continue

        remarks = "HD" if "HD" in window else ""
        item = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remarks,
        }
        if default_type_id:
            item["type_id"] = default_type_id
        if default_type_name:
            item["type_name"] = default_type_name
        # 日期只作副标题展示（MM-DD，无年份）
        date_m = SHORT_DATE_RE.search(window)
        if date_m:
            item["vod_subtitle"] = date_m.group(0)
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# 播放地址解析
# ---------------------------------------------------------------------------

def _decode_player_url(url, encrypt):
    """解码 player_aaaa.url：encrypt 0=明文，1=escape 编码，2=base64。"""
    if not url:
        return ""
    url = url.strip()
    try:
        if encrypt in (1, "1"):
            return unquote(url)
        if encrypt in (2, "2"):
            padded = url + "=" * (-len(url) % 4)
            return base64.b64decode(padded).decode("utf-8", errors="ignore")
    except Exception:  # noqa: BLE001 - 解码失败则回落明文
        pass
    return url


def _extract_stream_urls(html_text):
    """从 HTML 里直搜流媒体地址，返回去重后的 [(name, url)]。"""
    found = []
    seen = set()
    # 先把 JSON 里常见的 \/ 转义还原，否则 https:\/\/... 匹配不到
    text = (html_text or "").replace("\\/", "/")
    for pattern in (M3U8_RE, MP4_RE):
        for raw in pattern.findall(text):
            url = _abs_url(raw)
            if url and url not in seen:
                seen.add(url)
                found.append(url)
    return found


def _player_aaaa_json(html_text):
    """按花括号配对取 player_aaaa = {...} 的完整 JSON 文本。

    兼容 var player_aaaa = {...}; 与 player_aaaa={...}</script> 两种写法；
    扫描时跳过字符串内的花括号/转义字符，避免停在 vod_data 子对象处。
    """
    text = html_text or ""
    m = re.search(r"player_aaaa\s*=\s*\{", text)
    if not m:
        return ""
    start = m.end() - 1
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return ""


def _player_aaaa_urls(html_text):
    """解析 MacCMS 标准变量 var player_aaaa = {...}，返回 (直链, iframe链接)。"""
    direct = []
    iframe_links = []
    raw_json = _player_aaaa_json(html_text)
    if not raw_json:
        return direct, iframe_links
    try:
        data = json.loads(raw_json)
    except ValueError:
        return direct, iframe_links
    encrypt = data.get("encrypt", 0)
    for key in ("url", "url_next"):
        url = _decode_player_url(str(data.get(key) or ""), encrypt)
        if url:
            url = _abs_url(url)
            # url 字段偶尔是多地址以 $$$ 或 # 分隔，逐个拆开
            for part in re.split(r"[\$#]+", url):
                part = part.strip()
                if part.startswith("http") and part not in direct:
                    direct.append(part)
    for key in ("link", "link_next"):
        link = str(data.get(key) or "").strip()
        if link and link.startswith("http"):
            iframe_links.append(_abs_url(link))
    return direct, iframe_links


async def _resolve_play_urls(play_page_html):
    """分层提取播放地址，返回 [(name, url)]（可能为空）。"""
    urls = []

    # 1) player_aaaa 直链
    direct, iframe_links = _player_aaaa_urls(play_page_html)
    urls.extend(direct)

    # 2) 页面内直搜 m3u8 / mp4
    for url in _extract_stream_urls(play_page_html):
        if url not in urls:
            urls.append(url)
    if urls:
        return [("播放", u) for u in urls]

    # 3) 跟进 iframe（播放器内页），最多跟 2 个
    iframe_srcs = []
    for src in IFRAME_SRC_RE.findall(play_page_html or ""):
        abs_src = _abs_url(src)
        if abs_src and abs_src not in iframe_srcs:
            iframe_srcs.append(abs_src)
    for link in iframe_links:
        if link not in iframe_srcs:
            iframe_srcs.append(link)
    for src in iframe_srcs[:2]:
        inner = await _fetch(src)
        if not inner:
            continue
        direct2, _ = _player_aaaa_urls(inner)
        urls.extend(u for u in direct2 if u not in urls)
        for url in _extract_stream_urls(inner):
            if url not in urls:
                urls.append(url)
        if urls:
            break

    return [("播放", u) for u in urls]


# ---------------------------------------------------------------------------
# OmniBox handlers
# ---------------------------------------------------------------------------

async def home(params, context):
    """首页：分类 + 推荐列表（首页 5 个栏目、各 8 条，共约 40 条）。"""
    await OmniBox.log("info", "桃花坞 home：获取首页数据")
    html_text = await _fetch(BASE_URL + "/")
    items = parse_vod_list(html_text)
    result = {
        "class": CATEGORIES,
        "list": items,
        "filters": {c["type_id"]: [SORT_FILTER] for c in CATEGORIES},
    }
    if items:
        result["banner"] = [
            {
                "title": it.get("vod_name", ""),
                "subtitle": it.get("vod_remarks", ""),
                "backgroundImage": it.get("vod_pic", ""),
                "genre": it.get("type_name", ""),
                "actors": "",
                "description": "",
            }
            for it in items[:5]
        ]
    return result


async def category(params, context):
    """分类列表。params: categoryId, page, filters{sort}。"""
    category_id = str(params.get("categoryId") or "1")
    page = int(params.get("page") or 1)
    filters = params.get("filters") or {}
    sort = (filters.get("sort") or "time").strip()
    type_name = CATEGORY_NAMES.get(category_id, "")

    if sort in ("hits", "up"):
        # 排序页：/index.php/vod/show/by/{sort}/id/{id}.html
        base = "%s/index.php/vod/show/by/%s/id/%s" % (BASE_URL, sort, category_id)
        page_pattern = (r"/vod/show/by/%s/id/%s/page/(\d+)\.html"
                        % (re.escape(sort), re.escape(category_id)))
    else:
        base = "%s/index.php/vod/type/id/%s" % (BASE_URL, category_id)
        page_pattern = (r"/vod/type/id/%s/page/(\d+)\.html"
                        % re.escape(category_id))
    url = base + (".html" if page <= 1 else "/page/%d.html" % page)

    await OmniBox.log("info", "桃花坞 category：%s page=%d" % (url, page))
    html_text = await _fetch(url)
    items = parse_vod_list(html_text, category_id, type_name)
    pagecount = _last_page(html_text, page_pattern) or page
    return {
        "page": page,
        "pagecount": pagecount,
        # 站内无总条数字段，用“总页数 x 每页16条”估算（末页可能不足 16 条）
        "total": pagecount * PAGE_SIZE,
        "list": items,
    }


async def detail(params, context):
    """视频详情。

    详情页全站空白，改为抓播放页取标题/分类/日期/标签。
    videoId 为数字 id（如 149605），也兼容 "id|sid|nid" 与完整播放链接。
    """
    raw_id = str(params.get("videoId") or "").strip()
    m = re.search(r"(\d+)", raw_id)
    if not m:
        return {"list": []}
    video_id = m.group(1)
    sid_m = re.search(r"\|(\d+)\|(\d+)", raw_id)
    sid = sid_m.group(1) if sid_m else "1"
    nid = sid_m.group(2) if sid_m else "1"

    play_url = ("%s/index.php/vod/play/id/%s/sid/%s/nid/%s.html"
                % (BASE_URL, video_id, sid, nid))
    await OmniBox.log("info", "桃花坞 detail：%s" % play_url)
    html_text = await _fetch(play_url)
    if not html_text:
        return {"list": []}

    name = ""
    title_m = TITLE_TAG_RE.search(html_text)
    if title_m:
        name = _clean(title_m.group(1))
        name = re.sub(r"\s*-\s*Niceav\s*$", "", name)
        name = re.sub(r"\s*第\d+集\s*$", "", name).strip()

    type_id, type_name = "", ""
    cat_m = CATEGORY_LINK_RE.search(html_text)
    if cat_m:
        type_id, type_name = cat_m.group(1), _clean(cat_m.group(2))

    pic = ""
    og_m = OG_IMAGE_RE.search(html_text) or OG_IMAGE_RE2.search(html_text)
    if og_m:
        pic = _abs_url(og_m.group(1))
    if not pic:
        img_m = IMG_TAG_RE.search(html_text)
        if img_m:
            pic = _img_pic(img_m.group(0))

    date_m = DATE_RE.search(html_text)
    tags = []
    for raw_tag in TAG_LINK_RE.findall(html_text):
        tag = _clean(unquote(raw_tag))
        if tag and tag not in tags:
            tags.append(tag)
    content_parts = []
    if date_m:
        content_parts.append("发布日期：%s" % date_m.group(1))
    if tags:
        content_parts.append("标签：%s" % "、".join(tags[:12]))

    # 播放源：站内为单线路单集；若播放页含同 id 的其他 sid/nid 链接则一并收录
    sources = {}
    for pm in PLAY_HREF_RE.finditer(html_text):
        if pm.group(1) != video_id:
            continue
        s, n = pm.group(2), pm.group(3)
        sources.setdefault(s, set()).add(n)
    if not sources:
        sources = {sid: {nid}}
    play_sources = []
    for s in sorted(sources, key=lambda x: int(x)):
        episodes = [
            {"name": "第%s集" % n,
             "playId": "%s|%s|%s" % (video_id, s, n)}
            for n in sorted(sources[s], key=lambda x: int(x))
        ]
        play_sources.append({"name": "线路%s" % s, "episodes": episodes})

    item = {
        "vod_id": video_id,
        "vod_name": name or raw_id,
        "vod_pic": pic,
        "vod_content": "\n".join(content_parts),
        "vod_remarks": "HD",
        "type_id": type_id,
        "type_name": type_name or CATEGORY_NAMES.get(type_id, ""),
        "vod_play_sources": play_sources,
    }
    if date_m:
        item["vod_year"] = date_m.group(1)[:4]
    return {"list": [item]}


async def search(params, context):
    """搜索。params: keyword, page。"""
    keyword = (params.get("keyword") or params.get("wd") or "").strip()
    page = int(params.get("page") or 1)
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    encoded = quote(keyword)
    if page <= 1:
        url = "%s/index.php/vod/search/wd/%s.html" % (BASE_URL, encoded)
    else:
        url = ("%s/index.php/vod/search/page/%d/wd/%s.html"
               % (BASE_URL, page, encoded))

    await OmniBox.log("info", "桃花坞 search：%s" % url)
    html_text = await _fetch(url)
    items = parse_vod_list(html_text)
    pagecount = _last_page(html_text, r"/vod/search/page/(\d+)/wd/") or page
    return {
        "page": page,
        "pagecount": pagecount,
        "total": pagecount * PAGE_SIZE,
        "list": items,
    }


async def play(params, context):
    """获取播放地址。

    playId 格式："{vod_id}|{sid}|{nid}"，也兼容纯数字 id 与完整播放链接。
    """
    raw_id = str(params.get("playId") or "").strip()
    flag = params.get("flag") or "play"
    if not raw_id:
        raise ValueError("playId 不能为空")

    m = re.search(r"(\d+)", raw_id)
    if not m:
        raise ValueError("playId 无法解析：%s" % raw_id)
    video_id = m.group(1)
    sid_m = re.search(r"\|(\d+)\|(\d+)", raw_id)
    sid = sid_m.group(1) if sid_m else "1"
    nid = sid_m.group(2) if sid_m else "1"
    play_url = ("%s/index.php/vod/play/id/%s/sid/%s/nid/%s.html"
                % (BASE_URL, video_id, sid, nid))

    await OmniBox.log("info", "桃花坞 play：%s" % play_url)
    html_text = await _fetch(play_url)
    header = dict(HEADERS)
    if html_text:
        resolved = await _resolve_play_urls(html_text)
        if resolved:
            return {
                "urls": [{"name": name, "url": url} for name, url in resolved],
                "flag": flag,
                "header": header,
                "parse": 0,  # 直链不需解析
            }

    # 兜底：未提取到直链时返回播放页，交由客户端嗅探（仅 ok影视 app 有效）
    await OmniBox.log("warn", "桃花坞 play：未提取到直链，回落嗅探 %s" % play_url)
    return {
        "urls": [{"name": "播放", "url": play_url}],
        "flag": flag,
        "header": header,
        "parse": 1,
    }


if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play,
    })
