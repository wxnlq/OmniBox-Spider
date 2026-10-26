# -*- coding: utf-8 -*-
# @name 海角社区
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/海角乱伦[瑟瑟].py
# @version 1.0.0
# @dependencies pyquery

import json
import re
from urllib.parse import quote, urlencode, urljoin, urlparse

from pyquery import PyQuery as pq
from spider_runner import OmniBox, run


SITE = "https://hjsqn.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

CLASSES = [
    {"type_id": "/", "type_name": "全部更新"},
    {"type_id": "/sort/hot/", "type_name": "海角热门"},
    {"type_id": "/category/hjyc/", "type_name": "海角原创"},
    {"type_id": "/category/hjll/", "type_name": "海角乱伦"},
    {"type_id": "/category/hjcg/", "type_name": "海角吃瓜"},
    {"type_id": "/category/hjth/", "type_name": "海角探花"},
    {"type_id": "/category/hjwh/", "type_name": "海角网黄"},
]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def absolute_url(value, base=SITE + "/"):
    value = clean(value).replace("\\/", "/")
    if not value:
        return ""
    return urljoin(base, value)


def safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def post_id(value):
    match = re.search(r"/archives/(\d+)", str(value or ""))
    return match.group(1) if match else ""


async def request_text(url, headers=None):
    if not url:
        raise ValueError("请求地址为空")
    response = await OmniBox.request(url, {
        "method": "GET",
        "headers": headers or HEADERS,
    })
    status = response.get("statusCode")
    if status is not None and not 200 <= int(status) < 300:
        raise RuntimeError(
            "HTTP %s: %s" % (status, response.get("body", ""))
        )
    return {
        "body": str(response.get("body") or ""),
        "url": response.get("url") or url,
    }


def parse_cards(page_html, base_url=SITE):
    doc = pq(page_html or "")
    videos = []
    seen = set()

    for row in doc(".xqbj-list-rows").items():
        anchor = row.find(".xqbj-list-rows-image > a[title]").eq(0)
        href = absolute_url(anchor.attr("href"), base_url)
        video_id = post_id(href)
        title = clean(
            anchor.attr("title")
            or anchor.find(".xqbj-list-rows-image-title").text()
        )
        if not href or not video_id or not title or video_id in seen:
            continue
        seen.add(video_id)

        image = row.find("img[z-image-loader-url]").eq(0)
        picture = absolute_url(image.attr("z-image-loader-url"), base_url)
        category = clean(row.find('a[href*="/category/"]').eq(0).text())
        date = clean(
            row.find(".xqbj-icon-time").parent().find(".is-desktop").text()
        )
        count = clean(row.find(".list-text-play").eq(0).text())

        remarks = category
        if count.isdigit():
            remarks = ("%s · " % category if category else "") + count + "项"
        elif date:
            remarks = ("%s · " % category if category else "") + date

        videos.append({
            "vod_id": href,
            "vod_name": title,
            "vod_pic": picture,
            "vod_remarks": remarks,
            "style": {"type": "rect", "ratio": 1.33},
        })
    return videos


def extract_pagecount(page_html, current_page):
    doc = pq(page_html or "")
    pages = [current_page]
    for anchor in doc('a[href*="/page/"]').items():
        match = re.search(r"/page/(\d+)/?", str(anchor.attr("href") or ""))
        if match:
            pages.append(safe_int(match.group(1), current_page))
    return max(pages)


async def log_failure(entry, error):
    await OmniBox.log("error", "[%s] 失败: %s" % (entry, error))


async def home(params, context):
    try:
        await OmniBox.log("info", "[home] 加载首页")
        response = await request_text(SITE + "/")
        return {
            "class": CLASSES,
            "list": parse_cards(response["body"], response["url"]),
        }
    except Exception as error:
        await log_failure("home", error)
        return {"class": CLASSES, "list": []}


async def category(params, context):
    page = max(1, safe_int((params or {}).get("page"), 1))
    category_id = str((params or {}).get("categoryId") or "/")
    try:
        base_url = absolute_url(category_id)
        parsed = urlparse(base_url)
        site = urlparse(SITE)
        if parsed.scheme != site.scheme or parsed.netloc != site.netloc:
            raise ValueError("分类地址无效")
        base_path = parsed.path.rstrip("/") or ""
        path = "%s/page/%s/" % (base_path, page) if page > 1 else (
            base_path or "/"
        )
        url = urljoin(SITE + "/", path.lstrip("/"))
        response = await request_text(url)
        videos = parse_cards(response["body"], response["url"])
        pages = extract_pagecount(response["body"], page)
        limit = len(videos) or 20
        return {
            "page": page,
            "pagecount": pages,
            "total": pages * limit,
            "list": videos,
        }
    except Exception as error:
        await log_failure("category", error)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


def parse_detail(page_html, page_url):
    doc = pq(page_html or "")
    title = clean(doc("h1.novel-title, h1").eq(0).text()) or "海角帖子"
    episodes = []
    used_urls = set()
    players = doc(".dplayer[data-config]")
    player_count = len(players)

    for index, node in enumerate(players.items(), start=1):
        raw_config = node.attr("data-config") or ""
        try:
            config = json.loads(raw_config)
        except (TypeError, ValueError) as error:
            raise ValueError("播放器配置解析失败: %s" % error)
        video = config.get("video") if isinstance(config, dict) else {}
        if not isinstance(video, dict):
            continue

        h264 = absolute_url(video.get("url"), page_url)
        h265 = absolute_url(video.get("h_265") or video.get("h265"), page_url)
        if h264 and h264 not in used_urls:
            used_urls.add(h264)
            name = "视频%d H264" % index if player_count > 1 else "H264原画"
            episodes.append({"name": name, "playId": h264})
        if h265 and h265 not in used_urls:
            used_urls.add(h265)
            name = "视频%d H265" % index if player_count > 1 else "H265原画"
            episodes.append({"name": name, "playId": h265})

    if not episodes:
        return None

    category = clean(
        doc('.detail-info-desc a[href*="/category/"]').eq(0).text()
    )
    author = clean(doc(".novel-info h2").eq(0).text())
    description = clean(doc(".detail-info-desc").text()) or title
    image = doc(".text.text-content img[z-image-loader-url]").eq(0)
    picture = absolute_url(image.attr("z-image-loader-url"), page_url)

    return {
        "vod_id": page_url,
        "vod_name": title,
        "vod_pic": picture,
        "vod_remarks": category or "视频",
        "vod_actor": author,
        "vod_content": description,
        "vod_play_sources": [{
            "name": "海角视频",
            "episodes": episodes,
        }],
    }


async def detail(params, context):
    video_id = str((params or {}).get("videoId") or "").strip()
    if not video_id:
        return {"list": []}
    try:
        url = absolute_url(video_id)
        site = urlparse(SITE)
        parsed = urlparse(url)
        if parsed.scheme != site.scheme or parsed.netloc != site.netloc:
            raise ValueError("视频地址无效")
        response = await request_text(url)
        video = parse_detail(response["body"], response["url"])
        return {"list": [video] if video else []}
    except Exception as error:
        await log_failure("detail", error)
        return {"list": []}


async def search(params, context):
    params = params or {}
    keyword = clean(params.get("keyword") or params.get("wd"))
    page = max(1, safe_int(params.get("page"), 1))
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    query = urlencode({
        "keyword": keyword,
        "type": "posts",
        "page": page,
        "limit": 20,
    })
    referer = "%s/search/%s/" % (SITE, quote(keyword, safe=""))
    headers = dict(HEADERS)
    headers["Referer"] = referer
    url = "%s/Searchs/searchpagination/?%s" % (SITE, query)

    try:
        response = await request_text(url, headers)
        payload = json.loads(response["body"] or "{}")
        items = payload.get("list", []) if isinstance(payload, dict) else []
        if isinstance(items, dict):
            items = items.get("posts") or []
        if not isinstance(items, list):
            items = []

        videos = []
        for item in items:
            if not isinstance(item, dict):
                continue
            video_id = str(item.get("cid") or "").strip()
            title = clean(item.get("title"))
            if not video_id or not title:
                continue
            thumbnails = item.get("thumbnails") or []
            thumbnail = (
                thumbnails[0].get("url")
                if thumbnails and isinstance(thumbnails[0], dict)
                else ""
            )
            category = clean(item.get("category_name"))
            views = safe_int(item.get("view", item.get("viewsNum")), 0)
            remarks = category + ((" · %s浏览" % views) if views else "")
            videos.append({
                "vod_id": "%s/archives/%s/" % (
                    SITE, quote(video_id, safe="")
                ),
                "vod_name": title,
                "vod_pic": absolute_url(thumbnail, response["url"]),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.33},
            })

        total = max(0, safe_int(payload.get("total"), len(videos)))
        pagecount = max(page, (total + 19) // 20) if total else page
        return {
            "list": videos,
            "page": page,
            "pagecount": pagecount,
            "total": total,
        }
    except Exception as error:
        await log_failure("search", error)
        return {"list": [], "page": page, "pagecount": 0, "total": 0}


async def play(params, context):
    play_id = str((params or {}).get("playId") or "").strip()
    if not play_id:
        raise ValueError("playId 不能为空")
    if not play_id.startswith(("http://", "https://")):
        raise ValueError("播放地址无效")

    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": (params or {}).get("flag") or "海角视频",
        "header": {
            "User-Agent": HEADERS["User-Agent"],
            "Accept-Encoding": "identity",
            "Referer": SITE + "/",
            "Origin": SITE,
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
