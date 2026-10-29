# -*- coding: utf-8 -*-
# 影探4K：由 影探4k.js 移植到鱼壳 webhtv 站点注入使用的 Python Spider。
# 用法：把本文件放到手机 /sdcard/py/影探4K.py，站点配置 api 填 file:///sdcard/py/影探4K.py
import base64
import json
import re
import time
import urllib.parse

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

try:
    from base.spider import Spider as _BaseSpider
except Exception:
    try:
        import sys
        sys.path.append('..')
        from base.spider import Spider as _BaseSpider
    except Exception:
        class _BaseSpider:
            pass

KEY = 'yingtan4k'
HOST = 'http://cms.lyyytv.cn'
CMS_KEY = 'wP5bvxoc3yv7FoBQENFZuAF0EUYr4LTy'

# 解析接口（对齐 yt4k.js：fys.lyyytv.cn / parsesId=3）
PARSE_API = 'http://fys.lyyytv.cn/api/index?parsesId=3&appid=10001&videoUrl='
HEADERS = {'User-Agent': 'okhttp/4.12.0'}
# 解析请求/回源头：对齐 JS 的 PH，避免 gzip 花屏
PARSE_HEADERS = {'User-Agent': 'okhttp/4.12.0', 'Accept-Encoding': 'identity'}

# baidu.con 前缀加密常量（对齐 yt4k.js）
DEC_PREFIX = 'https://baidu.con/'
# 解析重试轮数与退避基数（秒）
PARSE_ROUNDS = 3
PARSE_BACKOFF = 0.35
# 同一原始地址解析结果缓存窗口（秒）
PLAY_CACHE_TTL = 120

PAGE_LIMIT = 20
FILTER_NAMES = {
    'class': '类型', 'area': '地区', 'lang': '语言', 'year': '年份',
    'letter': '字母', 'by': '排序', 'sort': '顺序',
}
HOME_CACHE_TTL = 6 * 3600

_BASE64_RE = re.compile(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')
_LDMAX_RE = re.compile(r'^https?://ldmax\.cooom/', re.I)
_MEDIA_RE = re.compile(r'\.(?:mp4|m3u8?|flv|avi|mkv|ts|mov|wmv|webm|m4v|mpd)$', re.I)

_home_cache = {}
_play_cache = {}


def text(value):
    return '' if value is None else str(value).strip()


def page_of(value):
    m = re.match(r'\s*[+-]?\d+', '' if value is None else str(value))
    n = int(m.group(0)) if m else 0
    return max(1, n) if n else 1


def list_of(value):
    return value if isinstance(value, list) else []


def object_of(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def get_json(url, headers=None, timeout=15):
    headers = HEADERS if headers is None else headers
    rsp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    try:
        data = object_of(rsp.json())
    except Exception:
        data = {}
    if not data:
        raise Exception('影探4K：接口未返回有效 JSON')
    return data


def cms(path, params=None):
    params = params or {}
    query = urllib.parse.urlencode(params)
    data = get_json('%s/api.php/app/%s?%s' % (HOST, path, query))
    code = data.get('code')
    if code is not None:
        try:
            ok = int(code) in (1, 200)
        except (TypeError, ValueError):
            ok = False
        if not ok:
            raise Exception('影探4K：CMS 请求失败')
    return data


def decode_base64(value):
    clean = re.sub(r'\s+', '', text(value))
    if not clean or not _BASE64_RE.fullmatch(clean):
        return None
    try:
        return base64.b64decode(clean)
    except Exception:
        return None


def decrypt_lvdou(value):
    """对齐 JS decUrlOne：lvdou+ → 前16 key/后16 iv AES/CBC/PKCS7"""
    original = text(value)
    if not original.startswith('lvdou+'):
        return original
    if not CMS_KEY:
        return original
    try:
        encrypted = decode_base64(original[6:])
        if not encrypted:
            return original
        key = CMS_KEY[:16].encode('utf-8')
        iv = CMS_KEY[16:32].encode('utf-8') if len(CMS_KEY) >= 32 else key
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plain = unpad(cipher.decrypt(encrypted), AES.block_size)
        result = plain.decode('utf-8', errors='replace').strip()
        if result.startswith('http'):
            return result
    except Exception:
        pass
    return original


def is_http_url(value):
    try:
        parsed = urllib.parse.urlparse(text(value))
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


def is_site_url(value):
    if not is_http_url(value):
        return False
    host = (urllib.parse.urlparse(text(value)).hostname or '').lower()
    return host == 'lyyytv.cn' or host.endswith('.lyyytv.cn')


def is_ldmax_url(value):
    return bool(_LDMAX_RE.match(text(value)))


def decrypt_ldmax(value, depth=0):
    """兼容老加密：ldmax.cooom 前缀"""
    if depth > 5:
        return ''
    url = text(value)
    decoded = decode_base64(url)
    if decoded:
        url = re.sub(r'\s+', '', decoded.decode('utf-8', errors='replace'))
    if not is_ldmax_url(url):
        return url
    path = _LDMAX_RE.sub('', url)
    if len(path) <= 16:
        return ''
    try:
        key = path[:16][::-1].encode('utf-8')
        encrypted = decode_base64(path[16:])
        if not encrypted or len(encrypted) % 16:
            return ''
        cipher = AES.new(key, AES.MODE_CBC, key)
        plain = bytearray(cipher.decrypt(encrypted))
        pad = plain[-1]
        if 0 < pad <= 16:
            del plain[-pad:]
        result = bytes(plain).decode('utf-8', errors='replace').strip()
        return decrypt_ldmax(result, depth + 1) if is_ldmax_url(result) else result
    except Exception:
        return ''


def find_url(value):
    """对齐 JS findUrl：从解析响应 JSON 中挑出 url/playUrl/link/data.url"""
    if not isinstance(value, dict):
        return ''
    for key in ('url', 'playUrl', 'link'):
        v = value.get(key)
        if v:
            return text(v)
    return find_url(value.get('data'))


def resolve_parse(body):
    """
    对齐 JS resolveParse：
      1) JSON 包裹 → 取出 url
      2) https://baidu.con/ 前缀 → 前16位 key=iv，余下 base64 密文 AES/CBC/PKCS7
      3) 明文 URL
    """
    body = text(body)
    if not body:
        return ''

    candidate = body
    if body.startswith('{'):
        try:
            parsed = json.loads(body)
            found = find_url(parsed)
            if found:
                candidate = found
        except Exception:
            pass

    if candidate.startswith(DEC_PREFIX):
        rest = candidate[len(DEC_PREFIX):]
        if len(rest) <= 16:
            return ''
        key = rest[:16].encode('utf-8')
        cipher_b64 = rest[16:]
        # 优先按 base64 密文解密
        try:
            encrypted = base64.b64decode(cipher_b64, validate=False)
            cipher = AES.new(key, AES.MODE_CBC, key)
            plain = unpad(cipher.decrypt(encrypted), AES.block_size)
            result = plain.decode('utf-8', errors='replace').strip()
            if result.startswith('http'):
                return result
        except Exception:
            pass
        # 兜底：密文本身是 raw bytes
        try:
            raw = cipher_b64.encode('latin-1', errors='ignore')
            if raw and len(raw) % 16 == 0:
                cipher = AES.new(key, AES.MODE_CBC, key)
                plain = unpad(cipher.decrypt(raw), AES.block_size)
                result = plain.decode('utf-8', errors='replace').strip()
                if result.startswith('http'):
                    return result
        except Exception:
            pass
        return ''

    return candidate


def parse_url(raw):
    """对齐 JS play 内部：把原始地址拼到解析基址后请求，解出真实 URL。"""
    if not raw:
        return ''
    target = PARSE_API + urllib.parse.quote(raw, safe="!'()*")
    for rnd in range(PARSE_ROUNDS):
        if rnd > 0:
            time.sleep(rnd * PARSE_BACKOFF)
        try:
            rsp = requests.get(target, headers=PARSE_HEADERS, timeout=30)
            if rsp.status_code == 200 and rsp.text:
                resolved = resolve_parse(rsp.text)
                if resolved and resolved.startswith('http'):
                    return resolved
        except Exception:
            pass
    return ''


def is_media_url(url):
    if not is_http_url(url):
        return False
    return bool(_MEDIA_RE.search(urllib.parse.urlparse(text(url)).path))


def home(extend=''):
    cache_key = '%s_home_%s' % (KEY, text(extend))
    cached = _home_cache.get(cache_key)
    if cached and cached[0] > time.time():
        return cached[1]
    data = cms('nav', {'token': ''})
    classes = []
    filters = {}
    for item in list_of(data.get('list')):
        if not isinstance(item, dict):
            continue
        if item.get('type_id') is None or not text(item.get('type_name')):
            continue
        tid = text(item['type_id'])
        classes.append({'type_id': tid, 'type_name': text(item['type_name'])})
        ext = object_of(item.get('type_extend'))
        groups = []
        for key, name in FILTER_NAMES.items():
            values = [v for v in (text(x) for x in text(ext.get(key)).split(',')) if v]
            values = list(dict.fromkeys(values))
            if values:
                groups.append({
                    'key': key,
                    'name': name,
                    'init': '',
                    'value': [{'n': '全部', 'v': ''}] + [{'n': v, 'v': v} for v in values],
                })
        if groups:
            filters[tid] = groups
    result = {'class': classes}
    if classes:
        _home_cache[cache_key] = (time.time() + HOME_CACHE_TTL, result)
    return result


def home_vod():
    data = cms('index_video', {'token': ''})
    vlist = []
    for item in list_of(data.get('list')):
        if isinstance(item, dict):
            vlist.extend(list_of(item.get('vlist')))
    return {'list': vlist}


def paginated(data, requested_page):
    lst = list_of(data.get('list'))
    raw_page = data.get('page')
    page = page_of(raw_page if raw_page is not None else requested_page)
    try:
        limit = int(data.get('limit') or 0)
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0:
        limit = PAGE_LIMIT
    try:
        raw_pagecount = int(data.get('pagecount') or 0)
    except (TypeError, ValueError):
        raw_pagecount = 0
    has_pagecount = raw_pagecount > 0
    pagecount = raw_pagecount if has_pagecount else page + (1 if len(lst) >= limit else 0)
    try:
        raw_total = data.get('total')
        has_total = raw_total is not None and int(raw_total) >= 0
    except (TypeError, ValueError):
        has_total = False
    if has_pagecount and has_total:
        total = int(data.get('total'))
    else:
        total = (page - 1) * limit + len(lst) + (1 if pagecount > page else 0)
    data['page'] = page
    data['pagecount'] = pagecount
    data['limit'] = limit
    data['total'] = total
    data['list'] = lst
    return data


def category(tid, pg, extend):
    page = page_of(pg)
    tid = text(tid)
    if not tid:
        return paginated({'list': []}, page)
    extend = extend if isinstance(extend, dict) else {}
    params = {'tid': tid, 'pg': str(page), 'limit': '18'}
    for key in FILTER_NAMES:
        value = text(extend.get(key))
        if value and value != 'all':
            params[key] = value
    return paginated(cms('video', params), page)


def playlist(value):
    parts = []
    for entry in text(value).split('#'):
        sep = entry.find('$')
        if sep <= 0 or not text(entry[sep + 1:]):
            continue
        parts.append('%s$%s' % (text(entry[:sep]), decrypt_lvdou(entry[sep + 1:])))
    return '#'.join(parts)


def detail(ids):
    if not isinstance(ids, (list, tuple)):
        ids = [ids]
    lst = []
    for vid in ids:
        vid = text(vid)
        if not vid:
            continue
        data = cms('video_detail', {'id': vid}).get('data')
        if not isinstance(data, dict):
            continue
        players = data.get('vod_url_with_player')
        vod = {k: v for k, v in data.items() if k != 'vod_url_with_player'}
        names = text(vod.get('vod_play_from')).split('$$$')
        if isinstance(players, list):
            sources = players
        else:
            sources = [
                {'name': names[i] if i < len(names) else '', 'url': u}
                for i, u in enumerate(text(vod.get('vod_play_url')).split('$$$'))
            ]
        froms = []
        urls = []
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            url = playlist(source.get('url'))
            if not url:
                continue
            name = text(source.get('name')) or text(source.get('code')) or '线路%d' % (index + 1)
            froms.append(re.sub(r'[$#]', ' ', name))
            urls.append(url)
        vod['vod_play_from'] = '$$$'.join(froms)
        vod['vod_play_url'] = '$$$'.join(urls)
        lst.append(vod)
    return {'list': lst}


def search(key, pg):
    wd = text(key)
    page = page_of(pg)
    if not wd:
        return paginated({'list': []}, page)
    data = cms('search', {'text': wd, 'pg': str(page)})
    lst = []
    for item in list_of(data.get('list')):
        if isinstance(item, dict):
            lst.append({k: v for k, v in item.items() if k != 'type'})
    data['list'] = lst
    return paginated(data, page)


def play(play_id):
    """对齐 JS play：无条件走解析接口，解出真实地址再交播放器。"""
    original = decrypt_lvdou(play_id)
    if not original:
        return {'parse': 0, 'url': '', 'header': dict(PARSE_HEADERS)}

    # 兼容老加密：ldmax 前缀先本地解密
    if is_ldmax_url(original):
        decrypted = decrypt_ldmax(original)
        if decrypted:
            original = decrypted

    # 解析结果缓存
    now = time.time()
    cached = _play_cache.get(original)
    if cached and cached[0] > now:
        return {'parse': 0, 'url': cached[1], 'header': dict(PARSE_HEADERS)}

    resolved = parse_url(original)
    if resolved:
        _play_cache[original] = (now + PLAY_CACHE_TTL, resolved)

    return {'parse': 0, 'url': resolved or '', 'header': dict(PARSE_HEADERS)}


class Spider(_BaseSpider):
    def getName(self):
        return '🎬 影探4K'

    def init(self, extend=''):
        self.extend = extend or ''

    def isVideoFormat(self, url):
        return is_media_url(url)

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        return home(self.extend)

    def homeVideoContent(self):
        return home_vod()

    def categoryContent(self, tid, pg, filter, extend):
        return category(tid, pg, extend)

    def detailContent(self, ids):
        return detail(ids)

    def searchContent(self, key, quick, pg='1'):
        return search(key, pg)

    def playerContent(self, flag, id, vipFlags):
        return play(id)

    def localProxy(self, param):
        return None

    def destroy(self):
        pass
try:
    from spider_runner import OmniBox, run
except Exception:
    OmniBox = None
    run = None

# OmniBox compatibility layer.
orig_home = globals().get("home")
orig_category = globals().get("category")
orig_detail = globals().get("detail")
orig_search = globals().get("search")
orig_play = globals().get("play")


def _normalize_string_ids(value):
    string_key_names = {
        "type_id", "typeId", "vod_id", "vodId", "id", "video_id", "videoId",
        "categoryId", "vod_time", "vod_year", "vod_douban_score", "vod_remarks",
        "vod_name", "vod_pic", "vod_content", "vod_actor", "vod_director", "vod_area"
    }
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            new_key = key
            key_lower = str(key).lower()
            if item is None:
                result[new_key] = None
            elif isinstance(item, (dict, list)):
                result[new_key] = _normalize_string_ids(item)
            elif key_lower in {"page", "pagecount", "total", "limit"}:
                result[new_key] = item
            elif (
                new_key in string_key_names
                or "id" in key_lower
                or "time" in key_lower
                or "year" in key_lower
                or "score" in key_lower
                or "count" in key_lower
            ) and not isinstance(item, str):
                result[new_key] = str(item)
            else:
                result[new_key] = item
        return result
    if isinstance(value, list):
        return [_normalize_string_ids(item) for item in value]
    return value


def _omni_detail_payload(payload):
    if not isinstance(payload, dict):
        return {"list": []}
    items = payload.get("list") or []
    if not isinstance(items, list):
        items = [payload]
    result_list = []
    for item in items:
        if not isinstance(item, dict):
            continue
        detail = dict(item)
        detail["vod_id"] = str(detail.get("vod_id") or detail.get("id") or "")
        if "vod_play_sources" not in detail:
            play_from = str(detail.get("vod_play_from") or "")
            play_url = str(detail.get("vod_play_url") or "")
            sources = []
            if play_from or play_url:
                froms = [x for x in play_from.split("$$$") if x]
                urls = [x for x in play_url.split("$$$") if x]
                if not froms:
                    froms = ["线路%d" % (i + 1) for i in range(max(1, len(urls)))]
                for idx, line_name in enumerate(froms):
                    raw_url = urls[idx] if idx < len(urls) else ""
                    episodes = []
                    for part in str(raw_url).split("#"):
                        if not part:
                            continue
                        if "$" in part:
                            ep_name, ep_id = part.split("$", 1)
                            ep_name = ep_name.strip() or ("第%d集" % (len(episodes) + 1))
                            ep_id = ep_id.strip()
                            if ep_id:
                                episodes.append({"name": ep_name, "playId": ep_id})
                        else:
                            ep_id = part.strip()
                            if ep_id:
                                episodes.append({"name": "第%d集" % (len(episodes) + 1), "playId": ep_id})
                    if episodes:
                        sources.append({"name": line_name or ("线路%d" % (idx + 1)), "episodes": episodes})
            if sources:
                detail["vod_play_sources"] = sources
        result_list.append(detail)
    return {"list": result_list}


def _omni_play_payload(raw, flag):
    if not isinstance(raw, dict):
        return {"urls": [{"name": "播放", "url": str(raw)},], "flag": flag, "header": {}, "parse": 0}
    header = raw.get("header") if isinstance(raw.get("header"), dict) else {}
    url_value = raw.get("url") or raw.get("playUrl") or ""
    urls = raw.get("urls") if isinstance(raw.get("urls"), list) else []
    if not urls and url_value:
        urls = [{"name": "播放", "url": str(url_value)}]
    if not urls:
        for candidate in [raw.get("url"), raw.get("playUrl"), raw.get("m3u8")]:
            if candidate:
                urls = [{"name": "播放", "url": str(candidate)}]
                break
    return {"urls": urls if urls else [{"name": "播放", "url": ""}], "flag": raw.get("flag") or flag, "header": header, "parse": int(raw.get("parse") or 0)}


def _normalize_filter_labels(obj):
    if isinstance(obj, dict):
        obj.pop("filters", None)
        if "class" in obj:
            class_items = obj.get("class") or []
            if isinstance(class_items, list):
                obj["class"] = [
                    {
                        "type_id": str(item.get("type_id") or item.get("id") or ""),
                        "type_name": str(item.get("type_name") or item.get("name") or item.get("typeId") or "").strip(),
                    }
                    for item in class_items if isinstance(item, dict)
                ]
        for key, value in list(obj.items()):
            if key == "class":
                continue
            obj[key] = _normalize_filter_labels(value)
        return obj
    if isinstance(obj, list):
        return [_normalize_filter_labels(item) for item in obj]
    return obj


async def home(params, context):
    if params is None:
        params = {}
    if orig_home is not None:
        if isinstance(params, dict):
            extend = params.get("extend") or params.get("filters") or ""
            return _normalize_filter_labels(_normalize_string_ids(orig_home(extend)))
        return _normalize_filter_labels(_normalize_string_ids(orig_home(params or "")))
    return {"class": [], "list": []}


async def category(params, context):
    if params is None:
        params = {}
    if orig_category is not None:
        tid = str(params.get("categoryId") or params.get("typeId") or params.get("tid") or "1")
        page = params.get("page") or 1
        extend = params.get("filters") or params.get("extend") or {}
        return _normalize_string_ids(orig_category(tid, page, extend))
    return {"list": [], "page": 1, "pagecount": 1, "total": 0}


async def detail(params, context):
    if params is None:
        params = {}
    if orig_detail is not None:
        video_id = params.get("videoId") or params.get("vodId") or params.get("id")
        if video_id is None:
            return {"list": []}
        ids = [video_id] if not isinstance(video_id, (list, tuple)) else video_id
        payload = _normalize_string_ids(orig_detail(ids))
        return _omni_detail_payload(payload)
    return {"list": []}


async def search(params, context):
    if params is None:
        params = {}
    if orig_search is not None:
        keyword = params.get("keyword") or params.get("wd") or ""
        page = params.get("page") or "1"
        return _normalize_string_ids(orig_search(keyword, page))
    return {"page": 1, "pagecount": 0, "total": 0, "list": []}


async def play(params, context):
    if params is None:
        params = {}
    flag = params.get("flag") or "play"
    if orig_play is not None:
        play_id = params.get("playId") or params.get("play_id") or params.get("id")
        if play_id is None:
            raise ValueError("playId 不能为空")
        return _omni_play_payload(_normalize_string_ids(orig_play(play_id)), flag)
    raise ValueError("playId 不能为空")


if __name__ == "__main__":
    run({
        "home": home,
        "category": category,
        "detail": detail,
        "search": search,
        "play": play,
    })