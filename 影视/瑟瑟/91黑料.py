# -*- coding: utf-8 -*-
# @name 首页
# @version 1.0.0

import sys
import requests
from bs4 import BeautifulSoup
import re
from spider_runner import OmniBox, run

xurl = "https://kb11.adultporna-av1sim111.xyz"
headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
}

# ====================== 首页 ======================
async def home(params, context):
    await OmniBox.log("info", "加载首页")
    try:
        res = requests.get(xurl + '/zzzz', headers=headerx)
        res.encoding = "utf-8"
        doc = BeautifulSoup(res.text, "html.parser")
        classes = []
        classes.append({'type_id': '/t/86', 'type_name': '女优'})
        classes.append({'type_id': '/t/141', 'type_name': '日本番號'})
        classes.append({'type_id': '/t/5', 'type_name': '日本无码'})
        classes.append({'type_id': '/t/32', 'type_name': '日本巨乳无码'})
        classes.append({'type_id': '/t/34', 'type_name': '日本人妻无码'})
        classes.append({'type_id': '/t/35', 'type_name': '日本制服无码'})        
        classes.append({'type_id': '/t/223', 'type_name': '日本乱伦无码'})
        classes.append({'type_id': '/t/224', 'type_name': '日本强奸无码'})        
        classes.append({'type_id': '/t/36', 'type_name': '日本丝袜美腿'})
        classes.append({'type_id': '/t/13', 'type_name': '日本中文字幕'})
        classes.append({'type_id': '/t/53', 'type_name': '日本绝美少女'}) 
        classes.append({'type_id': '/t/6', 'type_name': '日本强奸乱伦'})
        classes.append({'type_id': '/t/7', 'type_name': '日本巨乳'})
        classes.append({'type_id': '/t/9', 'type_name': '日本制服诱惑'})
        classes.append({'type_id': '/t/11', 'type_name': '日本调教'})
        classes.append({'type_id': '/t/58', 'type_name': '日本口爆'})
        classes.append({'type_id': '/t/30', 'type_name': '欧美'})
        classes.append({'type_id': '/t/164', 'type_name': '成人动漫'})
        classes.append({'type_id': '/t/85', 'type_name': '伦理电影'}) 
        classes.append({'type_id': '/t/2', 'type_name': '国产传媒'})
        classes.append({'type_id': '/t/163', 'type_name': '国产视频'})        
        classes.append({'type_id': '/t/67', 'type_name': '国产空姐模特'})
        classes.append({'type_id': '/t/69', 'type_name': '国产学生'})
        classes.append({'type_id': '/t/70', 'type_name': '国产人妻熟女'})
        classes.append({'type_id': '/t/71', 'type_name': '国产乱伦'})
        classes.append({'type_id': '/t/72', 'type_name': '国产自慰'})
        classes.append({'type_id': '/t/73', 'type_name': '国产野合车震'})
        classes.append({'type_id': '/t/75', 'type_name': '国产名人'})
        classes.append({'type_id': '/t/74', 'type_name': '国产OL'})
        classes.append({'type_id': '/t/18', 'type_name': '国产剧情'})
        classes.append({'type_id': '/t/19', 'type_name': '国产偷怕'})
        classes.append({'type_id': '/t/76', 'type_name': '国产网曝'})        
        classes.append({'type_id': '/t/227', 'type_name': '综合传媒'})
        classes.append({'type_id': '/t/38', 'type_name': '麻豆合集'})
        classes.append({'type_id': '/t/109', 'type_name': '葫芦影业'})        
        classes.append({'type_id': '/t/111', 'type_name': '天美传媒'})
        classes.append({'type_id': '/t/112', 'type_name': '果冻传媒'})
        classes.append({'type_id': '/t/131', 'type_name': '91制片厂'})
        classes.append({'type_id': '/t/113', 'type_name': '蜜桃传媒'})
        classes.append({'type_id': '/t/114', 'type_name': '精东影业'})
        classes.append({'type_id': '/t/115', 'type_name': '皇家华人'})
        classes.append({'type_id': '/t/116', 'type_name': 'SWAG'})       
        classes.append({'type_id': '/t/120', 'type_name': '兔子先生'})
        classes.append({'type_id': '/t/122', 'type_name': 'PsychoPornTW'})        
        classes.append({'type_id': '/t/124', 'type_name': '微啪 & 陌丽影像传媒'})
        classes.append({'type_id': '/t/125', 'type_name': '大象传媒'})
        classes.append({'type_id': '/t/126', 'type_name': '乌鸦传媒'})
        classes.append({'type_id': '/t/141', 'type_name': '日本番号'})
        classes.append({'type_id': '/t/225', 'type_name': '综合番号'})
        classes.append({'type_id': '/t/142', 'type_name': '200GANA'})
        classes.append({'type_id': '/t/146', 'type_name': '259LUXU'})
        classes.append({'type_id': '/t/147', 'type_name': '261ARA'})
        classes.append({'type_id': '/t/148', 'type_name': '277DCV'})
        classes.append({'type_id': '/t/143', 'type_name': '300MIUM'})
        classes.append({'type_id': '/t/149', 'type_name': '300MAAN'})
        classes.append({'type_id': '/t/150', 'type_name': '300NTK'})
        classes.append({'type_id': '/t/152', 'type_name': '328HMDN'})        
        classes.append({'type_id': '/t/154', 'type_name': '336KNB'})
        classes.append({'type_id': '/t/155', 'type_name': '348NTR'})
        classes.append({'type_id': '/t/156', 'type_name': '390JAC'})
        classes.append({'type_id': '/t/158', 'type_name': '428SUKE'})
        classes.append({'type_id': '/t/181', 'type_name': 'AARM'})
        classes.append({'type_id': '/t/180', 'type_name': 'ADN'})
        classes.append({'type_id': '/t/185', 'type_name': 'ATID'})        
        classes.append({'type_id': '/t/192', 'type_name': 'DFDM'})
        classes.append({'type_id': '/t/194', 'type_name': 'DLDSS'})
        vodss = doc.find_all('dd')

        for vod in vodss:
            id = vod.find('a')['href'].rstrip("/")
            name = vod.find('a').text
            if not any(d['type_name'] == name for d in classes):
                classes.append({'type_id': id, 'type_name': name})

        res2 = requests.get(xurl + '/show/30/', headers=headerx)
        res2.encoding = "utf-8"
        doc2 = BeautifulSoup(res2.text, "html.parser")
        vodss2 = doc2.find('ul', class_='row row-space8 row-m-space8')
        vods2 = vodss2.find_all('li') if vodss2 else []
        videos = []

        for vod in vods2:
            name = vod.select_one('section a')['title']
            vid = vod.select_one('section a')['href']
            remarks = vod.select_one('section a span small').text
            pic = vod.select_one('section a img')['src']
            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "type_id": "",
                "type_name": "",
                "vod_remarks": remarks,
                "vod_year": "",
                "vod_douban_score": ""
            })

        return {"class": classes, "list": videos}
    except:
        return {"class": [], "list": []}

# ====================== 分类列表 ======================
async def category(params, context):
    category_id = params.get("categoryId") or ""
    page = params.get("page") or 1
    pg = str(page)

    try:
        if pg == "" or pg == "1":
            url = xurl + category_id
        else:
            url = xurl + category_id + '-' + str(pg)

        res = requests.get(url=url, headers=headerx)
        res.encoding = "utf-8"
        doc = BeautifulSoup(res.text, "html.parser")
        vodss = doc.find('ul', class_='row row-space8 row-m-space8')
        vods = vodss.find_all('li') if vodss else []
        videos = []

        for vod in vods:
            name = vod.select_one('section a')['title']
            vid = vod.select_one('section a')['href']
            remarks = vod.select_one('section a span small').text
            pic = vod.select_one('section a img')['src']
            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "type_id": "",
                "type_name": "",
                "vod_remarks": remarks,
                "vod_year": "",
                "vod_douban_score": ""
            })

        return {
            "page": int(page),
            "pagecount": 9999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 详情 ======================
async def detail(params, context):
    video_id = params.get("videoId")
    if not video_id:
        return {"list": []}

    try:
        did = video_id.replace("voddetail", "v")
        res = requests.get(url=xurl + did, headers=headerx)
        res.encoding = "utf-8"
        source_match = re.search(r'"","url":"(.*?)"', res.text)
        purl = ""
        if source_match:
            purl = source_match.group(1).replace("\\", "")

        episodes = []
        if purl:
            episodes.append({
                "name": "播放",
                "playId": purl
            })

        return {
            "list": [{
                "vod_id": video_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_content": "",
                "vod_year": "",
                "vod_remarks": "",
                "vod_douban_score": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_area": "",
                "vod_play_sources": [{
                    "name": "直链播放",
                    "episodes": episodes
                }]
            }]
        }
    except:
        return {"list": []}

# ====================== 搜索 ======================
async def search(params, context):
    keyword = (params.get("keyword") or params.get("wd") or "").strip()
    page = params.get("page") or 1

    if not keyword:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

    try:
        header2 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }
        url = f"{xurl}/s/page/{page}/wd/{keyword}"
        res = requests.get(url, headers=header2)
        res.encoding = "utf-8"
        doc = BeautifulSoup(res.text, "html.parser")
        vodss = doc.find('ul', class_='row row-space8 row-m-space8')
        vods = vodss.find_all('li') if vodss else []
        videos = []

        for vod in vods:
            name = vod.select_one('section a')['title']
            vid = vod.select_one('section a')['href']
            remarks = vod.select_one('section a span small').text
            pic = vod.select_one('section a img')['src']
            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "type_id": "",
                "type_name": "",
                "vod_remarks": remarks,
                "vod_year": "",
                "vod_douban_score": ""
            })

        return {
            "page": int(page),
            "pagecount": 9999,
            "total": 999999,
            "list": videos
        }
    except:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}

# ====================== 播放 ======================
async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": headerx,
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
