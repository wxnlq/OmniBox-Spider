# -*- coding: utf-8 -*-
# @name UAA[听]
# @version 1.0.0

import json
import urllib.parse
import re
from spider_runner import OmniBox, run

# ====================== 全局配置 ======================
base_url = "https://www.uaa001.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": base_url
}

# ====================== 工具函数 ======================
def fetch(url):
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = "utf-8"
        return r
    except:
        return None

def format_count(count):
    try:
        count = int(count)
        if count >= 10000:
            return f"{count/10000:.1f}万"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        else:
            return str(count)
    except:
        return str(count)

def getChapterUrl(cid):
    try:
        u = f"{base_url}/api/audio/app/audio/chapter?id={cid}"
        r = fetch(u)
        d = json.loads(r.text)
        return d.get("model", {}).get("chapterUrl", "")
    except:
        return ""

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载 UAA[听]")
    classes = [
        {"type_name": "有声小说", "type_id": "有声小说"},
        {"type_name": "淫词艳曲", "type_id": "淫词艳曲"},
        {"type_name": "激情骚麦", "type_id": "激情骚麦"},
        {"type_name": "寸止训练", "type_id": "寸止训练"},        
        {"type_name": "ASMR", "type_id": "ASMR"}
    ]
    return {"class": classes, "list": []}

# ====================== 分类 ======================
async def category(params, context):
    tid = params.get("categoryId", "")
    pg = params.get("page", 1)
    videos = []
    try:
        url = f"{base_url}/api/audio/app/audio/search?category={tid}&orderType=1&page={pg}&searchType=1&size=42"
        rsp = fetch(url)
        data = json.loads(rsp.text)
        for item in data["model"]["data"]:
            videos.append({
                "vod_id": item["id"],
                "vod_name": item["title"],
                "vod_pic": item["coverUrl"],
                "vod_remarks": item["categories"],
                "type_id": "", "type_name": "",
                "vod_year": "", "vod_douban_score": ""
            })
    except:
        pass

    return {
        "page": int(pg),
        "pagecount": 9999,
        "total": 999999,
        "list": videos
    }

# ====================== 搜索 ======================
async def search(params, context):
    key = (params.get("keyword") or "").strip()
    videos = []
    if not key:
        return {"list": []}
    try:
        url = f"{base_url}/api/audio/app/audio/search?category=&keyword={urllib.parse.quote(key)}&orderType=1&page=1&searchType=1&size=32"
        rsp = fetch(url)
        data = json.loads(rsp.text)
        for item in data["model"]["data"]:
            videos.append({
                "vod_id": item["id"],
                "vod_name": item["title"],
                "vod_pic": item["coverUrl"],
                "vod_remarks": item["categories"],
                "type_id": "", "type_name": "",
                "vod_year": "", "vod_douban_score": ""
            })
    except:
        pass
    return {"list": videos}

# ====================== 详情（新版标准格式） ======================
async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}

    try:
        url = f"{base_url}/api/audio/app/audio/intro?id={vid}"
        rsp = fetch(url)
        data = json.loads(rsp.text)
        m = data["model"]

        # 章节列表
        episodes = []
        if "chapters" in m and m["chapters"]:
            for c in m["chapters"]:
                cid = c.get("id", "")
                title = c.get("title", f"第{c.get('order',1)}集")
                play_url = getChapterUrl(cid)
                if play_url:
                    episodes.append({"name": title, "playId": play_url})

        # 兜底
        if not episodes and "latestReadChapterUrl" in m:
            episodes.append({"name": "第1集", "playId": m["latestReadChapterUrl"]})

        # 备注
        rem = []
        if "playCount" in m:
            rem.append(f"收听:{format_count(m['playCount'])}")
        if "collectCount" in m:
            rem.append(f"收藏:{format_count(m['collectCount'])}")
        remark = " | ".join(rem) if rem else m.get("updateState", "")

        return {
            "list": [{
                "vod_id": vid,
                "vod_name": m["title"],
                "vod_pic": m["coverUrl"],
                "vod_content": m.get("intro", ""),
                "vod_actor": m.get("author", "未知"),
                "vod_area": m.get("categories", ""),
                "vod_remarks": remark,
                "vod_year": "", "vod_douban_score": "",
                "vod_director": "",
                "vod_play_sources": [{
                    "name": "UAA",
                    "episodes": episodes
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

    return {
        "urls": [{"name": "播放", "url": pid}],
        "flag": "play",
        "header": headers,
        "parse": 0
    }

# ====================== 启动 ======================
if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
