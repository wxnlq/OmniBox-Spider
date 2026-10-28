// @name 小穴生
// @version 1.0.0
// @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/影视/瑟瑟/小穴生[瑟瑟].js
// @dependencies spider_runner axios cheerio
const OmniBox = require("omnibox_sdk");
const runner = require("spider_runner");
const axios = require("axios");
const cheerio = require("cheerio");

const BASE_URL = "https://kkb2.sixnicexxs.cc";

module.exports = { home, category, detail, search, play };
runner.run(module.exports);

function fixUrl(url) {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  if (url.startsWith("//")) return "https:" + url;
  if (url.startsWith("/")) return BASE_URL + url;
  return BASE_URL + "/" + url;
}

async function fetchHtml(url) {
  const res = await axios.get(url, {
    timeout: 20000,
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      Referer: BASE_URL + "/",
      Origin: BASE_URL,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    },
  });
  return res.data || "";
}

async function extractVideoUrlFromText(html, seen = new Set(), depth = 0) {
  if (!html) return "";
  if (depth > 5) return "";

  const raw = String(html).trim();
  if (!raw) return "";

  const normalized = raw
    .replace(/\\\//g, "/")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">");

  const direct = normalized.match(/https?:\/\/[^\s"'<>]+(?:\.(?:m3u8|mp4|flv|ts))(?:(?:\?|#)[^\s"'<>]*)?/i);
  if (direct) return direct[0];

  const varPatterns = [
    /["'](?:url|src|videoUrl|video_url|play_url|playUrl)["']\s*:\s*["']([^"']+)["']/i,
    /(?:var\s+)?(?:url|src|videoUrl|video_url|play_url|playUrl)\s*=\s*["']([^"']+)["']/i,
    /(?:window\.location|location\.href)\s*=\s*["']([^"']+)["']/i,
    /["'](?:video|url)["']\s*:\s*["']([^"']+)["']/i,
  ];

  for (const p of varPatterns) {
    const m = normalized.match(p);
    if (m && m[1]) {
      const val = m[1].trim();
      if (/^https?:\/\//i.test(val)) return val;
      if (val && /m3u8|mp4|flv|ts/i.test(val)) {
        return fixUrl(val);
      }
    }
  }

  const iframe = normalized.match(/<iframe[^>]+src=["']([^"']+)["']/i);
  if (iframe && iframe[1]) {
    const iframeUrl = fixUrl(iframe[1]);
    if (!seen.has(iframeUrl)) {
      seen.add(iframeUrl);
      try {
        const iframeHtml = await fetchHtml(iframeUrl);
        const inner = await extractVideoUrlFromText(iframeHtml, seen, depth + 1);
        if (inner) return inner;
      } catch (e) {}
    }
  }

  const locationMatch = normalized.match(/location\.href\s*=\s*["']([^"']+)["']/i);
  if (locationMatch && locationMatch[1]) {
    const redirectUrl = fixUrl(locationMatch[1]);
    if (!seen.has(redirectUrl)) {
      seen.add(redirectUrl);
      try {
        const redirectHtml = await fetchHtml(redirectUrl);
        const inner = await extractVideoUrlFromText(redirectHtml, seen, depth + 1);
        if (inner) return inner;
      } catch (e) {}
    }
  }

  const videoTag = normalized.match(/<video[^>]+src=["']([^"']+)["']/i);
  if (videoTag && videoTag[1]) return videoTag[1];

  const sourceTag = normalized.match(/<source[^>]+src=["']([^"']+)["']/i);
  if (sourceTag && sourceTag[1]) return sourceTag[1];

  const scripts = [...normalized.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)];
  for (const script of scripts) {
    const scriptText = script[1] || "";
    const m = scriptText.match(/https?:\/\/[^\s"'<>]+(?:\.(?:m3u8|mp4|flv|ts))(?:(?:\?|#)[^\s"'<>]*)?/i);
    if (m) return m[0];
  }

  return "";
}

function normalizeTagItem(href, name, extra = {}) {
  if (!href || !name) return null;
  return {
    name: String(name).trim(),
    href,
    className: "cursor-pointer",
    id: "dark-link",
    target: "_blank",
    ...extra,
  };
}

function extractLinkTags($, selector, hrefPattern, options = {}) {
  const items = [];
  const seen = new Set();

  $(selector).each((_, el) => {
    const href = $(el).attr("href");
    const name = $(el).text().trim();
    if (!href || !name) return;
    if (hrefPattern && !hrefPattern.test(href)) return;
    const key = `${href}::${name}`;
    if (seen.has(key)) return;
    seen.add(key);
    const item = normalizeTagItem(href, name, options);
    if (item) items.push(item);
  });

  return items;
}

function buildFilterData($) {
  const filterTags = extractLinkTags(
    $,
    "section.dx-tag-panel a[href*='/index.php/vod/type/id/']",
    /\/index\.php\/vod\/type\/id\/\d+\.html/i,
    { type: "category", className: "cursor-pointer", id: "dark-link" }
  );

  const hotTags = extractLinkTags(
    $,
    "a[href*='/index.php/vod/search.html?wd=']",
    /\/index\.php\/vod\/search\.html\?wd=/i,
    { type: "hot", className: "cursor-pointer", id: "dark-link" }
  );

  return {
    filterTags,
    hotTags,
    tags: [...filterTags, ...hotTags],
    filters: {
      category: filterTags,
      hot: hotTags,
    },
  };
}

async function home(params, context) {
  await OmniBox.log("info", "获取首页数据");
  const html = await fetchHtml(BASE_URL + "/");
  const $ = cheerio.load(html);

  const classList = [];
  const seen = new Set();

  $("section.dx-tag-panel a[href*='/index.php/vod/type/id/']").each((_, el) => {
    const href = $(el).attr("href");
    const name = $(el).text().trim();
    if (!href || !name) return;
    const match = href.match(/\/index\.php\/vod\/type\/id\/(\d+)\.html/i);
    if (!match) return;
    const id = match[1];
    if (seen.has(id)) return;
    seen.add(id);
    classList.push({ type_id: id, type_name: name, className: "cursor-pointer" });
  });

  const filterData = buildFilterData($);

  const list = [];
  $("a.dx-card[href*='/index.php/vod/play/']").each((_, el) => {
    const href = $(el).attr("href");
    const title = $(el).attr("title") || $(el).find("img").attr("alt") || "";
    const pic = $(el).find("img").first().attr("src") || "";
    const tag = $(el).find("i").first().text().trim();

    if (!href || !title) return;

    list.push({
      vod_id: href,
      vod_name: title,
      vod_pic: fixUrl(pic),
      type_id: "0",
      type_name: tag || "未知",
      vod_remarks: tag || "",
    });
  });

  return {
    class: classList,
    filterTags: filterData.filterTags,
    hotTags: filterData.hotTags,
    tags: filterData.tags,
    filters: filterData.filters,
    list: list.slice(0, 20),
  };
}

async function category(params, context) {
  const categoryId = params.categoryId || params.type_id || "1";
  const page = Number(params.page || 1);

  let url = `${BASE_URL}/index.php/vod/type/id/${categoryId}.html`;
  if (page > 1) {
    url = `${BASE_URL}/index.php/vod/type/id/${categoryId}/page/${page}.html`;
  }

  const html = await fetchHtml(url);
  const $ = cheerio.load(html);
  const filterData = buildFilterData($);

  const list = [];
  $("a.dx-card[href*='/index.php/vod/play/']").each((_, el) => {
    const href = $(el).attr("href");
    const title = $(el).attr("title") || $(el).find("img").attr("alt") || "";
    const pic = $(el).find("img").first().attr("src") || "";
    const tag = $(el).find("i").first().text().trim();
    if (!href || !title) return;

    list.push({
      vod_id: href,
      vod_name: title,
      vod_pic: fixUrl(pic),
      type_id: categoryId,
      type_name: tag || "未知",
      vod_remarks: tag || "",
    });
  });

  return {
    page,
    pagecount: 10,
    total: list.length || 0,
    filterTags: filterData.filterTags,
    hotTags: filterData.hotTags,
    tags: filterData.tags,
    filters: filterData.filters,
    list,
  };
}

async function detail(params, context) {
  const videoUrl = params.videoId || params.id;
  if (!videoUrl) return { list: [] };

  const html = await fetchHtml(fixUrl(videoUrl));
  const $ = cheerio.load(html);

  const title = $("title").text().split("_")[0].trim() || "未知视频";
  const pic = $("img").first().attr("src") || "";

  return {
    list: [
      {
        vod_id: videoUrl,
        vod_name: title,
        vod_pic: fixUrl(pic),
        vod_content: "详情页仅提供播放入口，实际播放地址在播放页中解析。",
        vod_play_sources: [
          {
            name: "线路1",
            episodes: [{ name: "播放", playId: videoUrl }],
          },
        ],
      },
    ],
  };
}

async function search(params, context) {
  const keyword = params.keyword || "";
  const page = Number(params.page || 1);
  if (!keyword) return { page, pagecount: 0, total: 0, list: [] };

  const url = `${BASE_URL}/index.php/vod/search.html?wd=${encodeURIComponent(keyword)}&page=${page}`;
  const html = await fetchHtml(url);
  const $ = cheerio.load(html);

  const list = [];
  $("a.dx-card[href*='/index.php/vod/play/']").each((_, el) => {
    const href = $(el).attr("href");
    const title = $(el).attr("title") || $(el).find("img").attr("alt") || "";
    const pic = $(el).find("img").first().attr("src") || "";
    if (!href || !title) return;

    list.push({
      vod_id: href,
      vod_name: title,
      vod_pic: fixUrl(pic),
      type_id: "0",
      type_name: "搜索",
      vod_remarks: "",
    });
  });

  return {
    page,
    pagecount: 5,
    total: list.length || 0,
    list,
  };
}

async function play(params, context) {
  const playId = params.playId;
  const flag = params.flag || "线路1";

  if (!playId) {
    throw new Error("playId 不能为空");
  }

  const playUrl = fixUrl(playId);
  const html = await fetchHtml(playUrl);
  const realUrl = await extractVideoUrlFromText(html);

  if (!realUrl) {
    return {
      urls: [],
      parse: 1,
    };
  }

  return {
    urls: [{ name: flag, url: realUrl }],
    flag,
    header: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      Referer: playUrl,
      Origin: BASE_URL,
    },
    parse: 0,
  };
}