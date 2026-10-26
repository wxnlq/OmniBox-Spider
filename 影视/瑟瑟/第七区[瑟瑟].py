# -*- coding: utf-8 -*-
# @name 第七区
// @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/第七区[瑟瑟].py
// @version 0.0.1

import ast
import html
import random
import re
import urllib.parse

from lxml import etree
from spider_runner import OmniBox, run


DOMAIN_POOL = [
    "618600.xyz", "618601.xyz", "618602.xyz", "618603.xyz", "618604.xyz",
    "618605.xyz", "618606.xyz", "618607.xyz", "618608.xyz", "618609.xyz",
    "618610.xyz", "618611.xyz", "618612.xyz", "618613.xyz", "618614.xyz",
    "618615.xyz", "618620.xyz", "618621.xyz", "618622.xyz", "618623.xyz",
    "618624.xyz", "618625.xyz", "618626.xyz", "618627.xyz", "618629.xyz",
    "618630.xyz", "618631.xyz", "618632.xyz", "618633.xyz", "618634.xyz",
    "618635.xyz", "618636.xyz", "618637.xyz", "618639.xyz", "618640.xyz",
    "618641.xyz", "618642.xyz", "618644.xyz", "618645.xyz", "618646.xyz",
    "618647.xyz", "61860120.xyz", "618649.xyz", "618650.xyz", "618651.xyz",
    "618652.xyz", "618653.xyz", "618654.xyz", "618655.xyz", "618660.xyz",
    "618661.xyz", "618662.xyz", "618663.xyz", "618671.xyz", "618672.xyz",
    "618673.xyz", "618674.xyz", "618675.xyz", "618676.xyz", "618677.xyz",
    "61860100.xyz", "6186134.xyz", "6186133.xyz", "6186132.xyz",
    "6186131.xyz", "6186130.xyz", "6186129.xyz", "6186128.xyz",
    "6186127.xyz", "6186126.xyz", "6186125.xyz", "6186124.xyz",
    "6186123.xyz", "6186122.xyz", "6186121.xyz", "6186120.xyz",
    "6186119.xyz", "6186118.xyz", "6186117.xyz", "6186116.xyz",
    "6186115.xyz", "6186114.xyz", "6186113.xyz", "6186112.xyz",
    "6186111.xyz", "6186110.xyz", "6186109.xyz", "6186108.xyz",
    "6186107.xyz", "6186106.xyz", "6186105.xyz", "6186104.xyz",
    "6186103.xyz", "6186102.xyz", "6186101.xyz",
]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
SUBCATEGORY_IDS = (
    ("1", "凨遨襆頑"),
    ("13", "餙藉簾呁"),
    ("22", "劶枍譱恑"),
    ("6", "噽丧襆頑"),
    ("8", "溅縯岑姳"),
    ("9", "輣夹妧姶"),
    ("10", "姳和亓峞"),
    ("11", "綠为兺澔"),
    ("12", "襒苲拮澔"),
    ("20", "为夻焟姳"),
    ("23", "敥革勧恅"),
    ("21", "繏凸侦璆"),
    ("7", "抐为刨澫"),
    ("14", "簾呁丌厺"),
    ("40", "簾呁争厺"),
)
PLAINTEXT_SUBCATEGORY_IDS = {"3"}
_site_config = None


async def request_text(url, headers=None):
    response = await OmniBox.request(url, {
        "method": "GET",
        "headers": headers or HEADERS,
    })
    status = response.get("statusCode")
    if status is not None and not 200 <= int(status) < 300:
        raise RuntimeError("HTTP %s: %s" % (status, response.get("body", "")))
    return str(response.get("body") or "")


def parse_link_script(script):
    def parse_array(name, pattern):
        match = re.search(pattern, script, re.DOTALL)
        if not match:
            raise ValueError("入口脚本缺少 %s 配置" % name)
        value = ast.literal_eval(match.group(1))
        if not isinstance(value, list):
            raise ValueError("入口脚本 %s 配置格式无效" % name)
        return value

    zone_domains = parse_array(
        "zuArr", r"\bzuArr\s*=\s*(\[\[.*?\]\])\s*;"
    )
    zone_names = parse_array("z", r"\bz\s*=\s*(\[[^\]]*\])")
    zone_types = parse_array("t", r"\bt\s*=\s*(\[[^\]]*\])")
    zone_ids = parse_array("i", r"\bi\s*=\s*(\[[^\]]*\])")
    if not (len(zone_domains) >= 10 and len(zone_names) >= 10
            and len(zone_types) >= 10 and len(zone_ids) >= 10):
        raise ValueError("入口脚本分区配置不完整")

    column_count = min(30, *(len(row) for row in zone_domains[:10]))
    if column_count < 1:
        raise ValueError("入口脚本域名配置为空")
    column = random.randrange(column_count)

    index = 6
    domain_suffix = str(zone_domains[index][column])
    if not domain_suffix.isdigit():
        raise ValueError("入口脚本包含无效域名")
    domain = "618%s.xyz" % domain_suffix
    content_type = str(zone_types[index])
    if content_type not in ("vod", "art"):
        raise ValueError("入口脚本包含无效内容类型")
    type_id = str(zone_ids[index])
    if not type_id.isdigit():
        raise ValueError("入口脚本包含无效分类 ID")
    return [{
        "type_id": "%s_%s_%s" % (domain, content_type, type_id),
        "type_name": str(zone_names[index]),
    }]


async def get_site_config():
    global _site_config
    if _site_config:
        return _site_config

    candidates = ["618640.xyz"]
    candidates.extend(domain for domain in DOMAIN_POOL if domain not in candidates)
    remaining_candidates = candidates[1:]
    random.shuffle(remaining_candidates)
    candidates = candidates[:1] + remaining_candidates
    last_error = None
    for domain in candidates:
        root_url = "https://%s/" % domain
        try:
            page_html = await request_text(root_url)
            doc = html_document(page_html)
            scripts = doc.xpath("//script[@src]/@src") if doc is not None else []
            script_urls = [urllib.parse.urljoin(root_url, src) for src in scripts]
            script_urls.sort(key=lambda url: "center_upload" not in url, reverse=False)
            for script_url in script_urls:
                try:
                    script = await request_text(script_url, {
                        "User-Agent": USER_AGENT,
                        "Referer": root_url,
                    })
                    classes = parse_link_script(script)
                    _site_config = {
                        "entry_host": root_url.rstrip("/"),
                        "classes": classes,
                    }
                    await OmniBox.log(
                        "info", "已从入口脚本获取 %d 个分区" % len(classes)
                    )
                    return _site_config
                except Exception as error:
                    last_error = error
        except Exception as error:
            last_error = error

    raise RuntimeError("无法获取入口页分区配置: %s" % last_error)


def html_document(content):
    return etree.HTML(content) if content else None


def decrypt_title(encrypted_text):
    try:
        return "".join(chr(ord(char) ^ 128) for char in encrypted_text)
    except (TypeError, ValueError):
        return encrypted_text


def make_subcategory_classes(zone_type_id):
    domain = zone_type_id.split("_", 1)[0]
    if not re.fullmatch(r"618\d+\.xyz", domain):
        raise ValueError("分区域名无效")
    return [
        {
            "type_id": "%s_vod_%s" % (domain, category_id),
            "type_name": (
                encrypted_name
                if category_id in PLAINTEXT_SUBCATEGORY_IDS
                else decrypt_title(encrypted_name)
            ),
        }
        for category_id, encrypted_name in SUBCATEGORY_IDS
    ]


def extract_total_pages(text):
    match = re.search(r"const totalPages\s*=\s*['\"]?(\d+)['\"]?", text or "")
    return int(match.group(1)) if match else None


def normalize_pic_url(pic_url, host):
    if not pic_url:
        return ""
    pic_url = pic_url.strip()
    if pic_url.startswith("//"):
        pic_url = "https:" + pic_url
    elif pic_url.startswith("/"):
        pic_url = host + pic_url
    elif not pic_url.startswith("http"):
        pic_url = host + "/" + pic_url
    return pic_url.replace(" ", "%20")


def extract_videos(doc, host, limit=None):
    if doc is None:
        return []
    videos = []
    elements = doc.xpath(
        '//ul[contains(@class,"thumbnail-group")]'
        '//a[contains(@class,"thumbnail")]'
        '|//a[contains(concat(" ", normalize-space(@class), " "), " vodbox ")]'
    )
    for element in elements:
        try:
            href_nodes = element.xpath("./@href")
            if not href_nodes:
                continue
            href = html.unescape(href_nodes[0])
            if href.startswith("/"):
                href = host + href

            decoded_href = html.unescape(href)
            parsed = urllib.parse.urlparse(decoded_href)
            query = urllib.parse.parse_qs(parsed.query)
            pic_url = query.get("b", [""])[0]
            vod_id = urllib.parse.quote(href, safe="")

            title_nodes = element.xpath(
                './/span[contains(@class,"title")]/text()'
            )
            encrypted_title = False
            if not title_nodes:
                title_nodes = element.xpath(
                    './/p[contains(concat(" ", normalize-space(@class), " "), '
                    '" km-script ")]/text()'
                )
                encrypted_title = bool(title_nodes)
            if not title_nodes:
                title_nodes = element.xpath(".//img/@alt | .//img/@title")
            raw_title = title_nodes[0].strip() if title_nodes else ""
            title = decrypt_title(raw_title) if encrypted_title else raw_title
            title = re.sub(r"\s+", " ", title).strip() or "未知标题"

            if not pic_url:
                for attribute in ("data-original", "data-src", "src"):
                    image_nodes = element.xpath(".//img/@%s" % attribute)
                    if image_nodes:
                        pic_url = image_nodes[0]
                        break

            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": normalize_pic_url(pic_url, host),
                "vod_remarks": "",
                "vod_year": "",
            })
        except (IndexError, TypeError, ValueError) as error:
            print("[第七区] 提取视频出错: %s" % error)
    return videos[:limit] if limit else videos


def parse_pagecount(doc, page_html):
    pagecount = 5
    page_elements = doc.xpath('//ul[@class="pagination"]/li/a') if doc is not None else []
    if page_elements:
        for element in page_elements:
            text = element.text or ""
            if "尾" in text or "last" in text.lower():
                href = element.xpath("./@href")
                match = re.search(r"/page/(\d+)\.html", href[0]) if href else None
                if match:
                    pagecount = int(match.group(1))
                    break
    else:
        pagecount = extract_total_pages(page_html) or pagecount
    return pagecount


def category_url(category_id, page=1):
    parts = category_id.split("_", 2)
    if len(parts) == 3:
        domain, content_type, type_id = parts
    elif len(parts) == 2:
        domain, type_id = parts
        content_type = "vod"
    else:
        raise ValueError("分类 ID 格式无效")
    if not re.fullmatch(r"618\d+\.xyz", domain):
        raise ValueError("分类域名无效")
    if content_type not in ("vod", "art") or not type_id.isdigit():
        raise ValueError("分类类型或 ID 无效")
    url = "https://%s/index.php/%s/type/id/%s.html" % (
        domain, content_type, type_id
    )
    return url.replace(".html", "/page/%s.html" % page) if page > 1 else url


def allowed_page_url(value):
    url = urllib.parse.urlparse(value)
    if (url.scheme not in ("http", "https") or not url.hostname
            or not re.fullmatch(r"618\d+\.xyz", url.hostname)):
        raise ValueError("视频地址无效")
    return value


async def home(params, context):
    config = await get_site_config()
    zone = config["classes"][0]
    try:
        url = category_url(zone["type_id"])
        page_html = await request_text(url)
        host = "https://%s" % urllib.parse.urlparse(url).netloc
        return {
            "class": make_subcategory_classes(zone["type_id"]),
            "list": extract_videos(html_document(page_html), host, limit=20),
        }
    except Exception as error:
        await OmniBox.log("error", "首页获取出错: %s" % error)
        return {
            "class": make_subcategory_classes(zone["type_id"]),
            "list": [],
        }


async def category(params, context):
    params = params or {}
    try:
        page = max(1, int(params.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    category_id = str(params.get("categoryId") or "")
    try:
        url = category_url(category_id, page)
        domain = urllib.parse.urlparse(url).netloc
        page_html = await request_text(url)
        doc = html_document(page_html)
        videos = extract_videos(doc, "https://%s" % domain, limit=20)
        pagecount = parse_pagecount(doc, page_html)
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20,
            "list": videos,
        }
    except Exception as error:
        await OmniBox.log("error", "分类内容获取出错: %s" % error)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


async def search(params, context):
    params = params or {}
    keyword = str(params.get("keyword") or params.get("wd") or "").strip()
    try:
        page = max(1, int(params.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    config = await get_site_config()
    first_domain = config["classes"][0]["type_id"].split("_", 1)[0]
    host = "https://%s" % first_domain
    url = "%s/index.php/vod/search/wd/%s/page/%s.html" % (
        host, urllib.parse.quote(keyword), page
    )
    try:
        page_html = await request_text(url)
        doc = html_document(page_html)
        pagecount = parse_pagecount(doc, page_html)
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20,
            "list": extract_videos(doc, host, limit=20),
        }
    except Exception as error:
        await OmniBox.log("error", "搜索出错: %s" % error)
        return {"page": page, "pagecount": 0, "total": 0, "list": []}


async def detail(params, context):
    video_id = str((params or {}).get("videoId") or "").strip()
    if not video_id:
        return {"list": []}
    try:
        play_url = urllib.parse.unquote(video_id)
        play_url = allowed_page_url(html.unescape(play_url))
        parsed = urllib.parse.urlparse(play_url)
        query = urllib.parse.parse_qs(parsed.query)
        pic_url = query.get("b", [""])[0]
        host = "%s://%s" % (parsed.scheme, parsed.netloc)

        title_match = re.search(
            r"/([^/]+)\.html$", urllib.parse.unquote(parsed.path)
        )
        title = (
            decrypt_title(title_match.group(1).replace(" ", ""))
            if title_match else "未知标题"
        )
        if not pic_url:
            try:
                page_html = await request_text(play_url)
                doc = html_document(page_html)
                if doc is not None:
                    for xpath in (
                        '//meta[@property="og:image"]/@content',
                        '//div[contains(@class,"video-cover")]//img/@src',
                        '//div[contains(@class,"poster")]//img/@src',
                        '//img[contains(@class,"cover")]/@src',
                        '//img[@class="lazy"]/@data-original',
                        '//img[@class="lazy"]/@data-src',
                    ):
                        image_nodes = doc.xpath(xpath)
                        if image_nodes:
                            pic_url = image_nodes[0]
                            break
            except Exception as error:
                await OmniBox.log("warning", "详情封面获取失败: %s" % error)

        return {"list": [{
            "vod_id": video_id,
            "vod_name": title,
            "vod_pic": normalize_pic_url(pic_url, host),
            "vod_remarks": "",
            "vod_year": "",
            "vod_play_sources": [{
                "name": "直接播放",
                "episodes": [{"name": "第1集", "playId": play_url}],
            }],
        }]}
    except Exception as error:
        await OmniBox.log("error", "详情获取出错: %s" % error)
        return {"list": []}


async def play(params, context):
    params = params or {}
    play_id = str(params.get("playId") or "").strip()
    if not play_id:
        raise ValueError("playId 不能为空")

    play_url = allowed_page_url(html.unescape(urllib.parse.unquote(play_id)))
    parsed = urllib.parse.urlparse(play_url)
    video_url = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
    if video_url:
        return {
            "urls": [{"name": "播放", "url": video_url}],
            "flag": params.get("flag") or "play",
            "header": {"User-Agent": USER_AGENT, "Referer": "%s://%s/" % (
                parsed.scheme, parsed.netloc
            )},
            "parse": 0,
        }

    try:
        page_html = await request_text(play_url)
        match = re.search(
            r"""["']((?:https?:)?//[^"']+\.m3u8[^"']*)["']""",
            page_html,
            re.IGNORECASE,
        )
        if match:
            video_url = match.group(1)
            if video_url.startswith("//"):
                video_url = "https:" + video_url
            return {
                "urls": [{"name": "播放", "url": video_url}],
                "flag": params.get("flag") or "play",
                "header": {"User-Agent": USER_AGENT, "Referer": play_url},
                "parse": 0,
            }
    except Exception as error:
        await OmniBox.log("error", "播放地址获取出错: %s" % error)

    return {
        "urls": [{"name": "播放", "url": play_url}],
        "flag": params.get("flag") or "play",
        "header": {"User-Agent": USER_AGENT},
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
