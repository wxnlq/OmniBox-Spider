# -*- coding: utf-8 -*-
# @name 日日撸
# @version 1.0.1
# @downloadURL https://gh-proxy.org/https://github.com/wxnlq/-box/raw/refs/heads/main/影视/瑟瑟/日日撸.py
# @indexs 1
# @dependencies requests,beautifulsoup4

import json
import os
import re
from urllib.parse import quote, urlencode, urljoin
from bs4 import BeautifulSoup
from spider_runner import OmniBox, run

# 站点默认地址
DEFAULT_SITE_URL = "https://ririlu.cc"
SITE_API = os.environ.get("SITE_API", DEFAULT_SITE_URL).rstrip("/")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    )
}


async def request_html(url):
    """发送网页 GET 请求并返回 BeautifulSoup 对象"""
    await OmniBox.log("info", f"请求页面: {url}")
    res = await OmniBox.request(url, {"method": "GET", "headers": HEADERS})
    if res.get("statusCode") != 200:
        raise RuntimeError(f"HTTP {res.get('statusCode')}: {url}")
    return BeautifulSoup(res.get("body", ""), "html.parser")


def to_int(v):
    """安全转换为整型"""
    try:
        return int(float(v)) if isinstance(v, str) else int(v)
    except (ValueError, TypeError):
        return 0


def map_vod_item(href, title, pic, remark):
    """构造标准 VodItem 对象"""
    return {
        "vod_id": urljoin(SITE_API, href) if href else "",
        "vod_name": str(title or "").strip(),
        "vod_pic": urljoin(SITE_API, pic) if pic else "",
        "vod_remarks": str(remark or "").strip(),
    }


async def home(params, context):
    """首页分类与推荐视频"""
    try:
        classes = [
            {"type_id": "/vodshow/28", "type_name": "中文字幕"},
            {"type_id": "/vodshow/20", "type_name": "国产"},
            {"type_id": "/vodshow/21", "type_name": "日本有码"},
            {"type_id": "/vodshow/22", "type_name": "日本无码"},
            {"type_id": "/vodshow/23", "type_name": "欧美"},
            {"type_id": "/vodshow/24", "type_name": "动漫"},
            {"type_id": "/vodshow/25", "type_name": "伦理"},
            {"type_id": "/vodshow/36", "type_name": "韩国"},
            {"type_id": "/vodshow/41", "type_name": "另类"},
        ]

        # 抓取排行榜作为首页推荐数据
        rank_url = f"{SITE_API}/label/rank/"
        soup = await request_html(rank_url)
        vod_list = []

        for item in soup.select(".list-content a"):
            href = item.get("href", "")
            if not href:
                continue
            title_el = item.select_one(".desc")
            img_el = item.select_one("img")
            read_el = item.select_one(".read")

            title = title_el.get_text(strip=True) if title_el else ""
            pic = (img_el.get("data-src") or img_el.get("src")) if img_el else ""
            remark = f"▶️{read_el.get_text(strip=True)}" if read_el else ""

            vod_list.append(map_vod_item(href, title, pic, remark))

        return {"class": classes, "list": vod_list}
    except Exception as e:
        await OmniBox.log("error", f"[home] 异常: {e}")
        return {"class": [], "list": []}


async def category(params, context):
    """分类分页列表处理"""
    try:
        category_id = params.get("categoryId") or params.get("tid") or "/vodshow/28"
        page = params.get("page") or 1
        filters = params.get("filters") or {}

        cate_id = filters.get("cateId", category_id)
        by_sort = filters.get("by", "time")

        url = f"{SITE_API}{cate_id}--{by_sort}------{page}---/"
        soup = await request_html(url)
        vod_list = []

        for item in soup.select(".list-content a"):
            href = item.get("href", "")
            if not href:
                continue
            title_el = item.select_one(".desc")
            img_el = item.select_one("img")
            read_el = item.select_one(".read")

            title = title_el.get_text(strip=True) if title_el else ""
            pic = (img_el.get("data-src") or img_el.get("src")) if img_el else ""
            remark = f"▶️{read_el.get_text(strip=True)}" if read_el else ""

            vod_list.append(map_vod_item(href, title, pic, remark))

        return {
            "page": to_int(page),
            "pagecount": 999,
            "total": 9999,
            "list": vod_list,
        }
    except Exception as e:
        await OmniBox.log("error", f"[category] 异常: {e}")
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}


async def detail(params, context):
    """解析视频详情与多线路播放列表"""
    try:
        video_id = params.get("videoId") or params.get("id")
        if not video_id:
            return {"list": []}

        url = video_id if video_id.startswith("http") else urljoin(SITE_API, video_id)
        soup = await request_html(url)

        title_el = soup.select_one("h1") or soup.select_one("title")
        title = title_el.get_text(strip=True) if title_el else "视频详情"

        img_el = soup.select_one('meta[property="og:image"]') or soup.select_one("img")
        pic = ""
        if img_el:
            pic = img_el.get("content") or img_el.get("src") or ""

        play_sources = []
        line_els = soup.select(".play-btn-group .line")

        if line_els:
            for idx, line in enumerate(line_els):
                line_title_el = line.select_one("a")
                line_name = (
                    f"📽️{line_title_el.get_text(strip=True)}📺"
                    if line_title_el
                    else f"📽️线路{idx + 1}📺"
                )

                episodes = []
                for link in line.select("a"):
                    p_name = link.get_text(strip=True)
                    p_href = link.get("href", "")
                    if p_href:
                        episodes.append({
                            "name": p_name,
                            "playId": urljoin(SITE_API, p_href)
                        })

                if episodes:
                    play_sources.append({"name": line_name, "episodes": episodes})

        # 回退默认线路
        if not play_sources:
            play_sources.append({
                "name": "默认线路",
                "episodes": [{"name": "正片", "playId": url}]
            })

        vod_item = map_vod_item(url, title, pic, "")
        vod_item["vod_play_sources"] = play_sources

        return {"list": [vod_item]}
    except Exception as e:
        await OmniBox.log("error", f"[detail] 异常: {e}")
        return {"list": []}


async def search(params, context):
    """AJAX 接口搜索视频"""
    try:
        keyword = (params.get("keyword") or params.get("wd") or "").strip()
        page = params.get("page") or 1

        if not keyword:
            return {"page": 1, "pagecount": 0, "total": 0, "list": []}

        search_url = f"{SITE_API}/index.php/ajax/suggest?mid=1&wd={quote(keyword)}"
        res = await OmniBox.request(search_url, {"method": "GET", "headers": HEADERS})

        if res.get("statusCode") != 200:
            return {"page": 1, "pagecount": 0, "total": 0, "list": []}

        data = json.loads(res.get("body", "{}"))
        vod_list = []

        for item in data.get("list") or []:
            v_id = item.get("id", "")
            v_name = item.get("name", "")
            v_pic = item.get("pic", "")

            play_href = f"{SITE_API}/vodplay/{v_id}-1-1/"
            vod_list.append(map_vod_item(play_href, v_name, v_pic, ""))

        return {
            "page": to_int(page),
            "pagecount": 1,
            "total": len(vod_list),
            "list": vod_list,
        }
    except Exception as e:
        await OmniBox.log("error", f"[search] 异常: {e}")
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}


async def play(params, context):
    """解析真实播放链接 (包含正则提取 m3u8/mp4 逻辑)"""
    try:
        play_id = params.get("playId")
        flag = params.get("flag") or "play"

        if not play_id:
            raise ValueError("playId 不能为空")

        headers = {"User-Agent": HEADERS["User-Agent"], "Referer": play_id}

        # 若已经是媒体直链，直接返回
        if play_id.endswith((".m3u8", ".mp4")):
            return {
                "urls": [{"name": "播放", "url": play_id}],
                "flag": flag,
                "header": headers,
                "parse": 0,
            }

        # 抓取播放页源码解析直链
        res = await OmniBox.request(play_id, {"method": "GET", "headers": HEADERS})
        html_text = res.get("body", "")

        m3u8_matches = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html_text)
        mp4_matches = re.findall(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', html_text)

        filtered_m3u8 = [u for u in m3u8_matches if "baidu.com" not in u]
        filtered_mp4 = [u for u in mp4_matches if "baidu.com" not in u]

        video_url = None
        if filtered_m3u8:
            video_url = filtered_m3u8[0]
        elif filtered_mp4:
            video_url = filtered_mp4[0]

        if video_url:
            return {
                "urls": [{"name": "直链播放", "url": video_url}],
                "flag": flag,
                "header": headers,
                "parse": 0,
            }

        # 无法解析出直链时回退交由客户端解析
        return {
            "urls": [{"name": "解析播放", "url": play_id}],
            "flag": flag,
            "header": headers,
            "parse": 1,
        }
    except Exception as e:
        await OmniBox.log("error", f"[play] 异常: {e}")
        return {
            "urls": [],
            "flag": params.get("flag", ""),
            "header": {},
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
