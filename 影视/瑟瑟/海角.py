# -*- coding: utf-8 -*-
# @name bulunhufait 影视采集器
# @version 1.0.0
# @indexs 1
# @dependencies beautifulsoup4, lxml

import json
import os
import re
import html as htmlmod
import base64
from urllib.parse import quote, unquote, urljoin
from spider_runner import OmniBox, run

try:
    from lxml import etree
except ImportError:
    etree = None

# 站点 API / 基础地址（优先读环境变量，兜底默认地址）
SITE_HOST = os.environ.get("SITE_API", "https://4tw3gy653a.bulunhufait.buzz").rstrip("/")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", str(text))).strip()

def is_video_format(url):
    return any(ext in url.lower() for ext in [".m3u8", ".mp4", ".flv", ".ts"])

async def fetch_html(url, referer=None):
    """使用 OmniBox 异步 API 请求 HTML"""
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
            return res.get("body", "")
    except Exception as e:
        await OmniBox.log("error", f"Fetch HTML 异常 [{url}]: {e}")
    return ""

def extract_title(html_text):
    title = ""
    m = re.search(r'<title>([^<]+)</title>', html_text, re.I)
    if m:
        title = m.group(1).strip()
        title = re.sub(r'详情介绍.*$', '', title)
        title = re.sub(r'在线观看.*$', '', title)
        title = re.sub(r'迅雷下载.*$', '', title)
        title = title.strip("- ")
    if title:
        return clean_text(title)
    
    for pat in [
        r'<h1[^>]*>(.*?)</h1>',
        r'<h2[^>]*>(.*?)</h2>',
        r'<div[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</div>',
        r'<strong[^>]*class=["\']title["\'][^>]*>(.*?)</strong>'
    ]:
        m = re.search(pat, html_text, re.S | re.I)
        if m:
            t = clean_text(m.group(1))
            if t:
                return t
    return ""

def extract_pic(html_text):
    patterns = [
        r'<img[^>]+data-original=["\']([^"\']+)["\'][^>]*>',
        r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*(?:poster|cover|thumb)[^"\']*["\']',
        r'<img[^>]+class=["\'][^"\']*(?:poster|cover|thumb)[^"\']*["\'][^>]+src=["\']([^"\']+)["\']'
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.I)
        if m:
            return fix_url(m.group(1))
    return ""

def extract_content(html_text):
    patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        r'<div[^>]*class=["\'][^"\']*(?:content|desc|summary|intro|vod-content)[^"\']*["\'][^>]*>(.*?)</div>'
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.S | re.I)
        if m:
            res = clean_text(m.group(1))
            if res:
                return res
    return ""

def extract_playlist(html_text):
    sources = []
    play_urls = []
    if etree:
        doc = etree.HTML(html_text)
        if doc is not None:
            panels = doc.xpath('//div[contains(@class,"play") or contains(@class,"playlist") or contains(@class,"source") or contains(@class,"panel")]')
            for panel in panels:
                try:
                    sname_list = panel.xpath('.//h3/text() | .//span[contains(@class,"name") or contains(@class,"title") or contains(@class,"tab")]/text() | .//div[contains(@class,"from")]/text()')
                    sname = clean_text(sname_list[0]) if sname_list else "默认线路"
                    eps = panel.xpath('.//a[contains(@href,"/vodplay/") or contains(@href,"/play/")]')
                    if not eps:
                        eps = panel.xpath('.//a[contains(@href,"vodplay")]')
                    ep_list = []
                    for ep in eps:
                        try:
                            ep_title_list = ep.xpath('./text()')
                            ep_title = clean_text(ep_title_list[0]) if ep_title_list else "播放"
                            ep_href_list = ep.xpath('./@href')
                            ep_href = ep_href_list[0] if ep_href_list else ""
                            if ep_href:
                                ep_list.append({"name": ep_title, "playId": fix_url(ep_href)})
                        except Exception:
                            continue
                    if ep_list:
                        sources.append({"name": sname, "episodes": ep_list})
                except Exception:
                    continue

    if not sources:
        eps = re.findall(r'<a[^>]+href=["\'](/vodplay/[^"\']+)["\'][^>]*>(.*?)</a>', html_text, re.S | re.I)
        if eps:
            ep_list = []
            for href, title in eps:
                title = clean_text(title) or "播放"
                ep_list.append({"name": title, "playId": fix_url(href)})
            if ep_list:
                sources.append({"name": "默认线路", "episodes": ep_list})
                
    return sources

async def extract_play_url(html_text, page_url):
    m = re.search(r'var\s+player_data\s*=\s*(\{.*?\});', html_text, re.DOTALL)
    if not m:
        m = re.search(r'player_data\s*=\s*(\{.*?\});', html_text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            url = data.get("url", "")
            encrypt = data.get("encrypt", "0")
            if encrypt == "1" or encrypt == 1:
                url = unquote(url)
            elif encrypt == "2" or encrypt == 2:
                url = unquote(base64.b64decode(url).decode("utf-8"))
            return url
        except Exception:
            pass

    for pat in [
        r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
        r'(https?://[^\s"\']+\.mp4[^\s"\']*)',
        r'var\s*now\s*=\s*["\']([^"\']+)["\']'
    ]:
        m = re.search(pat, html_text)
        if m:
            return m.group(1)

    m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html_text)
    if m:
        try:
            u = fix_url(m.group(1))
            h = await fetch_html(u, referer=page_url)
            if h:
                return await extract_play_url(h, u)
        except Exception:
            pass
    return ""

def parse_card_list(html_text):
    if not html_text or not etree:
        return []
    doc = etree.HTML(html_text)
    if doc is None:
        return []
    
    items = doc.xpath('//div[contains(@class,"row")]//dl')
    if not items:
        items = doc.xpath('//dl[.//a[contains(@href,"/voddetail/")]]')
        
    videos = []
    seen = set()
    for item in items:
        try:
            a = item.xpath('.//dt/a | .//dd/a')[0]
            tlist = a.xpath('.//h3/text() | ./@title | .//img/@alt')
            title = clean_text(tlist[0]) if tlist else ""
            hlist = item.xpath('.//dt/a/@href | .//dd/a/@href')
            href = hlist[0] if hlist else ""
            m = re.search(r'/voddetail/([0-9]+)/', href)
            vid = m.group(1) if m else href
            if not vid or vid in seen:
                continue
            seen.add(vid)
            
            plist = item.xpath('.//img/@data-original | .//img/@data-src | .//img/@src')
            pic = fix_url(plist[0]) if plist else ""
            
            videos.append({
                "vod_id": str(vid),
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": ""
            })
        except Exception:
            continue
    return videos

# ================= OmniBox Standard Handlers =================

async def home(params, context):
    """首页及分类树"""
    classes = [
        {"type_name": "制服诱惑", "type_id": "27"},
        {"type_name": "网红头条", "type_id": "317"},
        {"type_name": "主播网红", "type_id": "59"},
        {"type_name": "精东影业", "type_id": "430"},
        {"type_name": "麻豆资源", "type_id": "423"},
        {"type_name": "欧美美女", "type_id": "506"},
        {"type_name": "闷骚护士", "type_id": "97"},
        {"type_name": "探花约炮", "type_id": "276"},
        {"type_name": "主播诱惑", "type_id": "275"},
        {"type_name": "AV明星", "type_id": "144"},
        {"type_name": "AV解说", "type_id": "312"},
        {"type_name": "欧美", "type_id": "52"},
        {"type_name": "国产裸聊", "type_id": "374"},
        {"type_name": "三级伦理", "type_id": "163"},
        {"type_name": "国产自拍", "type_id": "274"},
        {"type_name": "国产视频", "type_id": "297"},
        {"type_name": "杏吧原创", "type_id": "435"},
        {"type_name": "剧情介绍", "type_id": "86"},
        {"type_name": "极品媚黑", "type_id": "315"},
        {"type_name": "貧乳小奶", "type_id": "179"},
        {"type_name": "明星换脸", "type_id": "307"},
        {"type_name": "韩国主播", "type_id": "319"},
        {"type_name": "映画传媒", "type_id": "165"},
        {"type_name": "兔子先生", "type_id": "434"},
        {"type_name": "少女萝莉", "type_id": "361"},
        {"type_name": "家庭乱伦", "type_id": "397"},
        {"type_name": "女优明星", "type_id": "287"},
        {"type_name": "可爱学生", "type_id": "93"},
        {"type_name": "国产自拍", "type_id": "375"},
        {"type_name": "明星换脸", "type_id": "152"},
        {"type_name": "AV解说", "type_id": "153"},
        {"type_name": "国产精品", "type_id": "49"},
        {"type_name": "禁漫", "type_id": "53"},
        {"type_name": "素人自拍", "type_id": "80"},
        {"type_name": "SM调教", "type_id": "401"},
        {"type_name": "瑜伽裤", "type_id": "96"},
        {"type_name": "群交淫乱", "type_id": "367"},
        {"type_name": "日本无码", "type_id": "301"}
    ]
    try:
        # 获取默认首个分类作为推荐
        url = f"{SITE_HOST}/vodtype/27/"
        html_text = await fetch_html(url)
        vod_list = parse_card_list(html_text)
        return {"class": classes, "list": vod_list}
    except Exception as e:
        await OmniBox.log("error", f"[home] 异常: {e}")
        return {"class": classes, "list": []}

async def category(params, context):
    """分类筛选与分页"""
    try:
        tid = params.get("categoryId") or "27"
        page = int(params.get("page") or 1)
        prefix = "arttype" if tid == "506" else "vodtype"
        
        url = f"{SITE_HOST}/{prefix}/{tid}/" if page == 1 else f"{SITE_HOST}/{prefix}/{tid}-{page}/"
        html_text = await fetch_html(url)
        if not html_text:
            return {"page": page, "pagecount": 1, "total": 0, "list": []}

        videos = parse_card_list(html_text)
        
        maxpg = page
        if etree:
            doc = etree.HTML(html_text)
            if doc is not None:
                plinks = doc.xpath('//div[@class="pagination"]//a/@href')
                for pl in plinks:
                    m = re.search(r'/(?:vod|art)type/\d+-(\d+)/', pl)
                    if m:
                        p = int(m.group(1))
                        if p > maxpg:
                            maxpg = p
                            
        if maxpg == page and len(videos) >= 24:
            maxpg = page + 1

        return {
            "page": page,
            "pagecount": maxpg,
            "total": 999999,
            "list": videos
        }
    except Exception as e:
        await OmniBox.log("error", f"[category] 异常: {e}")
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}

async def detail(params, context):
    """视频详情解析"""
    try:
        vid = params.get("videoId")
        if not vid:
            return {"list": []}

        url = f"{SITE_HOST}/voddetail/{vid}/"
        html_text = await fetch_html(url)
        if not html_text:
            return {"list": []}

        title = extract_title(html_text) or str(vid)
        pic = extract_pic(html_text)
        content = extract_content(html_text)
        play_sources = extract_playlist(html_text)

        if not play_sources:
            direct_url = await extract_play_url(html_text, url)
            if direct_url:
                play_sources = [{
                    "name": "默认线路",
                    "episodes": [{"name": "正片", "playId": direct_url}]
                }]
            else:
                play_sources = [{
                    "name": "默认线路",
                    "episodes": [{"name": "播放", "playId": f"{SITE_HOST}/vodplay/{vid}-1-1/"}]
                }]

        vod_item = {
            "vod_id": str(vid),
            "vod_name": title,
            "vod_pic": pic,
            "vod_content": content,
            "vod_play_sources": play_sources
        }
        return {"list": [vod_item]}
    except Exception as e:
        await OmniBox.log("error", f"[detail] 异常: {e}")
        return {"list": []}

async def search(params, context):
    """搜索功能"""
    try:
        keyword = (params.get("keyword") or params.get("wd") or "").strip()
        page = int(params.get("page") or 1)
        if not keyword:
            return {"page": 1, "pagecount": 1, "total": 0, "list": []}

        url = f"{SITE_HOST}/vodsearch/-------------/?wd={quote(keyword)}&page={page}"
        html_text = await fetch_html(url)
        videos = parse_card_list(html_text)

        return {
            "page": page,
            "pagecount": page + 1 if len(videos) >= 24 else page,
            "total": 999999,
            "list": videos
        }
    except Exception as e:
        await OmniBox.log("error", f"[search] 异常: {e}")
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}

async def play(params, context):
    """播放器解析逻辑"""
    try:
        play_id = params.get("playId", "")
        flag = params.get("flag") or "play"
        
        if not play_id:
            raise ValueError("playId 缺失")

        headers = {
            "Referer": SITE_HOST + "/",
            "User-Agent": DEFAULT_HEADERS["User-Agent"]
        }

        # 1. 直接是 m3u8/mp4 等直链视频地址
        if is_video_format(play_id):
            return {
                "urls": [{"name": "播放", "url": play_id}],
                "flag": flag,
                "header": headers,
                "parse": 0
            }

        # 2. 属于 /vodplay/ 或 /play/ 页面，进入提取
        if "/vodplay/" in play_id or "/play/" in play_id or play_id.startswith("http"):
            html_text = await fetch_html(play_id, referer=SITE_HOST + "/")
            if html_text:
                purl = await extract_play_url(html_text, play_id)
                if purl:
                    return {
                        "urls": [{"name": "播放", "url": purl}],
                        "flag": flag,
                        "header": headers,
                        "parse": 0
                    }

        # 3. 兜底转交给 Web 容器 / 客户端硬解析
        return {
            "urls": [{"name": "网页解析", "url": play_id}],
            "flag": flag,
            "header": headers,
            "parse": 1
        }
    except Exception as e:
        await OmniBox.log("error", f"[play] 异常: {e}")
        return {"urls": [], "flag": params.get("flag", ""), "header": {}, "parse": 0}

if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
