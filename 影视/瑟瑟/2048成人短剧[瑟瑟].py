# -*- coding: utf-8 -*-
# @name 🦋 2048成人短剧
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/2048成人短剧[瑟瑟].py
# @version 1.0.0

import json
from urllib.parse import (
    parse_qsl,
    quote,
    unquote,
    urlencode,
    urljoin,
    urlsplit,
    urlunsplit,
)

from spider_runner import OmniBox, run


SITE_URL = "https://mdcmai4.xyz"
API_CATEGORIES = "/api/v1/categories?type=video"
API_VIDEOS = "/api/v1/videos"
API_SHORT_DRAMAS = "/api/v1/short-dramas"
API_SHORT_DRAMA_DETAIL = "/api/v1/short-dramas/"
API_SEARCH = "/api/v1/videos/search"
API_M3U8_PROXY = "/api/v1/m3u8/proxy?path="
API_IMAGE_PROXY = "/api/v1/image/proxy?path="
SHORT_DRAMA_TID = "short_drama_ai"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": f"{SITE_URL}/",
    "Origin": SITE_URL,
    "Accept": "application/json, text/plain, */*",
}


def build_url(path, params=None):
    url = urljoin(SITE_URL, path)
    if not params:
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        (key, str(value))
        for key, value in params.items()
        if value is not None and value != ""
    )
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


async def request_json(path, params=None):
    url = build_url(path, params)
    await OmniBox.log("info", f"[2048成人短剧][request] {url}")
    response = await OmniBox.request(
        url,
        {
            "method": "GET",
            "headers": HEADERS,
        },
    )
    status_code = response.get("statusCode")
    if status_code != 200:
        body = response.get("body", "")
        raise RuntimeError(f"HTTP {status_code}: {body}")

    body = response.get("body", "")
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body)


def response_data(response, action):
    if response.get("code") != 200:
        raise RuntimeError(
            f"{action}失败: {response.get('message') or 'code=' + str(response.get('code'))}"
        )
    return response.get("data")


def format_cover(path):
    if not path:
        return ""
    path = str(path)
    if path.startswith(("http://", "https://")):
        return path
    if path.startswith(("/uploads/", "/api/")):
        return urljoin(SITE_URL, path)
    return f"{SITE_URL}{API_IMAGE_PROXY}{quote(path, safe='')}"


def format_play_url(path):
    if not path:
        return ""
    path = str(path)
    if path.startswith(("http://", "https://")):
        return path
    if path.startswith("/api/v1/m3u8/proxy"):
        return urljoin(SITE_URL, path)
    return f"{SITE_URL}{API_M3U8_PROXY}{quote(path, safe='')}"


def format_duration(seconds):
    try:
        total_seconds = int(seconds or 0)
    except (TypeError, ValueError):
        return ""
    if total_seconds <= 0:
        return ""

    total_minutes, remainder = divmod(total_seconds, 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remainder:02d}"
    return f"{total_minutes:02d}:{remainder:02d}"


def make_video_id(kind, item):
    if kind == "drama":
        title = quote(str(item.get("title") or ""), safe="")
        cover = quote(str(item.get("coverUrl") or ""), safe="")
        return f"drama@@{item.get('id')}@@{title}@@{cover}"

    video_url = quote(str(item.get("videoUrl") or ""), safe="")
    title = quote(str(item.get("title") or ""), safe="")
    cover = quote(str(item.get("coverUrl") or ""), safe="")
    return f"video@@{item.get('id')}@@{video_url}@@{title}@@{cover}"


def format_video(item, kind):
    title = str(item.get("title") or "")
    category_name = str(item.get("categoryName") or "")
    if kind == "drama":
        remarks = (
            f"评分:{item.get('rating', 0)} | "
            f"共{item.get('episodeCount', 1)}集"
        )
    else:
        remarks = format_duration(item.get("durationSec")) or category_name

    return {
        "vod_id": make_video_id(kind, item),
        "vod_name": title,
        "vod_pic": format_cover(item.get("coverUrl")),
        "type_name": category_name,
        "vod_remarks": remarks,
    }


def parse_video_id(video_id):
    parts = str(video_id).split("@@")
    try:
        if parts[0] == "drama" and len(parts) == 4:
            return {
                "kind": "drama",
                "id": parts[1],
                "title": unquote(parts[2]),
                "cover": unquote(parts[3]),
            }
        if parts[0] == "video" and len(parts) == 5:
            return {
                "kind": "video",
                "id": parts[1],
                "video_url": unquote(parts[2]),
                "title": unquote(parts[3]),
                "cover": unquote(parts[4]),
            }
    except (IndexError, ValueError):
        return None
    return None


def positive_page(value):
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


async def home(params, context):
    await OmniBox.log("info", "获取首页分类")
    response = await request_json(API_CATEGORIES)
    categories = response_data(response, "获取分类")
    classes = [{"type_id": SHORT_DRAMA_TID, "type_name": "🔥 AI短剧"}]

    if isinstance(categories, list):
        for category in categories:
            if category.get("enabled", True):
                classes.append(
                    {
                        "type_id": str(category.get("id")),
                        "type_name": str(category.get("name") or "未知分类"),
                    }
                )
    return {"class": classes}


async def category(params, context):
    category_id = str(params.get("categoryId") or "")
    if not category_id:
        raise ValueError("分类ID不能为空")
    page = positive_page(params.get("page"))
    is_drama = category_id == SHORT_DRAMA_TID

    if is_drama:
        path = API_SHORT_DRAMAS
        query = {"productId": 1, "sortBy": "heat", "page": page, "size": 12}
    else:
        path = API_VIDEOS
        query = {"page": page, "size": 24, "categoryId": category_id}

    response = await request_json(path, query)
    data = response_data(response, "获取分类列表")
    if not isinstance(data, dict):
        raise RuntimeError("分类列表响应格式无效")

    items = data.get("items") or []
    return {
        "page": page,
        "pagecount": int(data.get("totalPages") or page),
        "total": int(data.get("total") or 0),
        "list": [
            format_video(item, "drama" if is_drama else "video")
            for item in items
        ],
    }


async def detail(params, context):
    video_id = str(params.get("videoId") or "")
    if not video_id:
        raise ValueError("videoId 不能为空")

    video = parse_video_id(video_id)
    if not video:
        raise ValueError(f"无法识别的视频ID: {video_id}")

    title = video.get("title") or "视频详情"
    cover = video.get("cover") or ""
    source_name = "专线播放"
    episodes = []

    if video["kind"] == "drama":
        path = f"{API_SHORT_DRAMA_DETAIL}{quote(video['id'], safe='')}"
        response = await request_json(path, {"productId": 1})
        drama = response_data(response, "获取短剧详情")
        if not isinstance(drama, dict):
            raise RuntimeError("短剧详情响应格式无效")

        title = str(drama.get("title") or title)
        cover = str(drama.get("coverUrl") or cover)
        source_name = "AI短剧专线"
        for episode in drama.get("episodes") or []:
            video_url = episode.get("videoUrl")
            if video_url:
                episodes.append(
                    {
                        "name": f"第{episode.get('episodeNo') or 1}集",
                        "playId": format_play_url(video_url),
                    }
                )
    else:
        play_url = format_play_url(video.get("video_url"))
        if play_url:
            episodes.append({"name": "正片", "playId": play_url})

    return {
        "list": [
            {
                "vod_id": video_id,
                "vod_name": title,
                "vod_pic": format_cover(cover),
                "vod_play_sources": [
                    {"name": source_name, "episodes": episodes}
                ],
            }
        ]
    }


async def search(params, context):
    keyword = str(params.get("keyword") or params.get("wd") or "").strip()
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    page = positive_page(params.get("page"))
    response = await request_json(
        API_SEARCH,
        {"page": page, "size": 24, "q": keyword},
    )
    data = response_data(response, "搜索视频")
    if not isinstance(data, dict):
        raise RuntimeError("搜索响应格式无效")

    items = data.get("items") or []
    return {
        "page": page,
        "pagecount": int(data.get("totalPages") or page),
        "total": int(data.get("total") or 0),
        "list": [format_video(item, "video") for item in items],
    }


async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")
    return {
        "urls": [{"name": "播放", "url": str(play_id)}],
        "flag": params.get("flag") or "play",
        "header": HEADERS,
        "parse": 0,
    }


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
