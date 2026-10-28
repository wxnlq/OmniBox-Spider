# -*- coding: utf-8 -*-
# @name 少女破处
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/少女破处[瑟瑟].py
# @version 1.0.0

import re
import html
import json
from urllib.parse import quote, unquote
import requests
from spider_runner import OmniBox, run

HOST = "https://83w43wdlty.md-md22.top"

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Referer": HOST + "/",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
}

session = requests.Session()
session.headers.update(headers)


def _get(url):
    for _ in range(3):
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                return ""
            return r.content.decode("utf-8", errors="ignore")
        except Exception:
            continue
    return ""


def _decode(h):
    m = re.search(r'var Words\s*=\s*"([^"]+)"', h)
    if not m:
        return h
    d = re.sub(r'%u([0-9a-fA-F]{4})', lambda x: chr(int(x.group(1), 16)), m.group(1))
    return unquote(d)


def _abs(u):
    if not u:
        return ""
    if u.startswith("http"):
        return u
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return HOST + u
    return HOST + "/" + u


def _cards(h):
    lst = []
    seen = set()
    for m in re.finditer(r"<article>(.*?)</article>", h, re.S):
        block = m.group(1)
        um = re.search(r'href="(/(?:detail|video)/\?\d+(?:-\d+)*\.html)"', block)
        if not um:
            continue
        vid = re.search(r"\?(\d+(?:-\d+)*)\.html", um.group(1))
        if not vid:
            continue
        vid = vid.group(1)
        if vid in seen:
            continue
        seen.add(vid)

        nm = re.search(r"<cite>([^<]+)</cite>", block)
        if not nm:
            nm = re.search(r'alt="([^"]+)"', block)
        name = html.unescape(nm.group(1).strip()) if nm else ""
        if not name:
            continue

        pm = re.search(r'data-src="([^"]+)"', block)
        if not pm:
            pm = re.search(r'<img[^>]*src="([^"]+)"', block)
        pic = _abs(pm.group(1)) if pm else ""

        lst.append({
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_remarks": "",
        })
    return lst


def _parse_player_json(h, varname):
    idx = h.find(f"var {varname}=")
    if idx < 0:
        return None
    seg = h[idx:idx + 12000]
    start = seg.find("{")
    if start < 0:
        return None
    depth = 0
    for i, c in enumerate(seg[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(seg[start:i + 1])
                except Exception:
                    return None
    return None


def _decode_url(url, encrypt):
    if not url:
        return ""
    try:
        if encrypt == 1:
            return unquote(url)
        if encrypt == 2:
            import base64
            return unquote(base64.b64decode(unquote(url)).decode("utf-8", errors="ignore"))
    except Exception:
        pass
    return url


def _decode_obfuscated_js(h):
    try:
        scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', h, re.S)
        for s in scripts:
            s = s.strip()
            if len(s) < 100 or "var b=" not in s:
                continue
            m = re.search(r'var b=(\{.*?\});', s, re.S)
            if not m:
                continue
            pairs = re.findall(r'(?:"([^"]+)"|([A-Za-z0-9_]+))\s*:\s*"((?:[^"\\]|\\.)*)"', m.group(1))
            mp = {(qk if qk else bk): v for qk, bk, v in pairs}
            em = re.search(r'var b=a\(`([^`]+)`', s)
            if not em:
                continue
            dec = ''.join(mp.get(c, c) for c in em.group(1))
            mm = re.search(r'https?://[^\s"\'<>]+?\.(m3u8|mp4)[^\s"\'<>]*', dec)
            if mm:
                return mm.group(0)
    except Exception:
        pass
    return ""


def _extract_play_url(h):
    for varname in ["player_aaaa", "player_data"]:
        data = _parse_player_json(h, varname)
        if data and data.get("url"):
            u = _decode_url(data["url"], data.get("encrypt", 0))
            if u:
                return u

    m = re.search(r'<mark[^>]+data-user-name="([^"]+)"', h, re.I)
    if m:
        u = m.group(1).strip()
        if u.startswith("http"):
            return u

    m = re.search(r'MacPlayer\.PlayUrl\s*=\s*["\']([^"\']+)["\']', h)
    if m and m.group(1).strip():
        return m.group(1).strip()

    m = re.search(r"var dp_video_url\s*=\s*['\"]([^'\"]+)['\"]", h)
    if m:
        try:
            import base64
            return base64.b64decode(m.group(1)).decode("utf-8", errors="ignore")
        except Exception:
            pass

    m = re.search(r'<iframe[^>]*src="([^"]+)"', h)
    if m:
        return m.group(1)

    for m in re.finditer(r'"url"\s*:\s*"([^"]+)"', h):
        u = m.group(1).replace('\\/', '/').replace('\\', '')
        if re.search(r'\.(m3u8|mp4)(\?|$)', u) and u.startswith('http'):
            return u

    u = _decode_obfuscated_js(h)
    if u:
        return u

    return ""


def _normalize_video_id(vid):
    if not vid:
        return ""
    vid = str(vid).strip()
    if not vid:
        return ""
    if re.match(r'^\d+(?:-\d+)+$', vid):
        return vid
    return re.sub(r'(-\d+)+$', '', vid)


def _clean_text(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r'<.*?>', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _extract_detail_meta(h):
    meta = {
        "vod_name": "",
        "vod_pic": "",
        "vod_content": "",
        "vod_year": "",
        "vod_area": "",
        "vod_actor": "",
        "vod_director": "",
        "vod_remarks": ""
    }

    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S | re.I)
    if title_match:
        meta["vod_name"] = _clean_text(title_match.group(1))[:60]

    img_match = re.search(r'<div[^>]*class=["\'][^"\']*image-containe[^"\']*["\'][^>]*>\s*<img[^>]+src=["\']([^"\']+)["\']', h, re.S | re.I)
    if img_match:
        meta["vod_pic"] = _abs(img_match.group(1))
    if not meta["vod_pic"]:
        pm = re.search(r'data-src="([^"]+)"', h)
        if pm:
            meta["vod_pic"] = _abs(pm.group(1))

    content_block = re.search(r'<div[^>]*class=["\'][^"\']*content1[^"\']*["\'][^>]*>(.*?)</div>', h, re.S | re.I)
    if content_block:
        text = _clean_text(content_block.group(1))
        if text:
            meta["vod_content"] = text
            if not meta["vod_name"]:
                meta["vod_name"] = text[:60]

    if not meta["vod_content"]:
        for pat in [
            r'<p[^>]*>(.*?)</p>',
            r'<div[^>]*class=["\'][^"\']*content2[^"\']*["\'][^>]*>(.*?)</div>'
        ]:
            mm = re.search(pat, h, re.S | re.I)
            if mm:
                text = _clean_text(mm.group(1))
                if text:
                    meta["vod_content"] = text
                    break

    for label, key in [
        ('年份', 'vod_year'),
        ('地区', 'vod_area'),
        ('主演', 'vod_actor'),
        ('导演', 'vod_director'),
        ('备注', 'vod_remarks'),
    ]:
        m = re.search(rf'{label}[:：\s]*([^<\n]+)', h, re.I)
        if m:
            meta[key] = _clean_text(m.group(1))[:60]

    if not meta["vod_remarks"]:
        m = re.search(r'更新时间[:：\s]*([^<\n]+)', h, re.I)
        if m:
            meta["vod_remarks"] = _clean_text(m.group(1))[:60]

    if not meta["vod_year"]:
        m = re.search(r'(?:年份|year)[:：\s]*([0-9]{4})', h, re.I)
        if m:
            meta["vod_year"] = m.group(1)

    return meta


async def home(params, context):
    try:
        h = _decode(_get(HOST + "/"))
        cats = []
        seen = set()
        for u, cid, n in re.findall(r'href="(/list/\?(\d+)\.html)"[^>]*>([^<]{1,12})</a>', h):
            name = n.strip()
            if cid in seen or not name or "更多" in name:
                continue
            seen.add(cid)
            cats.append({"type_id": cid, "type_name": html.unescape(name)})
        return {"class": cats, "list": []}
    except Exception:
        return {"class": [], "list": []}


async def category(params, context):
    try:
        tid = params.get("categoryId") or ""
        pg = int(params.get("page") or 1)
        url = f"{HOST}/list/?{tid}.html"
        if pg > 1:
            url = f"{HOST}/list/?{tid}-{pg}.html"
        h = _decode(_get(url))
        lst = _cards(h)
        return {"page": pg, "pagecount": 9999, "total": 0, "list": lst}
    except Exception:
        return {"page": 1, "pagecount": 1, "total": 0, "list": []}


async def detail(params, context):
    try:
        raw_vid = str(params.get("videoId") or "").strip()
        if not raw_vid:
            return {"list": []}

        base_vid = _normalize_video_id(raw_vid) or raw_vid
        candidate_vids = []
        seen = set()
        for vid in [raw_vid, base_vid, f"{base_vid}-0-0", f"{base_vid}-0", f"{base_vid}-1-0"]:
            if vid and vid not in seen:
                candidate_vids.append(vid)
                seen.add(vid)

        final_url = ""
        final_vid = raw_vid
        for vid in candidate_vids:
            for route in [
                f"{HOST}/video/?{vid}.html",
                f"{HOST}/detail/?{vid}.html",
            ]:
                h = _get(route)
                if not h:
                    continue
                if re.search(r'<h1[^>]*>', h, re.I) or 'data-user-name' in h or 'MacPlayer' in h or 'DPlayer' in h:
                    final_url = route
                    final_vid = vid
                    break
            if final_url:
                break

        if not final_url:
            final_url = f"{HOST}/video/?{base_vid}-0-0.html"
            final_vid = f"{base_vid}-0-0"

        h = _get(final_url)
        t = re.search(r"<h1[^>]*>([^<]+)</h1>", h, re.S)
        name = html.unescape((t.group(1).strip() if t else "")).strip()[:60] if t else ""

        pic = ""
        m_img = re.search(r'<div[^>]*class=["\'][^"\']*image-containe[^"\']*["\'][^>]*>\s*<img[^>]+src=["\']([^"\']+)["\']', h, re.S | re.I)
        if m_img:
            pic = _abs(m_img.group(1))
        if not pic:
            pm = re.search(r'data-src="([^"]+)"', h)
            pic = _abs(pm.group(1)) if pm else ""

        content = name or ""
        if not content:
            mc = re.search(r'<div[^>]*class=["\'][^"\']*content1[^"\']*["\'][^>]*>.*?<h1[^>]*>(.*?)</h1>', h, re.S | re.I)
            if mc:
                content = html.unescape(re.sub(r'<.*?>', '', mc.group(1))).strip()

        vod = {
            "vod_id": final_vid,
            "vod_name": name or "少女破处",
            "vod_pic": pic,
            "vod_content": content,
            "vod_play_sources": [{
                "name": "少女破处",
                "episodes": [{"name": "正片", "playId": final_url}]
            }]
        }
        return {"list": [vod]}
    except Exception:
        return {"list": []}


async def search(params, context):
    try:
        key = (params.get("keyword") or params.get("wd") or "").strip()
        if not key:
            return {"page": 1, "pagecount": 0, "total": 0, "list": []}

        url = f"{HOST}/search.php?searchword={quote(key, safe='')}"
        h = _decode(_get(url))
        lst = _cards(h)
        return {"page": 1, "pagecount": 1, "total": len(lst), "list": lst}
    except Exception:
        return {"page": 1, "pagecount": 0, "total": 0, "list": []}


async def play(params, context):
    play_id = params.get("playId")
    if not play_id:
        raise ValueError("playId 不能为空")

    h = _get(play_id)
    url = _extract_play_url(h)

    if url:
        if url.startswith("/"):
            url = _abs(url)
        return {
            "urls": [{"name": "播放", "url": url}],
            "flag": "play",
            "header": {"User-Agent": "Mozilla/5.0", "Referer": play_id},
            "parse": 0,
        }

    return {
        "urls": [{"name": "播放", "url": play_id}],
        "flag": "play",
        "header": {"User-Agent": "Mozilla/5.0", "Referer": play_id},
        "parse": 1,
    }


def isVideoFormat(url):
    u = (url or "").split("?")[0].lower()
    return u.endswith(".m3u8") or u.endswith(".mp4")


if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play
    })
