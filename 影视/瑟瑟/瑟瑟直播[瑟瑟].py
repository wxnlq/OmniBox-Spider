# -*- coding: utf-8 -*-
# @name Leospring直播
# @version 1.0.0

import json
from spider_runner import OmniBox, run

host = "http://api.maiyoux.com:81/mf/"
cateList = {}

# 初始化加载分类
try:
    import requests
    resp = requests.get(host + "json.txt", timeout=10)
    resp.encoding = "utf-8"
    cateList = json.loads(resp.text)
except:
    cateList = {}

async def home(params, context):
    """首页：分类 + 推荐列表"""
    await OmniBox.log("info", "加载直播首页")
    classes = []
    for key in cateList:
        classes.append({
            "type_id": key,
            "type_name": key
        })
    return {
        "class": classes,
        "list": []
    }

async def category(params, context):
    """分类列表"""
    category_id = params.get("categoryId") or ""
    page = params.get("page") or 1

    videos = []
    if category_id in cateList:
        items = cateList[category_id]
        for item in items:
            videos.append({
                "vod_id": item.get("address", ""),
                "vod_name": item.get("title", ""),
                "vod_pic": item.get("xinimg", ""),
                "type_id": category_id,
                "type_name": category_id,
                "vod_remarks": item.get("Number", ""),
                "vod_year": "",
                "vod_douban_score": ""
            })

    return {
        "page": int(page),
        "pagecount": 1,
        "total": len(videos),
        "list": videos
    }

async def detail(params, context):
    """视频详情（直播多线路）"""
    video_id = params.get("videoId")
    if not video_id:
        return {"list": []}

    try:
        resp = requests.get(host + video_id, timeout=10)
        resp.encoding = "utf-8"
        data = json.loads(resp.text)
        zhubo = data.get("zhubo", [])

        episodes = []
        for idx, vod in enumerate(zhubo):
            title = vod.get("title", f"线路{idx+1}")
            address = vod.get("address", "")
            episodes.append({
                "name": title,
                "playId": address
            })

        return {
            "list": [
                {
                    "vod_id": video_id,
                    "vod_name": "直播源",
                    "vod_pic": "",
                    "vod_content": "公众号：蚂蚁科技杂谈",
                    "vod_year": "",
                    "vod_remarks": "",
                    "vod_douban_score": "",
                    "vod_actor": "",
                    "vod_director": "",
                    "vod_area": "",
                    "vod_play_sources": [
                        {
                            "name": "Leospring",
                            "episodes": episodes
                        }
                    ]
                }
            ]
        }
    except Exception as e:
        await OmniBox.log("error", f"详情错误: {e}")
        return {"list": []}

async def search(params, context):
    """搜索（直播源一般不实现）"""
    return {
        "page": 1,
        "pagecount": 0,
        "total": 0,
        "list": []
    }

async def play(params, context):
    """播放地址：直接返回直播链接"""
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": {
            "User-Agent": "Mozilla/5.0",
            "Referer": host
        },
        "parse": 0
    }

if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
