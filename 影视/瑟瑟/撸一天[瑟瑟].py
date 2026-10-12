# -*- coding: utf-8 -*-
# @name 撸一天
# @version 1.0.0

import json
import re
import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin
from spider_runner import OmniBox, run

# 全局配置
host = "https://luyitian.com"
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})

# ====================== 工具函数 ======================
def fetch(url, timeout=10):
    try:
        res = session.get(url, timeout=timeout, allow_redirects=True)
        res.encoding = 'utf-8'
        return res
    except:
        return None

def _js_decode(js_str):
    b64_match = re.search(r'atob\s*\(\s*["\']([^"\']+)["\']\s*\)', js_str)
    if b64_match:
        try:
            return base64.b64decode(b64_match.group(1)).decode('utf-8')
        except:
            pass
    unescape_match = re.search(r'unescape\s*\(\s*["\']([^"\']+)["\']\s*\)', js_str)
    if unescape_match:
        try:
            return unquote(unescape_match.group(1))
        except:
            pass
    url_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', js_str, re.I)
    if url_match:
        return url_match.group(1)
    return None

def _sniff_xhr(html, page_url):
    patterns = [
        r'fetch\s*\(\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        r'url\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        r'src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
    ]
    for pat in patterns:
        match = re.search(pat, html, re.I)
        if match:
            url = match.group(1)
            return url if url.startswith('http') else urljoin(page_url, url)
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script'):
        if script.string:
            found = _js_decode(script.string)
            if found and '.m3u8' in found:
                return found
    return None

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载撸一天")
    classes = [{"type_name": "中文字幕", "type_id": "28"},
            {"type_name": "日本中字", "type_id": "51"},
            {"type_name": "日本无码", "type_id": "22"},
            {"type_name": "日本有码", "type_id": "21"},
            {"type_name": "国产精品", "type_id": "26"},
            {"type_name": "国产剧情", "type_id": "27"},
            {"type_name": "国产自拍", "type_id": "29"},
            {"type_name": "国产主播", "type_id": "35"},
            {"type_name": "欧美精品", "type_id": "104"},
            {"type_name": "动漫精品", "type_id": "103"},
            {"type_name": "韩国主播", "type_id": "37"},
            {"type_name": "Cosplay", "type_id": "106"},
            {"type_name": "人妻", "type_id": "31"},
            {"type_name": "素人", "type_id": "44"}]
    return {"class": classes, "list": []}

# ====================== 分类 ======================
async def category(params, context):
    tid = params.get("categoryId", "28")
    pg = params.get("page", 1)
    url = f"{host}/vodtype/{tid}-{pg}/"
    res = fetch(url)
    if not res:
        return {"page": 1, "pagecount": 999, "total": 0, "list": []}

    soup = BeautifulSoup(res.text, 'html.parser')
    vod_list = []
    items = soup.select('div#mdym > div, .stui-vodlist__item, .myui-vodlist__box, .video-item, .item, .vodlist_item')

    for item in items:
        a = item.select_one('a')
        if not a:
            continue
        href = a.get('href', '')
        vid = re.search(r'/vodplay/(\d+)', href).group(1) if re.search(r'/vodplay/(\d+)', href) else href

        name = ""
        img = item.select_one('img')
        if img:
            name = img.get('alt', '') or a.get('title', '')
        if not name:
            name = (item.select_one('.title, .name, .text') or a).get_text(strip=True) or "未知标题"

        pic = ""
        if img:
            pic = img.get('data-src') or img.get('src', '')
            if pic and not pic.startswith('http'):
                pic = urljoin(host, pic)

        remark = ""
        rem = item.select_one('.remarks, .note, .tag')
        if rem:
            remark = rem.get_text(strip=True)

        vod_list.append({
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "type_id": "", "type_name": "",
            "vod_remarks": remark,
            "vod_year": "", "vod_douban_score": ""
        })

    return {
        "page": int(pg),
        "pagecount": 999,
        "total": 9999,
        "list": vod_list
    }

# ====================== 详情（新版标准格式） ======================
async def detail(params, context):
    vid = params.get("videoId", "")
    if not vid:
        return {"list": []}

    url = f"{host}/vodplay/{vid}-1-1/"
    res = fetch(url)
    if not res:
        return {"list": []}

    soup = BeautifulSoup(res.text, 'html.parser')
    raw_title = soup.title.text.split('|')[0].replace('在线播放在线观看','').replace('《','').replace('》','').strip()

    return {
        "list": [{
            "vod_id": vid,
            "vod_name": raw_title,
            "vod_pic": "",
            "vod_content": "撸一天资源",
            "vod_year": "", "vod_remarks": "",
            "vod_douban_score": "", "vod_actor": "",
            "vod_director": "", "vod_area": "",
            "vod_play_sources": [{
                "name": "Luyitian",
                "episodes": [{"name": "播放", "playId": f"{vid}-1-1"}]
            }]
        }]
    }

# ====================== 搜索 ======================
async def search(params, context):
    key = (params.get("keyword") or params.get("wd") or "").strip()
    pg = params.get("page", 1)
    if not key:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    url = f"{host}/vodsearch/{key}----------{pg}---/"
    res = fetch(url)
    if not res:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    soup = BeautifulSoup(res.text, 'html.parser')
    vod_list = []
    items = soup.select('div#mdym > div, .stui-vodlist__item, .myui-vodlist__box, .video-item')

    for item in items:
        a = item.select_one('a')
        if not a:
            continue
        href = a.get('href', '')
        vid = re.search(r'/vodplay/(\d+)', href).group(1) if re.search(r'/vodplay/(\d+)', href) else href

        name = ""
        img = item.select_one('img')
        if img:
            name = img.get('alt', '') or a.get('title', '')
        if not name:
            name = (item.select_one('.title, .name') or a).get_text(strip=True) or "搜索结果"

        pic = img.get('data-src') or img.get('src', '') if img else ""

        vod_list.append({
            "vod_id": vid,
            "vod_name": name.strip(),
            "vod_pic": pic,
            "type_id": "", "type_name": "",
            "vod_remarks": "",
            "vod_year": "", "vod_douban_score": ""
        })

    return {"page": 1, "pagecount": 1, "total": len(vod_list), "list": vod_list}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    real_id = play_id.split('-')[0] if '-' in play_id else play_id
    play_url = f"{host}/vodplay/{real_id}-1-1/"
    res = fetch(play_url)
    if not res:
        return {"urls": [{"name": "播放", "url": play_url}], "flag": "play", "header": session.headers, "parse": 1}

    html = res.text
    m3u8_url = None

    match = re.search(r'var\s+player_aaaa\s*=\s*(\{.*?\});', html, re.DOTALL)
    if match:
        try:
            config = json.loads(match.group(1).strip().rstrip(','))
            m3u8_url = config.get('url', '')
        except:
            pass

    if not m3u8_url:
        m3u8_url = _js_decode(html)
    if not m3u8_url:
        m3u8_url = _sniff_xhr(html, play_url)

    if m3u8_url:
        m3u8_url = unquote(m3u8_url)
        if m3u8_url.startswith('//'):
            m3u8_url = 'https:' + m3u8_url
        elif not m3u8_url.startswith('http'):
            m3u8_url = urljoin(host, m3u8_url)

        try:
            test = session.get(m3u8_url, headers={'Referer': play_url}, timeout=5)
            if test.status_code == 200 and test.text.startswith('#EXTM3U'):
                return {
                    "urls": [{"name": "播放", "url": m3u8_url}],
                    "flag": "play",
                    "header": {
                        "User-Agent": session.headers['User-Agent'],
                        "Referer": play_url
                    },
                    "parse": 0
                }
        except:
            pass

    return {
        "urls": [{"name": "播放", "url": play_url}],
        "flag": "play",
        "header": session.headers,
        "parse": 1
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
