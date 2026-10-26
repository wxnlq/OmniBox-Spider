# @name baoporn.com 站点适配版
# @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/爆色[瑟瑟].py
# @version 1.0.0
# @dependencies cheerio

const OmniBox = require("omnibox_sdk");
const cheerio = require("cheerio");
const runner = require("spider_runner");

module.exports = { home, category, detail, search, play };
runner.run(module.exports);

const SITE = "https://baoporn.com";
const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "zh-CN,zh;q=0.9",
  Referer: SITE,
};

const TAG_NAMES = [
  "国产", "日本", "欧美", "剧情", "平安夜", "酒店", "约炮", "美尻",
  "人妻", "美女", "麻豆传媒", "制服", "3P", "巨乳", "口爆", "极品",
  "中出", "推特", "多P", "海角", "无毛", "高颜值", "FansOne", "素人",
  "粉嫩", "私拍", "调教", "绿帽", "白虎", "露出", "裸体", "少妇", "网红",
  "女同", "御姐", "继母", "吞精", "双飞", "VIP", "OnlyFans", "Fansly", "乱伦",
];

const FIXED_TAGS = TAG_NAMES.map((name) => ({
  type_id: `/tag/${encodeURIComponent(name)}`,
  type_name: name,
}));

function cleanUrl(value) {
  const url = String(value || "").trim().replace(/^["']|["']$/g, "");
  if (!url) return "";
  if (url.startsWith("//")) return `https:${url}`;
  try {
    return new URL(url, `${SITE}/`).href;
  } catch {
    return "";
  }
}

function safeInt(value, fallback = 1) {
  const number = Number.parseInt(value, 10);
  return Number.isFinite(number) && number > 0 ? number : fallback;
}

function extractPic($, node) {
  const image = $(node).is("img") ? $(node) : $(node).find("img").first();
  const attrs = [
    "src", "data-src", "data-original", "data-lazy-src", "data-thumb",
    "data-pic", "data-cover", "data-img", "z-image-loader-url", "srcset",
  ];

  for (const attr of attrs) {
    let value = (image.attr(attr) || "").trim();
    if (value) {
      if (attr === "srcset") value = value.split(",")[0].trim().split(/\s+/)[0];
      return cleanUrl(value);
    }
  }

  const style = $(node).attr("style") || image.attr("style") || "";
  const match = style.match(/url\(\s*["']?([^)'"]+)["']?\s*\)/i);
  return match ? cleanUrl(match[1]) : "";
}

function cleanTitle(value) {
  return String(value || "")
    .replace(/[\u00a0\t\r\n]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\s+\d{1,2}:\d{2}\s*(?:\[[^\]]+\])?$/, "")
    .replace(/\s+(?:\[[^\]]+\]|#[^\s]+|[\uf000-\uffff]+)$/, "")
    .trim()
    .replace(/^[-_|\/ "'"]+|[-_|\/ "'"]+$/g, "");
}

function pickTitle($, anchor) {
  const card = $(anchor).closest(
    "article, .post, .video-item, .post-card, li, section",
  );
  const root = card.length ? card : $(anchor);
  const candidates = [
    $(anchor).attr("title"),
    root.find("img").first().attr("alt"),
    $(anchor).find("a").eq(1).text(),
    root.find("h1, h2, h3, .title, .entry-title, .post-card-title, .video-title, p")
      .first().text(),
    $(anchor).text(),
  ];

  for (const candidate of candidates) {
    const title = cleanTitle(candidate);
    if (title && !title.startsWith("#") && !/^\d{1,2}:\d{2}$/.test(title)) {
      return title;
    }
  }
  return "";
}

function iterVideoNodes($) {
  const selectors = [
    "section a[href*='/video/']", "section a[href*='/movie/']", "section a[href*='/detail/']",
    "main a[href*='/video/']", "main a[href*='/movie/']", "main a[href*='/detail/']",
    "article a[href*='/video/']", "article a[href*='/movie/']", "article a[href*='/detail/']",
    "a[href*='/video/']", "a[href*='/movie/']", "a[href*='/detail/']",
  ].join(", ");
  const seen = new Set();
  const nodes = [];

  $(selectors).each((_, anchor) => {
    const href = ($(anchor).attr("href") || "").trim();
    const lower = href.toLowerCase();
    if (
      !href ||
      ["/tag/", "/category/", "/search/", "/author/", "/page/"].some((part) => lower.includes(part)) ||
      href.startsWith("#") ||
      ($(anchor).text() || "").trim().startsWith("#") ||
      seen.has(href)
    ) {
      return;
    }
    seen.add(href);
    nodes.push(anchor);
  });
  return nodes;
}

function mapVod($, anchor) {
  const href = ($(anchor).attr("href") || "").trim();
  const lower = href.toLowerCase();
  if (
    !href ||
    ["/tag/", "/category/", "/search/", "/author/", "/page/"].some((part) => lower.includes(part)) ||
    !["/video/", "/movie/", "/detail/"].some((part) => lower.includes(part))
  ) {
    return null;
  }

  const title = pickTitle($, anchor);
  const pic = extractPic($, anchor);
  if (!title || !pic) return null;

  const card = $(anchor).closest("article, .post, .video-item, .post-card, li, section");
  const root = card.length ? card : $(anchor);
  const remarks = root.find("time, .duration, .time").first().text().trim();
  return {
    vod_id: cleanUrl(href),
    vod_name: title,
    vod_pic: pic,
    type_id: "",
    type_name: "",
    vod_remarks: remarks,
    vod_year: "",
    vod_douban_score: "",
  };
}

async function requestHtml(url, redirects = 0) {
  if (!url) throw new Error("请求地址为空");
  if (redirects > 5) throw new Error("重定向次数过多");

  const response = await OmniBox.request(url, {
    method: "GET",
    headers: HEADERS,
  });
  const status = Number(response.statusCode || response.status || 0);
  const responseHeaders = response.headers || {};
  const location = responseHeaders.Location || responseHeaders.location;

  if (status >= 300 && status < 400 && location) {
    return requestHtml(cleanUrl(location), redirects + 1);
  }
  if (status && (status < 200 || status >= 300)) {
    throw new Error(`HTTP ${status}`);
  }
  return Buffer.isBuffer(response.body)
    ? response.body.toString("utf8")
    : String(response.body || "");
}

function parseList(html) {
  const $ = cheerio.load(html || "");
  const list = [];
  for (const node of iterVideoNodes($)) {
    const item = mapVod($, node);
    if (item) list.push(item);
  }
  const unique = new Map(list.map((item) => [item.vod_id, item]));
  return [...unique.values()];
}

async function logError(entry, error) {
  await OmniBox.log("error", `[${entry}] 失败: ${error.message || error}`);
}

async function home(params, context) {
  try {
    await OmniBox.log("info", "[home] 加载首页");
    const html = await requestHtml(SITE);
    return { class: FIXED_TAGS, list: parseList(html) };
  } catch (error) {
    await logError("home", error);
    return { class: FIXED_TAGS, list: [] };
  }
}

async function category(params, context) {
  const categoryId = String(params.categoryId || "");
  const page = safeInt(params.page, 1);
  try {
    let base = categoryId ? cleanUrl(categoryId) : SITE;
    if (!base.startsWith(SITE)) throw new Error("分类地址无效");
    base = base.replace(/\/+$/, "");
    const url = page > 1 ? `${base}/page/${page}/` : base;
    const list = parseList(await requestHtml(url));
    return { page, pagecount: 9999, total: 999999, list };
  } catch (error) {
    await logError("category", error);
    return { page, pagecount: 0, total: 0, list: [] };
  }
}

function decodePlayerUrl(value) {
  const encoded = String(value || "").trim();
  if (!encoded) return "";
  try {
    const decoded = Buffer.from(encoded.split("").reverse().join(""), "base64").toString("utf8");
    if (/^https?:\/\//i.test(decoded)) return decoded;
  } catch {
    // The player may expose an unencoded URL.
  }
  return encoded;
}

async function detail(params, context) {
  const videoId = params.videoId;
  if (!videoId) return { list: [] };

  try {
    const url = cleanUrl(videoId);
    const html = await requestHtml(url);
    const $ = cheerio.load(html || "");
    const title = $("h1").first().text().trim() || $("title").first().text().trim() || "未命名视频";
    const player = $("#artplayer");
    const poster = player.attr("data-poster") || "";
    const pic = cleanUrl(poster) || extractPic($, $("img").first());
    const episodes = [];
    const playerUrl = player.attr("data-url") || "";

    if (playerUrl) {
      const decoded = decodePlayerUrl(playerUrl);
      if (decoded) episodes.push({ name: "默认线路", playId: decoded });
    }

    $("video source, source, iframe").each((_, element) => {
      const href = $(element).attr("src") || $(element).attr("data-src") || "";
      if (!href) return;
      const decoded = decodePlayerUrl(href);
      const finalUrl = /^https?:\/\//i.test(decoded) ? decoded : cleanUrl(href);
      if (finalUrl && !episodes.some((episode) => episode.playId === finalUrl)) {
        episodes.push({ name: `线路${episodes.length + 1}`, playId: finalUrl });
      }
    });

    if (!episodes.length) {
      $("a[href]").each((_, element) => {
        const href = $(element).attr("href") || "";
        const text = $(element).text().trim();
        if (!href || !["播放", "watch", "video", "观看", "在线播放"].some((word) =>
          text.toLowerCase().includes(word.toLowerCase()))) {
          return;
        }
        const finalUrl = cleanUrl(href);
        if (finalUrl && !episodes.some((episode) => episode.playId === finalUrl)) {
          episodes.push({ name: text || `线路${episodes.length + 1}`, playId: finalUrl });
        }
      });
    }
    if (!episodes.length) episodes.push({ name: "默认线路", playId: url });

    return {
      list: [{
        vod_id: String(videoId),
        vod_name: title,
        vod_pic: pic,
        vod_content: $("meta[name='description']").attr("content") || title,
        vod_year: "",
        vod_remarks: "",
        vod_douban_score: "",
        vod_actor: "",
        vod_director: "",
        vod_area: "",
        vod_play_sources: [{ name: "线路1", episodes }],
      }],
    };
  } catch (error) {
    await logError("detail", error);
    return { list: [] };
  }
}

async function search(params, context) {
  const keyword = String(params.keyword || params.wd || "").trim();
  const page = safeInt(params.page, 1);
  if (!keyword) return { page: 1, pagecount: 0, total: 0, list: [] };

  try {
    const query = new URLSearchParams({ s: keyword });
    const url = page === 1
      ? `${SITE}/?${query}`
      : `${SITE}/page/${page}/?${query}`;
    const list = parseList(await requestHtml(url));
    return { page, pagecount: 9999, total: 999999, list };
  } catch (error) {
    await logError("search", error);
    return { page, pagecount: 0, total: 0, list: [] };
  }
}

async function play(params, context) {
  const playId = String(params.playId || "").trim();
  const flag = params.flag || "play";
  if (!playId) throw new Error("playId 不能为空");
  const direct = /\.(m3u8|mp4|ts|mpd)(?:[?#].*)?$/i.test(playId);
  return {
    urls: [{ name: "播放", url: cleanUrl(playId) }],
    flag,
    header: HEADERS,
    parse: direct ? 0 : 1,
  };
}
