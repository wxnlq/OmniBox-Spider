# -*- coding: utf-8 -*-
# @name 极品少女
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/极品少女[瑟瑟].py
# @version 0.0.1
# @dependencies: pycryptodome

import base64
import html
import json
import re
from urllib.parse import urlencode, urljoin

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from spider_runner import OmniBox, run


SITE = "https://xn--0809-kb2g560h.jpsn47.top/jpsn"
KEY = b"1234567898882222"
IV = b"8NONwyJtHesysWpM"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": SITE + "/",
}

CLASSES = [
    {"type_id": "174", "type_name": "视频一区"},
    {"type_id": "175", "type_name": "视频二区"},
    {"type_id": "176", "type_name": "视频三区"},
    {"type_id": "195", "type_name": "视频四区"},
    {"type_id": "204", "type_name": "视频五区"},
    {"type_id": "181", "type_name": "国产专区"},
    {"type_id": "191", "type_name": "精品推荐"},
    {"type_id": "192", "type_name": "国产精品"},
    {"type_id": "193", "type_name": "主播秀色"},
    {"type_id": "194", "type_name": "日本有码"},
    {"type_id": "138", "type_name": "亚洲有码"},
    {"type_id": "156", "type_name": "3P合辑"},
    {"type_id": "167", "type_name": "VR视角"},
    {"type_id": "140", "type_name": "中文字幕"},
    {"type_id": "143", "type_name": "人妻熟女"},
    {"type_id": "145", "type_name": "三级伦理"},
    {"type_id": "146", "type_name": "自拍偷拍"},
    {"type_id": "155", "type_name": "AV明星"},
    {"type_id": "157", "type_name": "巨乳系列"},
    {"type_id": "163", "type_name": "大秀视频"},
    {"type_id": "168", "type_name": "素人搭讪"},
    {"type_id": "139", "type_name": "欧美情色"},
    {"type_id": "141", "type_name": "动漫卡通"},
    {"type_id": "144", "type_name": "强奸乱伦"},
    {"type_id": "154", "type_name": "制服诱惑"},
    {"type_id": "158", "type_name": "颜射系列"},
    {"type_id": "161", "type_name": "SM重味"},
    {"type_id": "162", "type_name": "教师学生"},
    {"type_id": "164", "type_name": "日韩精品"},
    {"type_id": "196", "type_name": "日本无码"},
    {"type_id": "197", "type_name": "童颜巨乳"},
    {"type_id": "198", "type_name": "性感人妻"},
    {"type_id": "199", "type_name": "卡通动漫"},
    {"type_id": "200", "type_name": "丝袜OL"},
    {"type_id": "201", "type_name": "日本片商"},
    {"type_id": "202", "type_name": "剧情介绍"},
    {"type_id": "203", "type_name": "网曝系列"},
    {"type_id": "205", "type_name": "麻豆传媒"},
    {"type_id": "206", "type_name": "明星换脸"},
    {"type_id": "207", "type_name": "国产乱伦"},
    {"type_id": "208", "type_name": "国产丝袜"},
    {"type_id": "209", "type_name": "国产SM"},
    {"type_id": "210", "type_name": "国产人妻"},
    {"type_id": "211", "type_name": "探花嫖娼"},
    {"type_id": "212", "type_name": "同性恋"},
]

def clean(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def absolute_url(value, base=SITE + "/"):
    value = html.unescape(str(value or "")).strip()
    if not value:
        return ""
    return urljoin(base, value)


def page_id(value):
    value = str(value or "").strip()
    match = re.search(r"/vod/detail/id/(\d+)\.html", value)
    if match:
        return match.group(1)
    match = re.fullmatch(r"\d+", value)
    return match.group(0) if match else ""


async def request_text(url, method="GET", body=None, headers=None):
    response = await OmniBox.request(url, {
        "method": method,
        "headers": headers or HEADERS,
        **({"body": body} if body is not None else {}),
    })
    status = response.get("statusCode")
    if status is not None and not 200 <= int(status) < 300:
        raise RuntimeError("HTTP %s: %s" % (status, response.get("body", "")))
    return str(response.get("body") or "")


def decrypt_page(page_html):
    if not page_html:
        return ""

    match = re.search(
        r'<div[^>]*id=["\']app["\'][^>]*>\s*([A-Za-z0-9+/=\r\n]+?)\s*</div>',
        page_html,
        re.S,
    )
    if not match:
        if "stui-vodlist__box" in page_html or "stui-content__playlist" in page_html:
            return page_html
        return ""

    encoded = re.sub(r"\s+", "", match.group(1))
    ciphertext = base64.b64decode(encoded, validate=True)
    decrypted = AES.new(KEY, AES.MODE_CBC, IV).decrypt(ciphertext)
    try:
        decrypted = unpad(decrypted, AES.block_size)
    except ValueError:
        raise ValueError("页面 AES 解密后填充无效")
    return decrypted.decode("utf-8", errors="ignore")


def parse_cards(page_html):
    videos = []
    seen = set()
    pattern = re.compile(
        r'<a\b[^>]*class=["\'][^"\']*stui-vodlist__thumb[^"\']*["\'][^>]*>'
        r'[\s\S]*?</a>',
        re.I,
    )
    for match in pattern.finditer(page_html or ""):
        card = match.group(0)
        href_match = re.search(
            r"""href=["']([^"']*detail/id/(\d+)\.html)["']""", card, re.I
        )
        if not href_match:
            continue
        href, video_id = href_match.groups()

        title_match = re.search(r"""title=["']([^"']*)["']""", card, re.I)
        title = clean(title_match.group(1)) if title_match else ""
        if not title:
            alt_match = re.search(r"""alt=["']([^"']*)["']""", card, re.I)
            title = clean(alt_match.group(1)) if alt_match else ""

        image_match = re.search(
            r"""(?:data-original|data-src|src)=["']([^"']+)["']""", card, re.I
        )
        picture = absolute_url(image_match.group(1)) if image_match else ""

        remark_match = re.search(
            r'<span[^>]*class=["\'][^"\']*pic-text[^"\']*["\'][^>]*>'
            r'\s*<b>([^<]*)</b>',
            card,
            re.I,
        )
        remark = clean(remark_match.group(1)) if remark_match else ""

        key = (video_id, title)
        if key in seen:
            continue
        seen.add(key)
        videos.append({
            "vod_id": video_id,
            "vod_name": title or "未命名",
            "vod_pic": picture,
            "vod_remarks": remark,
        })
    return videos


def extract_pagecount(page_html):
    match = re.search(
        r'class=["\']active num["\'][^>]*>\s*<a[^>]*>\s*\d+\s*/\s*(\d+)',
        page_html or "",
    )
    if match:
        return int(match.group(1))
    last_page = re.findall(r'/page/(\d+)\.html[^>]*>\s*尾页', page_html or "")
    if last_page:
        return max(map(int, last_page))
    pages = re.findall(r"/page/(\d+)\.html", page_html or "")
    return max(map(int, pages)) if pages else 1


def parse_detail(page_html, video_id):
    title_match = re.search(
        r'<h1[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>([\s\S]*?)</h1>',
        page_html,
        re.I,
    )
    title = clean(title_match.group(1)) if title_match else "未命名"

    picture_match = re.search(
        r"""(?:data-original|data-src|poster|src)=["']([^"']+\.(?:jpg|jpeg|png|webp)(?:\?[^"']*)?)["']""",
        page_html,
        re.I,
    )
    picture = absolute_url(picture_match.group(1)) if picture_match else ""

    content_match = re.search(
        r'<span[^>]*class=["\'][^"\']*detail-content[^"\']*["\'][^>]*>'
        r'([\s\S]*?)</span>',
        page_html,
        re.I,
    )
    description = clean(content_match.group(1)) if content_match else ""

    episode_pattern = re.compile(
        r"""<a\b[^>]*href=["']([^"']*/vod/play/id/%s/sid/(\d+)/nid/(\d+)\.html)["'][^>]*>([^<]*)</a>"""
        % re.escape(str(video_id)),
        re.I,
    )
    grouped = {}
    seen = set()
    for match in episode_pattern.finditer(page_html or ""):
        href, sid, nid, label = match.groups()
        if href in seen:
            continue
        seen.add(href)
        label = clean(label)
        if label in ("", "立即播放", "立即观看"):
            label = "第%s集" % nid
        grouped.setdefault(sid, []).append({
            "name": label,
            "playId": absolute_url(href),
            "_nid": int(nid),
        })

    source_match = re.search(
        r'<h3[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>'
        r'\s*(?:<i[^>]*></i>)?\s*([^<]+)',
        page_html or "",
        re.I,
    )
    source_name = clean(source_match.group(1)) if source_match else "dadim3u8"
    sources = []
    for sid, episodes in grouped.items():
        episodes.sort(key=lambda episode: episode["_nid"])
        for episode in episodes:
            episode.pop("_nid", None)
        sources.append({
            "name": source_name if len(grouped) == 1 else "%s-%s" % (source_name, sid),
            "episodes": episodes,
        })

    return {
        "vod_id": str(video_id),
        "vod_name": title,
        "vod_pic": picture,
        "vod_content": description,
        "vod_play_sources": sources,
    }


async def home(params, context):
    try:
        await OmniBox.log("info", "获取首页数据")
        encrypted = await request_text(SITE + "/")
        return {
            "class": CLASSES,
            "list": parse_cards(decrypt_page(encrypted)),
        }
    except Exception as error:
        await OmniBox.log("error", "首页加载失败: %s" % error)
        return {"class": CLASSES, "list": []}


async def category(params, context):
    category_id = str(params.get("categoryId") or "174")
    try:
        page = max(1, int(params.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    if not re.fullmatch(r"\d+", category_id):
        await OmniBox.log("error", "分类 ID 无效: %s" % category_id)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}

    url = "%s/index.php/vod/type/id/%s/page/%s.html" % (
        SITE, category_id, page
    )
    try:
        page_html = decrypt_page(await request_text(url))
        return {
            "page": page,
            "pagecount": extract_pagecount(page_html),
            "total": 0,
            "list": parse_cards(page_html),
        }
    except Exception as error:
        await OmniBox.log("error", "分类加载失败: %s" % error)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


async def detail(params, context):
    video_id = page_id(params.get("videoId"))
    if not video_id:
        return {"list": []}

    try:
        url = "%s/index.php/vod/detail/id/%s.html" % (SITE, video_id)
        page_html = decrypt_page(await request_text(url))
        video = parse_detail(page_html, video_id)
        video["type_id"] = ""
        video["type_name"] = ""
        return {"list": [video]}
    except Exception as error:
        await OmniBox.log("error", "详情加载失败: %s" % error)
        return {"list": []}


async def search(params, context):
    keyword = str(params.get("keyword") or params.get("wd") or "").strip()
    try:
        page = max(1, int(params.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    url = SITE + "/index.php/vod/search.html"
    headers = dict(HEADERS)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Referer"] = SITE + "/"
    body = urlencode({"wd": keyword})
    try:
        page_html = decrypt_page(await request_text(url, "POST", body, headers))
        return {
            "page": page,
            "pagecount": 1,
            "total": 0,
            "list": parse_cards(page_html),
        }
    except Exception as error:
        await OmniBox.log("error", "搜索失败: %s" % error)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


async def play(params, context):
    play_id = str(params.get("playId") or "").strip()
    if not play_id:
        raise ValueError("playId 不能为空")

    url = absolute_url(play_id)
    if not url.startswith(SITE + "/"):
        raise ValueError("播放页地址无效")
    page_html = decrypt_page(await request_text(url))
    match = re.search(
        r"var\s+player_aaaa\s*=\s*(\{.*?\})\s*</script>",
        page_html,
        re.S | re.I,
    )
    if not match:
        match = re.search(r"var\s+player_aaaa\s*=\s*(\{.*?\})", page_html, re.S | re.I)

    play_url = ""
    if match:
        config = json.loads(match.group(1))
        if int(config.get("encrypt") or 0) != 0:
            raise ValueError("播放地址使用了暂不支持的加密方式")
        play_url = str(config.get("url") or "").strip()

    if not play_url:
        fallback = re.search(
            r"""(https?://[^"'\s<>]+\.(?:m3u8|mp4|flv|mpd)(?:\?[^"'\s<>]*)?)""",
            page_html,
            re.I,
        )
        if fallback:
            play_url = fallback.group(1)
    if not play_url.startswith(("http://", "https://")):
        raise ValueError("播放页未找到有效直链")

    return {
        "urls": [{"name": "播放", "url": play_url}],
        "flag": params.get("flag") or "dadim3u8",
        "header": {
            "User-Agent": USER_AGENT,
            "Referer": SITE + "/",
        },
        "parse": 0,
    }


if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play,
    })
