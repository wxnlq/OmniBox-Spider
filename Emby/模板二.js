// @name Emby-妯℃澘浜?
// @author
<<<<<<< HEAD
// @description 鐩磋繛 Emby 鎺ュ彛锛孴VBox T4 缁撴瀯杈撳嚭锛堝埉鍓婏細涓嶆敮鎸侊紝寮瑰箷锛氫笉鏀寔锛屽梾鎺細涓嶆敮鎸侊級
// @dependencies axios
// @version 1.0.0
// @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/Emby/%E6%A8%A1%E6%9D%BF%E4%BA%8C.js
// @indexs 0
=======
// @description 直连 Emby 接口，TVBox T4 结构输出（刮削：不支持，弹幕：不支持，嗅探：不支持）
// @dependencies axios
// @version 1.0.0
// @downloadURL https://raw.githubusercontent.com/wxnlq/OmniBox-Spider/refs/heads/main/Emby/模板二.js
<<<<<<< HEAD
>>>>>>> parent of 03e8814 (重写注释)
=======
>>>>>>> parent of 03e8814 (重写注释)

/**
 * ============================================================================
 * Emby[浼榏 - TVBox T4 鎺ュ彛鏍煎紡鑴氭湰
 * ============================================================================
 * 璇存槑锛?
 * 1. 灏嗘湰鍦?Emby 瑙勫垯鑴氭湰鏀归€犱负 OmniBox 鏍囧噯 5 鏂规硶杈撳嚭锛坔ome/category/search/detail/play锛夈€?
 * 2. 缁撴瀯涓庢敞閲婇鏍煎弬鑰冦€屼袱涓狟T銆嶈剼鏈紝渚夸簬缁熶竴缁存姢銆?
 * 3. 閰嶇疆寤鸿閫氳繃鐜鍙橀噺浼犲叆锛屾垨閫氳繃 params.extend 杩涜瑕嗙洊銆?
 */

const axios = require("axios");
const http = require("http");
const https = require("https");
const OmniBox = require("omnibox_sdk");

// ==================== 閰嶇疆鍖哄煙 ====================
const DEFAULT_CONFIG = {
  host: process.env.EMBY_HOST || "",
  userId: process.env.EMBY_USER_ID || "",
  token: process.env.EMBY_TOKEN || "",
  deviceId: process.env.EMBY_DEVICE_ID || "",
  clientVersion: process.env.EMBY_CLIENT_VERSION || "",
  pageSize: parseInt(process.env.EMBY_PAGE_SIZE || "30", 10) || 30,
};

const BASE_FIELDS = "BasicSyncInfo,CanDelete,Container,PrimaryImageAspectRatio,ProductionYear,Status,EndDate";
const IMAGE_TYPES = "Primary,Backdrop,Thumb,Banner";

const DEVICE_PROFILE = {
  DeviceProfile: {
    MaxStaticBitrate: 140000000,
    MaxStreamingBitrate: 140000000,
    DirectPlayProfiles: [
      {
        Container: "mp4,mkv,webm",
        Type: "Video",
        VideoCodec: "h264,h265,av1,vp9",
        AudioCodec: "aac,mp3,opus,flac",
      },
      { Container: "mp3,aac,flac,opus", Type: "Audio" },
    ],
    TranscodingProfiles: [
      {
        Container: "mp4",
        Type: "Video",
        VideoCodec: "h264",
        AudioCodec: "aac",
        Context: "Streaming",
        Protocol: "http",
      },
      { Container: "aac", Type: "Audio", Context: "Streaming", Protocol: "http" },
    ],
    SubtitleProfiles: [{ Format: "srt,ass,vtt", Method: "External" }],
    CodecProfiles: [
      {
        Type: "Video",
        Codec: "h264",
        ApplyConditions: [{ Condition: "LessThanEqual", Property: "VideoLevel", Value: "62" }],
      },
    ],
    BreakOnNonKeyFrames: true,
  },
};

const axiosInstance = axios.create({
  timeout: 15000,
  httpsAgent: new https.Agent({ keepAlive: true, rejectUnauthorized: false }),
  httpAgent: new http.Agent({ keepAlive: true }),
  validateStatus: (status) => status >= 200,
});

// ==================== 鏃ュ織宸ュ叿 ====================
const logInfo = (message, data = null) => {
  const output = data ? `${message}: ${JSON.stringify(data)}` : message;
  OmniBox.log("info", `[Emby-DEBUG] ${output}`);
};

const logError = (message, error) => {
  OmniBox.log("error", `[Emby-DEBUG] ${message}: ${error?.message || error}`);
};

// ==================== 鍩虹宸ュ叿 ====================
function normalizeHost(host) {
  const raw = String(host || "").trim();
  if (!raw) return "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

function toInt(value, defaultValue = 0) {
  const num = parseInt(String(value ?? ""), 10);
  return Number.isNaN(num) ? defaultValue : num;
}

function parseExtendParams(extend) {
  if (!extend) return {};
  if (typeof extend === "object") return extend;
  const text = String(extend || "").trim();
  if (!text) return {};
  try {
    const decoded = Buffer.from(text, "base64").toString("utf-8");
    return JSON.parse(decoded);
  } catch (_) {
    try {
      return JSON.parse(text);
    } catch (error) {
      logError("extend 鍙傛暟瑙ｆ瀽澶辫触", error);
      return {};
    }
  }
}

function resolveConfig(params = {}) {
  const ext = parseExtendParams(params.extend || params.config || params.ext);
  const merged = {
    ...DEFAULT_CONFIG,
    ...ext,
  };
  merged.host = normalizeHost(merged.host);
  merged.pageSize = toInt(merged.pageSize, DEFAULT_CONFIG.pageSize);
  return merged;
}

function getHeaders(config, extra = {}) {
  return {
    "X-Emby-Client": "Emby Web",
    "X-Emby-Device-Name": "Android WebView Android",
    "X-Emby-Device-Id": config.deviceId,
    "X-Emby-Client-Version": config.clientVersion,
    "X-Emby-Token": config.token,
    ...extra,
  };
}

function getImageUrl(config, itemId, imageTag) {
  if (!itemId || !imageTag) return "";
  return `${config.host}/emby/Items/${itemId}/Images/Primary?maxWidth=400&tag=${imageTag}&quality=90`;
}

function encodeMeta(obj) {
  try {
    return Buffer.from(JSON.stringify(obj || {}), "utf8").toString("base64");
  } catch {
    return "";
  }
}

function decodeMeta(str) {
  try {
    const raw = Buffer.from(str || "", "base64").toString("utf8");
    return JSON.parse(raw || "{}");
  } catch {
    return {};
  }
}

async function requestJson(url, options = {}, config) {
  const start = Date.now();
  try {
    const res = await axiosInstance.request({
      url,
      ...options,
      headers: {
        ...(options.headers || {}),
        ...getHeaders(config),
      },
    });
    const cost = Date.now() - start;
    logInfo(`璇锋眰瀹屾垚 ${url}`, { status: res.status, cost });
    if (res.status >= 400) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.data;
  } catch (error) {
    const cost = Date.now() - start;
    logError(`璇锋眰澶辫触 ${url} cost=${cost}ms`, error);
    throw error;
  }
}

function extractList(config, jsonData) {
  return (jsonData?.Items || []).map((item) => {
    const isFolder = ["Folder", "BoxSet", "CollectionFolder"].includes(item.Type);
    return {
      vod_id: String(item.Id || ""),
      vod_name: item.Name || "",
      vod_pic: getImageUrl(config, item.Id, item.ImageTags?.Primary),
      vod_remarks: item.ProductionYear ? String(item.ProductionYear) : "",
      vod_tag: isFolder ? "folder" : "video",
    };
  });
}

async function fetchPlaybackInfo(config, itemId) {
  const url = `${config.host}/emby/Items/${itemId}/PlaybackInfo`;
  return requestJson(
    url,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify(DEVICE_PROFILE),
    },
    config
  );
}

async function resolveFirstEpisodeId(config, seriesId) {
  const url = `${config.host}/emby/Shows/${seriesId}/Episodes?` +
    `UserId=${config.userId}&Fields=Overview,PrimaryImageAspectRatio&StartIndex=0&Limit=1&` +
    `SortBy=IndexNumber&SortOrder=Ascending`;

  const data = await requestJson(url, {}, config);
  const first = data?.Items?.[0];
  return first?.Id ? String(first.Id) : "";
}

// ==================== 鎺ュ彛瀹炵幇 ====================

async function home(params = {}) {
  const config = resolveConfig(params);
  logInfo("杩涘叆棣栭〉", { host: config.host });

  if (!config.host || !config.userId || !config.token) {
    logError("缂哄皯蹇呰閰嶇疆", new Error("璇烽厤缃?EMBY_HOST/EMBY_USER_ID/EMBY_TOKEN"));
    return { class: [], list: [] };
  }

  try {
    const classesUrl = `${config.host}/emby/Users/${config.userId}/Views`;
    const classJson = await requestJson(classesUrl, {}, config);

    const classList = (classJson?.Items || [])
      .filter((it) => !String(it.Name || "").includes("鎾斁鍒楄〃") && !String(it.Name || "").includes("鐩告満"))
      .map((it) => ({ type_id: String(it.Id), type_name: it.Name }));

    const listUrl = `${config.host}/emby/Users/${config.userId}/Items?` +
      `SortBy=DateCreated&SortOrder=Descending&IncludeItemTypes=Movie,Series,Folder&` +
      `Recursive=true&Limit=40&Fields=${BASE_FIELDS},CommunityRating,CriticRating,Path,Overview,IsFolder&` +
      `EnableImageTypes=${IMAGE_TYPES}&ImageTypeLimit=1`;
    const listJson = await requestJson(listUrl, {}, config);

    return {
      class: classList,
      list: extractList(config, listJson),
    };
  } catch (e) {
    logError("棣栭〉璇锋眰澶辫触", e);
    return { class: [], list: [] };
  }
}

async function category(params = {}) {
  const config = resolveConfig(params);
  const categoryId = params.categoryId || params.type_id || "";
  const pg = Math.max(1, toInt(params.page, 1));
  const startIndex = (pg - 1) * config.pageSize;

  logInfo("璇锋眰鍒嗙被", { categoryId, page: pg });

  if (!config.host || !config.userId || !config.token) {
    logError("缂哄皯蹇呰閰嶇疆", new Error("璇烽厤缃?EMBY_HOST/EMBY_USER_ID/EMBY_TOKEN"));
    return { list: [], page: pg, pagecount: 0 };
  }

  try {
    const url = `${config.host}/emby/Users/${config.userId}/Items?` +
      `SortBy=DateLastContentAdded,SortName&SortOrder=Descending&` +
      `IncludeItemTypes=Movie,Series,Folder&Recursive=true&` +
      `Fields=${BASE_FIELDS},CommunityRating,CriticRating,Path,Overview,IsFolder&` +
      `StartIndex=${startIndex}&ParentId=${categoryId}&EnableImageTypes=${IMAGE_TYPES}&` +
      `ImageTypeLimit=1&Limit=${config.pageSize}&EnableUserData=true`;

    const data = await requestJson(url, {}, config);
    const list = extractList(config, data);

    return {
      list,
      page: pg,
      pagecount: list.length >= config.pageSize ? pg + 1 : pg,
    };
  } catch (e) {
    logError("鍒嗙被璇锋眰澶辫触", e);
    return { list: [], page: pg, pagecount: 0 };
  }
}

async function search(params = {}) {
  const config = resolveConfig(params);
  const wd = params.keyword || params.wd || "";
  const pg = Math.max(1, toInt(params.page, 1));
  const startIndex = (pg - 1) * config.pageSize;

  logInfo("鎼滅储", { keyword: wd, page: pg });

  if (!config.host || !config.userId || !config.token) {
    logError("缂哄皯蹇呰閰嶇疆", new Error("璇烽厤缃?EMBY_HOST/EMBY_USER_ID/EMBY_TOKEN"));
    return { list: [], page: pg, pagecount: 0 };
  }

  try {
    const url = `${config.host}/emby/Users/${config.userId}/Items?` +
      `SortBy=SortName&SortOrder=Ascending&Fields=${BASE_FIELDS}&` +
      `StartIndex=${startIndex}&EnableImageTypes=${IMAGE_TYPES}&ImageTypeLimit=1&` +
      `Recursive=true&SearchTerm=${encodeURIComponent(wd)}&GroupProgramsBySeries=true&` +
      `Limit=${config.pageSize}`;

    const data = await requestJson(url, {}, config);
    const list = extractList(config, data);

    return {
      list,
      page: pg,
      pagecount: list.length >= config.pageSize ? pg + 1 : pg,
    };
  } catch (e) {
    logError("鎼滅储澶辫触", e);
    return { list: [], page: pg, pagecount: 0 };
  }
}

async function detail(params = {}) {
  const config = resolveConfig(params);
  const videoId = params.videoId || "";
  logInfo("璇锋眰璇︽儏", { videoId });

  if (!config.host || !config.userId || !config.token) {
    logError("缂哄皯蹇呰閰嶇疆", new Error("璇烽厤缃?EMBY_HOST/EMBY_USER_ID/EMBY_TOKEN"));
    return { list: [] };
  }

  try {
    const detailUrl = `${config.host}/emby/Users/${config.userId}/Items/${videoId}?` +
      `Fields=${BASE_FIELDS},CommunityRating,CriticRating,Path,Overview,People,Studios,RunTimeTicks,MediaStreams`;
    const info = await requestJson(detailUrl, {}, config);

    const people = info?.People || [];
    const director = people
      .filter((p) => p.Type === "Director" || (p.Role && p.Role.includes("Director")))
      .map((p) => p.Name)
      .join(" / ");

    const actor = people
      .filter((p) => p.Type === "Actor" || (p.Role && p.Role.includes("Actor")))
      .map((p) => p.Name)
      .join(" / ");

    const area = (info?.Studios || []).map((s) => s.Name).join(" / ");
    const language = Array.from(
      new Set(
        (info?.MediaStreams || [])
          .filter((s) => s.Type === "Audio" && s.Language)
          .map((s) => s.Language)
      )
    ).join(" / ");

    let duration = "";
    if (info?.RunTimeTicks) {
      const mins = Math.floor(info.RunTimeTicks / 600000000);
      const hours = Math.floor(mins / 60);
      duration = hours > 0 ? `${hours}灏忔椂${mins}鍒嗛挓` : `${mins}鍒嗛挓`;
    }

    const vod = {
      vod_id: String(videoId),
      vod_name: info?.Name || "",
      vod_pic: getImageUrl(config, info?.Id, info?.ImageTags?.Primary),
      vod_remarks: `璇勫垎锛?{info?.CommunityRating || "N/A"}`,
      vod_content: info?.Overview || "",
      vod_year: info?.ProductionYear ? String(info.ProductionYear) : "",
      vod_director: director,
      vod_actor: actor,
      vod_area: area,
      vod_lang: language,
      vod_time: duration,
      type_name: (info?.Genres || []).join(" "),
    };

    const playSources = [];

    if (info?.Type === "Series") {
      const seasonsUrl = `${config.host}/emby/Shows/${videoId}/Seasons?` +
        `UserId=${config.userId}&Fields=${BASE_FIELDS},Path,Overview&EnableTotalRecordCount=false`;
      const seasonsData = await requestJson(seasonsUrl, {}, config);
      const seasons = seasonsData?.Items || [];

      for (const season of seasons) {
        const episodesUrl = `${config.host}/emby/Shows/${videoId}/Episodes?` +
          `SeasonId=${season.Id}&ImageTypeLimit=1&UserId=${config.userId}&` +
          `Fields=Overview,PrimaryImageAspectRatio&Limit=1000`;
        const episodeData = await requestJson(episodesUrl, {}, config);
        const episodes = (episodeData?.Items || []).map((item) => {
          const episodeNum = item.IndexNumber ? `绗?{item.IndexNumber}闆哷 : "鏈煡闆嗘暟";
          const fullName = item.Name ? `${episodeNum} ${item.Name}` : episodeNum;
          const playId = `${item.Id}|||${encodeMeta({ type: "item", name: fullName })}`;
          return { name: fullName, playId };
        });

        if (episodes.length > 0) {
          playSources.push({ name: season.Name || "榛樿绾胯矾", episodes });
        }
      }
    } else if (["Folder", "BoxSet", "CollectionFolder"].includes(info?.Type)) {
      const childrenUrl = `${config.host}/emby/Users/${config.userId}/Items?` +
        `ParentId=${videoId}&Recursive=false&IncludeItemTypes=Movie,Series,Video&` +
        `Fields=${BASE_FIELDS},Overview&SortBy=SortName&SortOrder=Ascending&Limit=200`;
      const childrenData = await requestJson(childrenUrl, {}, config);
      const episodes = (childrenData?.Items || []).map((item) => {
        const label = item.Type === "Series" ? `${item.Name} [绯诲垪]` : item.Name;
        const playId = `${item.Id}|||${encodeMeta({ type: item.Type === "Series" ? "series" : "item", name: label })}`;
        return { name: label, playId };
      });
      if (episodes.length > 0) {
        playSources.push({ name: "璧勬簮鍒楄〃", episodes });
      }
    } else {
      const playId = `${videoId}|||${encodeMeta({ type: "item", name: info?.Name || "鎾斁" })}`;
      playSources.push({ name: "EMBY", episodes: [{ name: info?.Name || "鎾斁", playId }] });
    }

    vod.vod_play_sources = playSources;

    return { list: [vod] };
  } catch (e) {
    logError("璇︽儏鑾峰彇澶辫触", e);
    return { list: [] };
  }
}

async function play(params = {}) {
  const config = resolveConfig(params);
  const rawPlayId = params.playId || "";
  logInfo("鍑嗗鎾斁", { playId: rawPlayId });

  if (!config.host || !config.userId || !config.token) {
    logError("缂哄皯蹇呰閰嶇疆", new Error("璇烽厤缃?EMBY_HOST/EMBY_USER_ID/EMBY_TOKEN"));
    return { urls: [], parse: 1 };
  }

  try {
    let playId = rawPlayId;
    let meta = {};
    if (rawPlayId.includes("|||")) {
      const parts = rawPlayId.split("|||");
      playId = parts[0];
      meta = decodeMeta(parts[1]);
    }

    let itemId = String(playId || "");
    if (meta?.type === "series") {
      const firstEpisodeId = await resolveFirstEpisodeId(config, itemId);
      if (!firstEpisodeId) {
        throw new Error("鏈壘鍒板彲鎾斁鐨勫墽闆?);
      }
      itemId = firstEpisodeId;
    }

    const playbackInfo = await fetchPlaybackInfo(config, itemId);
    const mediaSource = playbackInfo?.MediaSources?.[0];

    if (!mediaSource) {
      return {
        parse: 1,
        url: `${config.host}/emby/Items/${itemId}/PlaybackInfo`,
        header: getHeaders(config, { "Content-Type": "application/json" }),
        msg: "娌℃湁鍙敤鐨勫獟浣撴簮",
      };
    }

    const playUrl = `${config.host}/emby/videos/${itemId}/stream?` +
      `Static=true&MediaSourceId=${mediaSource.Id}&DeviceId=${config.deviceId}&` +
      `api_key=${config.token}&PlaySessionId=${playbackInfo.PlaySessionId || ""}`;

    return {
      urls: [{ name: meta?.name || "榛樿绾胯矾", url: playUrl }],
      parse: 0,
      header: getHeaders(config),
    };
  } catch (e) {
    logError("瑙ｆ瀽鎾斁鍦板潃澶辫触", e);
    return { urls: [], parse: 1 };
  }
}

module.exports = { home, category, search, detail, play };

const runner = require("spider_runner");
runner.run(module.exports);


