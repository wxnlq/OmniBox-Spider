# -*- coding: utf-8 -*-
# @name 权色视频采集器
# @version 1.0.1
# @downloadURL https://raw.githubusercontent.com/wxnlq/-box/refs/heads/main/权色.py
# @indexs 1
# @dependencies beautifulsoup4

import json
import os
import re
import html
import base64
from urllib.parse import quote, unquote, urljoin
from spider_runner import OmniBox, run

# 站点 API / 基础地址（优先读环境变量，兜底默认地址）
SITE_HOST = os.environ.get("SITE_API", "https://www.xiaoqiche.shop").rstrip("/")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": SITE_HOST + "/",
}

# ================= 辅助工具函数 =================

def fix_url(url, host=SITE_HOST):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return urljoin(host, url)
    if url.startswith("http"):
        return url
    return urljoin(host, "/" + url)

def clean_text(text):
    if not text:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", str(text))).strip()

def is_video_format(url):
    return any(ext in url.lower() for ext in [".m3u8", ".mp4", ".flv", ".ts", ".mkv", ".avi", ".wmv", ".mov"])

def extract_id(href):
    m = re.search(r'/id/(\d+)', href)
    return m.group(1) if m else ''

def b64decode_str(s):
    try:
        padding = 4 - len(s) % 4
        if padding != 4:
            s += '=' * padding
        decoded = base64.b64decode(s)
        return decoded.decode('utf-8', errors='strict')
    except Exception:
        return ''

async def fetch_html(url, referer=None):
    """使用 OmniBox 异步 API 请求 HTML 内容"""
    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["Referer"] = referer
    
    try:
        await OmniBox.log("info", f"请求页面: {url}")
        res = await OmniBox.request(url, {
            "method": "GET",
            "headers": headers
        })
        if res.get("statusCode") == 200:
            body = res.get("body", "")
            if "Just a moment" in body or "cf-browser-verification" in body:
                await OmniBox.log("warn", "触发 Cloudflare 验证")
                return ""
            return body
    except Exception as e:
        await OmniBox.log("error", f"Fetch HTML 异常 [{url}]: {e}")
    return ""

def parse_html_list(html_text):
    """解析影片列表卡片"""
    if not html_text:
        return []
    videos = []
    seen = set()
    cards = re.findall(
        r'<li[^>]*class="[^"]*(?:col-md-2|col-sm-3|col-xs-4)[^"]*"[^>]*>(.*?)</li>',
        html_text, re.S | re.I
    )
    for card in cards:
        try:
            href_match = re.search(r'<a[^>]*class="[^"]*video-pic[^"]*"[^>]*href="([^"]*)"', card, re.I)
            if not href_match:
                continue
            href = href_match.group(1)
            vid = extract_id(href)
            if not vid or vid in seen:
                continue
            seen.add(vid)
            
            title = ''
            t_match = re.search(r'<a[^>]*class="[^"]*video-pic[^"]*"[^>]*title="([^"]*)"', card, re.I)
            if t_match:
                title = t_match.group(1)
            if not title:
                t_match = re.search(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*title="([^"]*)"', card, re.S | re.I)
                if t_match:
                    title = t_match.group(1)
            if not title:
                t_match = re.search(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>', card, re.S | re.I)
                if t_match:
                    title = clean_text(t_match.group(1))
                    
            pic = ''
            p_match = re.search(r'background:\s*url\(([^)]+)\)', card, re.I)
            if p_match:
                pic = p_match.group(1).strip().strip('"').strip("'")
                pic = fix_url(pic)
                
            remark = ''
            tds = re.findall(r'<td[^>]*>.*?<div[^>]*align="(?:left|right)"[^>]*>(.*?)</div>.*?</td>', card, re.S | re.I)
            if tds:
                remark = ' '.join(clean_text(t) for t in tds if clean_text(t))

            videos.append({
                'vod_id': str(vid),
                'vod_name': clean_text(title),
                'vod_pic': pic,
                'vod_remarks': remark
            })
        except Exception:
            continue
    return videos

async def extract_video_urls(html_text, page_url):
    """解析页面中嵌有的视频播放地址"""
    play_urls = []
    seen_urls = set()

    def add_url(label, url):
        if not url or url in seen_urls:
            return
        seen_urls.add(url)
        play_urls.append((label, url))

    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html_text, re.S | re.I)
    for script in scripts:
        for var_name in ['player_data', 'player_aaaa', 'playerConfig', 'player', 'videoInfo', 'vodData']:
            pattern = rf'var\s+{re.escape(var_name)}\s*=\s*(\{{.*?\}});'
            m = re.search(pattern, script, re.S)
            if m:
                try:
                    pdata = json.loads(m.group(1))
                    def find_url(obj):
                        if isinstance(obj, str):
                            if obj.startswith('http') and is_video_format(obj):
                                return obj
                            decoded = unquote(obj)
                            if decoded.startswith('http') and is_video_format(decoded):
                                return decoded
                        elif isinstance(obj, dict):
                            for k in ['url', 'src', 'file', 'video', 'm3u8', 'mp4', 'link', 'play_url']:
                                if k in obj:
                                    res = find_url(obj[k])
                                    if res: return res
                            for k in obj:
                                res = find_url(obj[k])
                                if res: return res
                        elif isinstance(obj, list):
                            for item in obj:
                                res = find_url(item)
                                if res: return res
                        return None

                    found = find_url(pdata)
                    if found:
                        add_url('主线路', found)
                except Exception:
                    pass

    # 提取常规 JS 变量
    for var in ['now', 'playurl', 'play_url', 'video_url', 'vod_url', 'url', 'src', 'file']:
        m = re.search(rf'var\s+{re.escape(var)}\s*=\s*["\']([^"\']+)["\']', html_text)
        if m:
            u = m.group(1).strip()
            if u.startswith('http'):
                add_url('直连', unquote(u))

    # 提取页面直链正则
    direct_links = re.findall(r'(https?://[^\s"\'<>]+\.(?:m3u8|mp4|flv|ts|mkv|avi)(?:\?[^\s"\'<>]*)?)', html_text)
    for link in set(direct_links):
        add_url('页面提取', unquote(link))

    # 嵌套 iframe 处理
    if not play_urls:
        iframe_srcs = re.findall(r'<iframe[^>]+(?:src|data-src)=["\']([^"\']+)["\']', html_text, re.I)
        for src in set(iframe_srcs):
            if any(k in src for k in ['play', 'm3u8', 'embed', 'player', 'video', 'vod']):
                full = fix_url(src) if not src.startswith('http') else src
                iframe_html = await fetch_html(full, referer=page_url)
                if iframe_html:
                    inner_urls = await extract_video_urls(iframe_html, full)
                    for label, url in inner_urls:
                        add_url(f'嵌套-{label}', url)
                if not any(u == full for _, u in play_urls):
                    add_url('嵌套页', full)

    # Base64 解码提取
    if not play_urls:
        for b64 in re.findall(r'["\']([A-Za-z0-9+/]{40,}={0,2})["\']', html_text):
            decoded = b64decode_str(b64)
            if decoded.startswith('http') and is_video_format(decoded):
                add_url('Base64', decoded)

    return play_urls

# ================= OmniBox Standard Handlers =================

async def home(params, context):
    """获取分类和首页推荐数据"""
    classes = [
        {'type_name': '国产视频', 'type_id': '1'},
        {'type_name': '中文字幕', 'type_id': '2'},
        {'type_name': '国产传媒', 'type_id': '3'},
        {'type_name': '强奸乱伦', 'type_id': '4'},
        {'type_name': '日本无码', 'type_id': '6'},
        {'type_name': '欧美无码', 'type_id': '7'},
        {'type_name': '制服诱惑', 'type_id': '8'},
        {'type_name': '国产主播', 'type_id': '9'},
        {'type_name': '换脸明星', 'type_id': '10'},
        {'type_name': '女优明星', 'type_id': '11'},
        {'type_name': '抖阴视频', 'type_id': '12'},
        {'type_name': '伦理三级', 'type_id': '13'},
        {'type_name': '黑料流出', 'type_id': '14'},
        {'type_name': '萝莉少女', 'type_id': '15'},
        {'type_name': '韩国主播', 'type_id': '16'},
    ]
    try:
        # 抓取默认分类 1 作为推荐数据
        url = f"{SITE_HOST}/index.php/vod/type/id/1.html"
        html_text = await fetch_html(url)
        vod_list = parse_html_list(html_text)
        return {"class": classes, "list": vod_list}
    except Exception as e:
        await OmniBox.log("error", f"[home] 失败: {e}")
        return {"class": classes, "list": []}

async def category(params, context):
    """获取分类列表分页"""
    try:
        tid = params.get("categoryId") or "1"
        page = int(params.get("page") or 1)
        
        url = f"{SITE_HOST}/index.php/vod/type/id/{tid}/page/{page}.html" if page > 1 else f"{SITE_HOST}/index.php/vod/type/id/{tid}.html"
        html_text = await fetch_html(url)
        
        videos = parse_html_list(html_text)
        total_pages = page + 1
        page_nums = re.findall(r'/page/(\d+)\.html', html_text)
        if page_nums:
            total_pages = max(int(p) for p in page_nums)

        return {
            "page": page,
            "pagecount": total_pages,
            "total": 999999,
            "list": videos
        }
    except Exception as e:
        await OmniBox.log("error", f"[category] 失败: {e}")
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

async def detail(params, context):
    """获取视频详情及剧集/播放源信息"""
    try:
        vid = params.get("videoId")
        if not vid:
            return {"list": []}

        url = f"{SITE_HOST}/index.php/vod/detail/id/{vid}.html"
        html_text = await fetch_html(url)

        if not html_text or 'player' not in html_text.lower():
            play_url = f"{SITE_HOST}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
            html_text = await fetch_html(play_url, referer=url)
            if html_text:
                url = play_url

        if not html_text:
            return {"list": []}

        title = ''
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html_text, re.S | re.I)
        if m:
            title = clean_text(m.group(1))
        if not title:
            m = re.search(r'<title>(.*?)</title>', html_text, re.S | re.I)
            if m:
                title = clean_text(m.group(1)).split('-')[0].split('_')[0]

        cover = ''
        for pat in [
            r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
            r'<img[^>]+data-original="([^"]+)"',
            r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*(?:pic|cover|poster|thumb)[^"]*"',
            r'background:\s*url\(([^)]+)\)',
        ]:
            m = re.search(pat, html_text, re.S | re.I)
            if m:
                cover = fix_url(m.group(1))
                break

        content = ''
        m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html_text, re.S | re.I)
        if m:
            content = m.group(1)

        extracted_urls = await extract_video_urls(html_text, url)
        play_sources = []

        if extracted_urls:
            episodes = []
            for label, purl in extracted_urls:
                episodes.append({
                    "name": label,
                    "playId": purl
                })
            play_sources.append({
                "name": "在线播放",
                "episodes": episodes
            })
        else:
            play_page = f"{SITE_HOST}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
            play_sources.append({
                "name": "默认线路",
                "episodes": [{"name": "正片", "playId": play_page}]
            })

        vod_item = {
            "vod_id": str(vid),
            "vod_name": title or str(vid),
            "vod_pic": cover,
            "vod_content": content,
            "vod_play_sources": play_sources
        }
        return {"list": [vod_item]}
    except Exception as e:
        await OmniBox.log("error", f"[detail] 失败: {e}")
        return {"list": []}

async def search(params, context):
    """搜索视频功能"""
    try:
        keyword = (params.get("keyword") or params.get("wd") or "").strip()
        page = int(params.get("page") or 1)
        if not keyword:
            return {"page": 1, "pagecount": 0, "total": 0, "list": []}

        url = f"{SITE_HOST}/index.php/vod/search/wd/{quote(keyword)}/page/{page}.html"
        html_text = await fetch_html(url)
        if not html_text:
            url = f"{SITE_HOST}/index.php/vod/search.html?wd={quote(keyword)}&page={page}"
            html_text = await fetch_html(url)

        videos = parse_html_list(html_text) if html_text else []
        return {
            "page": page,
            "pagecount": page + 1,
            "total": 999999,
            "list": videos
        }
    except Exception as e:
        await OmniBox.log("error", f"[search] 失败: {e}")
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

async def play(params, context):
    """返回最终播放地址与 Headers 配置"""
    try:
        play_id = params.get("playId", "")
        flag = params.get("flag") or "play"
        
        if not play_id:
            raise ValueError("playId 缺失")

        headers = {
            "Referer": SITE_HOST + "/",
            "User-Agent": DEFAULT_HEADERS["User-Agent"]
        }

        # 如果已经是视频文件格式（m3u8/mp4 等），直接播放
        if is_video_format(play_id):
            return {
                "urls": [{"name": "播放", "url": play_id}],
                "flag": flag,
                "header": headers,
                "parse": 0
            }

        # 如果是个网页 URL，尝试二级提取
        if 'play' in play_id or 'player' in play_id or 'embed' in play_id:
            html_text = await fetch_html(play_id, referer=SITE_HOST + "/")
            if html_text:
                inner = await extract_video_urls(html_text, play_id)
                if inner:
                    for label, url in inner:
                        if is_video_format(url):
                            headers["Referer"] = play_id
                            return {
                                "urls": [{"name": label, "url": url}],
                                "flag": flag,
                                "header": headers,
                                "parse": 0
                            }

        # 兜底降级：交代给 App 客户端自动解析/嗅探
        return {
            "urls": [{"name": "网页解析", "url": play_id}],
            "flag": flag,
            "header": headers,
            "parse": 1
        }
    except Exception as e:
        await OmniBox.log("error", f"[play] 失败: {e}")
        return {"urls": [], "flag": params.get("flag", ""), "header": {}, "parse": 0}

if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
