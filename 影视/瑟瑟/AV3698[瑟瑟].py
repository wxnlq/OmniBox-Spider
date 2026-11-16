# -*- coding: utf-8 -*-
# @name AV3698
# @version 1.0.2
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/AV3698[瑟瑟].py

import re
import urllib.parse

import requests
from spider_runner import OmniBox, run

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
HOSTS = [
    'https://av3698.cc',
    'https://www.av3698.cc',
]

FALLBACK_CLASSES = [
    ('日韩无码', '54', '54'),
    ('国产主播', '55', '55'),
    ('日韩精品', '57', '57'),
    ('欧美劲爆', '58', '58'),
    ('成人动漫', '59', '59'),
    ('自拍偷拍', '60', '60'),
    ('伦理影片', '61', '61'),
    ('视频二区', '69', '69'),
    ('巨乳尤物', '70', '70'),
    ('颜射系列', '71', '71'),
    ('口交视频', '72', '72'),
    ('自慰系列', '73', '73'),
    ('教师学生', '74', '74'),
    ('群P换妻', '75', '75'),
    ('AI换脸', '76', '76'),
    ('视频三区', '56', '56'),
    ('中文字幕', '62', '62'),
    ('人妻系列', '63', '63'),
    ('制服诱惑', '64', '64'),
    ('强奸乱伦', '65', '65'),
    ('无码流出', '66', '66'),
    ('主播诱惑', '67', '67'),
    ('在线观看', '68', '68'),
    ('视频四区', '77', '77'),
    ('熟女专区', '78', '78'),
    ('欧美专区', '79', '79'),
    ('调教捆绑', '80', '80'),
    ('情趣丝袜', '81', '81'),
]

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})


def get_active_host():
    for host in HOSTS:
        try:
            r = SESSION.get(host + '/', timeout=5, verify=False)
            if r.status_code == 200 and r.text:
                return host
        except Exception:
            continue
    return HOSTS[0]


def http_get(url, timeout=15):
    try:
        r = SESSION.get(url, timeout=timeout, verify=False)
        r.encoding = 'utf-8'
        return r.text
    except Exception:
        return ''


def parse_cards(html):
    items = []
    if not html:
        return items
    for m in re.finditer(r'<article class="media-card">([\s\S]*?)</article>', html):
        box = m.group(1)
        href_match = re.search(r'href="(/xwatch/\d+)"', box)
        if not href_match:
            continue
        vod_id = href_match.group(1)
        title_match = re.search(r'class="card-title"[^>]*>([^<]+)</a>', box)
        title = title_match.group(1).strip() if title_match else vod_id
        pic_match = re.search(r'<img[^>]+src="([^"]+)"', box)
        pic = pic_match.group(1) if pic_match else ''
        remark_match = re.search(r'class="duration"[^>]*>([^<]+)<', box)
        remark = remark_match.group(1).strip() if remark_match else ''
        if 'cached-thumb?url=' in pic:
            u = re.search(r'url=([^&"]+)', pic)
            if u:
                pic = urllib.parse.unquote(u.group(1))
        items.append({
            'vod_id': vod_id,
            'vod_name': title,
            'vod_pic': pic,
            'vod_remarks': remark,
        })
    return items


def get_class_items():
    return [{'type_id': str(cid), 'type_name': name} for name, cid, _ in FALLBACK_CLASSES]


async def home(params, context):
    await OmniBox.log('info', '加载 AV3698 首页')
    host = get_active_host()
    html = http_get(host + '/')
    list_items = parse_cards(html)
    if not list_items:
        html = http_get(f'{host}/?source=external&category=54')
        list_items = parse_cards(html)
    return {
        'class': get_class_items(),
        'filters': {},
        'list': list_items,
    }


async def category(params, context):
    category_id = str((params or {}).get('categoryId') or '54')
    page = int((params or {}).get('page') or 1)
    host = get_active_host()
    url = f'{host}/?q=&source=external&category={category_id}&page={page}'
    html = http_get(url)
    videos = parse_cards(html)
    pagecount = 1
    match = re.search(r'第\s*(\d+)\s*/\s*(\d+)\s*页', html)
    if match:
        pagecount = max(1, int(match.group(2)))
    return {
        'page': page,
        'pagecount': pagecount,
        'total': len(videos),
        'list': videos,
    }


async def detail(params, context):
    video_id = str((params or {}).get('videoId') or '').strip()
    if not video_id:
        return {'list': []}
    host = get_active_host()
    if not video_id.startswith('/'):
        video_id = '/xwatch/' + video_id
    html = http_get(host + video_id)
    if not html:
        return {'list': []}

    title_match = re.search(r'<title>([^<]+)', html)
    title = title_match.group(1).replace(' · av3698.cc', '').strip() if title_match else video_id

    stream = ''
    m = re.search(r'data-stream="([^"]+)"', html)
    if m:
        stream = m.group(1)
    if not stream:
        m2 = re.search(r'https?://[^"\'\s\\]+\.m3u8[^"\'\s\\]*', html)
        if m2:
            stream = m2.group(0)
    if not stream:
        return {'list': []}
    stream = urllib.parse.urljoin(host + '/', stream)
    stream_parts = urllib.parse.urlsplit(stream)
    if stream_parts.path.rstrip('/').endswith('/proxy-m3u8'):
        upstream = urllib.parse.parse_qs(stream_parts.query).get('url', [''])[0]
        upstream_parts = urllib.parse.urlsplit(upstream)
        if upstream_parts.scheme not in ('http', 'https') or not upstream_parts.netloc:
            raise ValueError('AV3698 的 proxy-m3u8 地址未包含有效的上游 M3U8 URL')
        stream = upstream

    return {'list': [{
        'vod_id': video_id,
        'vod_name': title,
        'vod_pic': '',
        'vod_content': title,
        'vod_year': '',
        'vod_remarks': 'M3U8',
        'vod_douban_score': '',
        'vod_actor': '',
        'vod_director': '',
        'vod_area': '',
        'vod_play_sources': [{
            'name': 'av3698',
            'episodes': [{
                'name': '播放',
                'playId': stream,
            }],
        }],
    }]}


async def search(params, context):
    keyword = str((params or {}).get('keyword') or (params or {}).get('wd') or '').strip()
    page = int((params or {}).get('page') or 1)
    if not keyword:
        return {'page': 1, 'pagecount': 0, 'total': 0, 'list': []}
    host = get_active_host()
    kw = urllib.parse.quote(keyword)
    html = http_get(f'{host}/?q={kw}&page={page}')
    videos = parse_cards(html)
    return {
        'page': page,
        'pagecount': 1,
        'total': len(videos),
        'list': videos,
    }


async def play(params, context):
    play_id = str((params or {}).get('playId') or '').strip()
    if not play_id:
        raise ValueError('playId 不能为空')
    return {
        'urls': [{'name': '播放', 'url': play_id}],
        'flag': 'play',
        'header': {
            'User-Agent': UA,
            'Referer': get_active_host() + '/',
        },
        'parse': 0,
    }


if __name__ == '__main__':
    run({
        'home': home,
        'category': category,
        'detail': detail,
        'search': search,
        'play': play,
    })
