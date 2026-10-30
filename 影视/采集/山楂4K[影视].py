# -*- coding: utf-8 -*-
# @name 山楂4K
# @version 1.0.0

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import uuid

try:
    import requests
except Exception:
    requests = None

try:
    from spider_runner import OmniBox, run
except Exception:
    OmniBox = None
    run = None

BASE_URL = "http://43.248.128.122:578"
USERNAME = "sukeke"
PASSWORD = "sukeke.1"
DEVICE_ID = "de94cd65-a825-4972-adf9-7dbece13e9f1"
USER_AGENT = "Mozilla/5.0 (Linux; Android 12) okhttp/3.12.1"
KNOWN_TYPES = [
    (1, "电影"), (2, "连续剧"), (3, "综艺"), (4, "动漫"),
    (20, "短剧"), (21, "少儿"), (22, "漫剧"), (23, "纪录片"),
]

_SESSION = {
    "jwt": "",
    "session_id": "",
    "sign_key": "",
    "device_id": DEVICE_ID,
}

_INIT_FILLER = {
    "sign": "s", "signature": "s", "app_id": "1", "app_key": "1",
    "app_version": "1.0", "version": "1", "platform": "android",
    "device": "android", "version_code": 1, "uid": "1",
    "source_id": "1", "site_id": "1", "type": "1",
}


def _http_json(method, path, params=None, payload=None, timeout=30):
    url = path if str(path).startswith("http") else BASE_URL + path
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    if _SESSION["jwt"]:
        headers["Authorization"] = "Bearer " + _SESSION["jwt"]
    if _SESSION["session_id"]:
        headers["X-Session-Id"] = _SESSION["session_id"]

    session = requests if requests is not None else None
    try:
        if session is not None:
            if method == "GET":
                r = session.get(url, params=params, headers=headers, timeout=timeout)
            else:
                r = session.post(url, params=params, json=payload, headers=headers, timeout=timeout)
            return r.json() if hasattr(r, "json") else json.loads(r.text)
        req = urllib.request.Request(url, data=None, headers=headers, method=method)
        if params:
            q = urllib.parse.urlencode(params)
            req.full_url = url + ("?" + q if "?" not in url else "&" + q)
        if method == "POST" and payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return json.loads(body)
    except Exception as exc:
        return {"code": 0, "msg": "请求失败: %s" % exc}


def _get_text(url, timeout=30, retry=2):
    headers = {"User-Agent": USER_AGENT, "Referer": "https://www.google.com/"}
    last_error = ""
    for i in range(max(1, retry)):
        try:
            if requests is not None:
                r = requests.get(url, headers=headers, timeout=timeout)
                return r.status_code, r.text
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.getcode(), resp.read().decode("utf-8", "replace")
        except Exception as exc:
            last_error = str(exc)
            if i < retry - 1:
                time.sleep(1.2)
    return 0, last_error


def _sign_headers(path, body=""):
    if not _SESSION["sign_key"]:
        return {}
    try:
        key = bytes.fromhex(_SESSION["sign_key"])
    except Exception:
        return {}
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    msg = (ts + nonce + path + (body or "")).encode("utf-8")
    sg = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return {
        "X-Timestamp": ts,
        "X-Nonce": nonce,
        "X-Sign": sg,
        "X-Device-Sign": sg,
        "X-Device-Id": _SESSION["device_id"],
    }


async def _login():
    r = _http_json(
        "POST",
        "/api/v1/user/login",
        payload={
            "Username": USERNAME,
            "Password": PASSWORD,
            "device_id": _SESSION["device_id"],
        },
    )
    if r.get("code") == 1 and isinstance(r.get("data"), dict):
        token = r["data"].get("token")
        if token:
            _SESSION["jwt"] = token
            return True
    return False


async def _handshake():
    challenge = _http_json("GET", "/api/v1/security/challenge")
    if challenge.get("code") != 1 or not isinstance(challenge.get("data"), dict):
        return False
    challenge_val = challenge["data"].get("challenge")
    challenge_id = challenge["data"].get("challenge_id")
    if not challenge_val or not challenge_id:
        return False
    payload = {
        "challenge": challenge_val,
        "challenge_id": challenge_id,
        "device_id": _SESSION["device_id"],
        "token": _SESSION["jwt"],
        "client_token": "",
        "timestamp": int(time.time()),
        "nonce": uuid.uuid4().hex,
        "username": USERNAME,
        "password": PASSWORD,
    }
    payload.update(_INIT_FILLER)
    r = _http_json("POST", "/api/v1/security/init", payload=payload)
    if r.get("code") == 1 and isinstance(r.get("data"), dict):
        _SESSION["session_id"] = r["data"].get("session_id") or ""
        _SESSION["sign_key"] = r["data"].get("sign_key") or ""
        return bool(_SESSION["session_id"])
    return False


async def _ensure_session():
    if not _SESSION["jwt"] and not await _login():
        return False
    if not _SESSION["session_id"] and not await _handshake():
        return False
    return True


def _search_api(wd, page=1, type_id=None):
    params = {"wd": wd, "page": page}
    if type_id:
        params["type"] = type_id
    delays = [0, 2.5, 5, 9, 15]
    last = {"code": 0}
    for i, d in enumerate(delays):
        if d:
            time.sleep(d)
        last = _http_json("GET", "/api/v1/search", params=params)
        if last.get("code") == 1:
            return last
        msg = str(last.get("msg") or "")
        if "频繁" not in msg and "rate" not in msg.lower():
            return last
    return last


def _item_to_vod(item):
    return {
        "vod_id": str(item.get("vod_id") or item.get("id") or ""),
        "vod_name": str(item.get("vod_name") or item.get("name") or ""),
        "vod_pic": str(item.get("vod_pic") or item.get("pic") or ""),
        "vod_remarks": str(item.get("vod_remarks") or item.get("remarks") or ""),
        "vod_year": str(item.get("vod_year") or ""),
        "vod_area": str(item.get("vod_area") or ""),
        "vod_class": str(item.get("vod_class") or item.get("type_name") or ""),
        "vod_actor": str(item.get("vod_actor") or ""),
        "vod_director": str(item.get("vod_director") or ""),
        "vod_content": str(item.get("vod_blurb") or item.get("vod_content") or ""),
        "type_id": str(item.get("type_id") or ""),
        "type_name": str(item.get("type_name") or ""),
        "vod_douban_score": str(item.get("vod_douban_score") or ""),
    }


def _decode_ticket(ticket):
    try:
        seg = ticket.split(".")[0]
        seg += "=" * (-len(seg) % 4)
        return json.loads(base64.urlsafe_b64decode(seg).decode("utf-8", "replace"))
    except Exception:
        return None


def _ticket_for(tk):
    r = _http_json(
        "POST",
        "/api/v1/vod/ticket",
        payload={"token": tk},
        timeout=30,
    )
    if r.get("code") == 1 and isinstance(r.get("data"), dict):
        return r["data"].get("ticket")
    return None


def _resolve_ticket(tk):
    ticket = _ticket_for(tk)
    if not ticket:
        return None, "换票失败"
    pl = _decode_ticket(ticket)
    if not pl:
        return None, "票据解析失败"
    d = pl.get("data") or {}
    api = str(d.get("parse_api") or "").replace("\\u00026", "&")
    du = str(d.get("url") or "")
    if not api or not du:
        return None, "无解析配置"

    if api.startswith("/"):
        full = BASE_URL + api + urllib.parse.quote(du, safe="")
        code, text = _get_text(full)
        try:
            j = json.loads(text) if text.strip().startswith("{") else None
        except Exception:
            j = None
        if isinstance(j, dict):
            if j.get("url"):
                return j["url"], ""
            msg = str(j.get("system") or j.get("msg") or "解析失败")
            return None, msg
        if code == 200 and text.startswith("http"):
            return text.strip(), ""
        return None, "解析失败(%s)" % code

    if "{md5}" in api:
        target = api.replace("{md5}", du)
    elif "url=" in api:
        target = api + urllib.parse.quote(du, safe="")
    else:
        target = api + du
    code, text = _get_text(target)
    try:
        j = json.loads(text) if text.strip().startswith("{") else None
    except Exception:
        j = None
    if isinstance(j, dict):
        if j.get("url"):
            return j["url"], ""
        return None, str(j.get("msg") or "外部解析失败")
    if code == 200 and text.startswith("http"):
        return text.strip(), ""
    return None, "外部解析失败(%s)" % code


async def home(params, context):
    await _ensure_session()
    classes = [{"type_id": str(t), "type_name": n} for t, n in KNOWN_TYPES]
    return {"class": classes, "list": []}


async def category(params, context):
    await _ensure_session()
    if not isinstance(params, dict):
        params = {}
    tid = str(params.get("categoryId") or params.get("typeId") or params.get("tid") or "1")
    page = int(params.get("page") or 1)
    r = _search_api("*", page=page, type_id=tid)
    if r.get("code") != 1:
        return {"page": page, "pagecount": 0, "total": 0, "list": []}
    data = r.get("data") or {}
    hits = data.get("hits") or []
    total = int(data.get("total") or 0)
    pages = int(data.get("total_pages") or 1)
    return {
        "page": page,
        "pagecount": pages,
        "total": total,
        "list": [_item_to_vod(item) for item in hits],
    }


async def detail(params, context):
    await _ensure_session()
    if not isinstance(params, dict):
        params = {}
    video_id = params.get("videoId") or params.get("vodId") or params.get("id")
    if not video_id:
        return {"list": []}
    if isinstance(video_id, (list, tuple)):
        video_id = video_id[0]
    r = _http_json("GET", "/api/v1/video/detail", params={"id": str(video_id)}, timeout=30)
    if r.get("code") != 1 or not isinstance(r.get("data"), dict):
        return {"list": []}
    vi = r["data"].get("vod_info") or {}
    sources = []
    for line in vi.get("vod_url_with_player") or []:
        name = str(line.get("name") or "线路")
        episodes = []
        raw = str(line.get("url") or "")
        for seg in raw.split("#"):
            if not seg:
                continue
            if "$" in seg:
                ep_name, tail = seg.split("$", 1)
                ep_name = (ep_name or "").strip() or ("第%d集" % (len(episodes) + 1))
                play_id = str(line.get("code") or "") + "|" + str(tail or "")
            else:
                ep_name = "第%d集" % (len(episodes) + 1)
                play_id = str(line.get("code") or "") + "|" + str(seg or "")
            if play_id:
                episodes.append({"name": ep_name, "playId": play_id})
        if episodes:
            sources.append({"name": name, "episodes": episodes})

    entry = {
        "vod_id": str(vi.get("vod_id") or video_id),
        "vod_name": str(vi.get("vod_name") or ""),
        "vod_pic": str(vi.get("vod_pic") or ""),
        "vod_content": str(vi.get("vod_content") or vi.get("vod_blurb") or ""),
        "vod_year": str(vi.get("vod_year") or ""),
        "vod_remarks": str(vi.get("vod_remarks") or ""),
        "vod_actor": str(vi.get("vod_actor") or ""),
        "vod_director": str(vi.get("vod_director") or ""),
        "vod_area": str(vi.get("vod_area") or ""),
        "vod_lang": str(vi.get("vod_lang") or ""),
        "vod_class": str(vi.get("vod_class") or ""),
        "vod_play_sources": sources or [{"name": "线路1", "episodes": [{"name": "播放", "playId": str(video_id)}]}],
    }
    return {"list": [entry]}


async def search(params, context):
    await _ensure_session()
    if not isinstance(params, dict):
        params = {}
    keyword = str(params.get("keyword") or params.get("wd") or "").strip()
    page = int(params.get("page") or 1)
    if not keyword:
        return {"page": page, "pagecount": 0, "total": 0, "list": []}
    r = _search_api(keyword, page=page)
    if r.get("code") != 1:
        return {"page": page, "pagecount": 0, "total": 0, "list": []}
    data = r.get("data") or {}
    hits = data.get("hits") or []
    total = int(data.get("total") or 0)
    pages = int(data.get("total_pages") or 1)
    return {
        "page": page,
        "pagecount": pages,
        "total": total,
        "list": [_item_to_vod(item) for item in hits],
    }


async def play(params, context):
    await _ensure_session()
    if params is None:
        params = {}
    if not isinstance(params, dict):
        params = {"playId": params}
    play_id = params.get("playId") or params.get("play_id") or params.get("id") or params.get("url") or params.get("playUrl")
    if not play_id:
        raise ValueError("playId 不能为空")
    flag = params.get("flag") or params.get("type") or "play"
    code, tk = "", str(play_id)
    if "|" in str(play_id):
        code, tk = str(play_id).split("|", 1)
    url, err = _resolve_ticket(tk)
    if not url:
        return {"urls": [{"name": "播放", "url": ""}], "flag": flag, "header": {}, "parse": 0, "msg": err or "播放失败"}
    return {
        "urls": [{"name": "播放", "url": url}],
        "flag": flag,
        "header": {"User-Agent": USER_AGENT, "Referer": "https://www.google.com/"},
        "parse": 0,
    }


def _ensure_runtime_dependencies():
    import importlib.util
    import subprocess
    import sys

    required = ["requests"]
    missing = []
    for name in required:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append(name)
        except Exception:
            missing.append(name)

    if missing:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *missing],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


_ensure_runtime_dependencies()

if __name__ == "__main__":
    if run is not None:
        run({
            "home": home,
            "category": category,
            "detail": detail,
            "search": search,
            "play": play,
        })
