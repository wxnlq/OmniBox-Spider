/**
* ============================================================================
* 在线之家资源 - OmniBox 爬虫脚本
* ============================================================================
*/
const axios = require("axios");
const https = require("https");
const http = require("http");
const cheerio = require("cheerio");
const OmniBox = require("omnibox_sdk");

// ========== 全局配置 ==========
const host = 'https://www.zxzjys.com';
const def_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.zxzjys.com'
};

const axiosInstance = axios.create({
    httpsAgent: new https.Agent({ keepAlive: true, rejectUnauthorized: false }),
    httpAgent: new http.Agent({ keepAlive: true }),
    timeout: 15000
});

/**
* 日志工具函数
*/
const logInfo = (message, data = null) => {
    const output = data ? `${message}: ${JSON.stringify(data)}` : message;
    OmniBox.log("info", `[ZXZJ-DEBUG] ${output}`);
};

const logError = (message, error) => {
    OmniBox.log("error", `[ZXZJ-DEBUG] ${message}: ${error.message || error}`);
};

const encodeMeta = (obj) => {
    try {
        return Buffer.from(JSON.stringify(obj || {}), "utf8").toString("base64");
    } catch {
        return "";
    }
};

const decodeMeta = (str) => {
    try {
        const raw = Buffer.from(str || "", "base64").toString("utf8");
        return JSON.parse(raw || "{}");
    } catch {
        return {};
    }
};

const buildScrapedEpisodeName = (scrapeData, mapping, originalName) => {
    if (!mapping || mapping.episodeNumber === 0 || (mapping.confidence && mapping.confidence < 0.5)) {
        return originalName;
    }
    if (mapping.episodeName) {
        return mapping.episodeName;
    }
    if (scrapeData && Array.isArray(scrapeData.episodes)) {
        const hit = scrapeData.episodes.find(
            (ep) => ep.episodeNumber === mapping.episodeNumber && ep.seasonNumber === mapping.seasonNumber
        );
        if (hit?.name) {
            return `${hit.episodeNumber}.${hit.name}`;
        }
    }
    return originalName;
};

/**
* 图像地址修复
*/
const fixPicUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    if (url.startsWith('//')) return 'https:' + url;
    return url.startsWith('/') ? `${host}${url}` : `${host}/${url}`;
};

/**
* 核心:解析 CMS 字符串为结构化播放源
* 逻辑:将 "来源1$$$来源2" 和 "第1集$ID1#第2集$ID2" 转换为 UI 识别的数组
*/
const parsePlaySources = (fromStr, urlStr, videoId = "", vodName = "") => {
    logInfo("开始解析播放源字符串", { from: fromStr, url: urlStr });
    const playSources = [];
    if (!fromStr || !urlStr) return playSources;

    const froms = fromStr.split('$$$');
    const urls = urlStr.split('$$$');

    for (let i = 0; i < froms.length; i++) {
        const sourceName = froms[i] || `线路${i + 1}`;
        const sourceItems = urls[i] ? urls[i].split('#') : [];

        const episodes = sourceItems.map((item, epIndex) => {
            const parts = item.split('$');
            const episodeName = parts[0] || '正片';
            const actualPlayId = parts[1] || parts[0];
            const fid = `${videoId}#${i}#${epIndex}`;
            return {
                name: episodeName,
                playId: `${actualPlayId}|||${encodeMeta({ sid: videoId, fid, v: vodName || "", e: episodeName })}`,
                _fid: fid,
                _rawName: episodeName,
            };
        }).filter(e => e.playId);

        if (episodes.length > 0) {
            playSources.push({
                name: sourceName,
                episodes: episodes
            });
        }
    }
    logInfo("播放源解析结果", playSources);
    return playSources;
};

/**
* 解析视频列表(工具函数)
*/
const parseVideoList = ($) => {
    const boxes = $('.stui-vodlist__item, .stui-vodlist li');
    const list = [];
    boxes.each((_, box) => {
        const $box = $(box);
        const $thumbEl = $box.find('.stui-vodlist__thumb, .pic');
        const $titleEl = $box.find('.title a').length ? $box.find('.title a') : $thumbEl;
        const $remarksEl = $box.find('.pic-text');

        // 处理vodId
        let vodId = $thumbEl.attr('href') || '';
        if (vodId && !vodId.startsWith('http')) {
            vodId = host + (vodId.startsWith('/') ? '' : '/') + vodId;
        }

        // 处理vodPic
        let vodPic = $thumbEl.attr('data-original') ||
            ($thumbEl.css('background-image') || '').match(/url\(["']?([^"')]+)["']?\)/)?.[1] || '';
        vodPic = fixPicUrl(vodPic);

        list.push({
            vod_id: vodId,
            vod_name: $thumbEl.attr('title') || $titleEl.text().trim() || '',
            vod_pic: vodPic,
            vod_remarks: $remarksEl.text().trim() || '',
            vod_actor: $box.find('.text').text().trim() || ''
        });
    });
    return list.filter(item => item.vod_id);
};

// ========== 接口实现 ==========

async function home(params) {
    logInfo("进入首页");
    return {
        class: [
            { 'type_id': '1', 'type_name': '电影' },
            { 'type_id': '2', 'type_name': '美剧' },
            { 'type_id': '3', 'type_name': '韩剧' },
            { 'type_id': '4', 'type_name': '日剧' },
            { 'type_id': '5', 'type_name': '泰剧' },
            { 'type_id': '6', 'type_name': '动漫' }
        ],
        list: []
    };
}

async function category(params) {
    const { categoryId, page } = params;
    const pg = parseInt(page) || 1;
    logInfo(`请求分类: ${categoryId}, 页码: ${pg}`);

    try {
        const url = `${host}/list/${categoryId}-${pg}.html`;
        const res = await axiosInstance.get(url, { headers: def_headers });
        const $ = cheerio.load(res.data);

        const list = parseVideoList($);

        // 解析总页数
        let pagecount = pg;
        try {
            const lastPageLink = $('.stui-page__item a').last();
            if (lastPageLink.length) {
                const lastHref = lastPageLink.attr('href');
                const match = lastHref.match(/-(\d+)\.html/);
                if (match) pagecount = parseInt(match[1]);
            }
        } catch (e) {
            logError("解析页数失败", e);
        }

        logInfo("分类接口返回数据", { count: list.length, pagecount });

        return {
            list: list,
            page: pg,
            pagecount: pagecount
        };
    } catch (e) {
        logError("分类请求失败", e);
        return { list: [], page: pg, pagecount: 0 };
    }
}

async function detail(params) {
    const videoId = params.videoId;
    logInfo(`请求详情 ID: ${videoId}`);

    try {
        const res = await axiosInstance.get(videoId, { headers: def_headers });
        const $ = cheerio.load(res.data);

        // 基础信息
        const title = $('.stui-content__detail .title').text().trim() || '';
        let vodPic = $('.stui-content__thumb img').attr('data-original') || 
                     $('.stui-content__thumb img').attr('src') || '';
        vodPic = fixPicUrl(vodPic);

        // 详情信息提取
        const infoElements = $('.stui-content__detail .data');
        const findInfo = (tag) => {
            const el = infoElements.filter((_, item) => $(item).text().includes(tag));
            return el.text().replace(tag, '').replace(/[::]/g, '').trim() || '';
        };

        // 播放线路处理
        const tabEls = $('.nav-tabs li a');
        const playlistEls = $('.stui-content__playlist');
        const playFroms = [];
        const playUrls = [];

        playlistEls.each((index, ul) => {
            const fromName = $(tabEls[index]).text().trim() || `线路${index + 1}`;
            const links = [];
            $(ul).find('li a').each((_, a) => {
                let href = $(a).attr('href');
                if (href && !href.startsWith('http')) {
                    href = host + href;
                }
                links.push(`${$(a).text().trim()}$${href}`);
            });
            if (links.length > 0) {
                playFroms.push(fromName);
                playUrls.push(links.join('#'));
            }
        });

        const vod_play_from = playFroms.join('$$$');
        const vod_play_url = playUrls.join('$$$');

        logInfo("详情接口返回原始数据", { title, playFroms: vod_play_from });

        // 解析播放源
        const playSources = parsePlaySources(vod_play_from, vod_play_url, String(videoId || ""), title);

        // 刮削处理
        let scrapeData = null;
        let videoMappings = [];
        let scrapeType = "";
        const scrapeCandidates = [];

        for (const source of playSources) {
            for (const ep of source.episodes || []) {
                if (!ep._fid) continue;
                scrapeCandidates.push({
                    fid: ep._fid,
                    file_id: ep._fid,
                    file_name: ep._rawName || ep.name || "正片",
                    name: ep._rawName || ep.name || "正片",
                    format_type: "video",
                });
            }
        }

        if (scrapeCandidates.length > 0) {
            try {
                const sourceId = `spider_source_${await OmniBox.getSourceId()}_${String(videoId || "")}`;
                const scrapingResult = await OmniBox.processScraping(sourceId, title || "", title || "", scrapeCandidates);
                OmniBox.log("info", `[ZXZJ-DEBUG] 刮削处理完成,结果: ${JSON.stringify(scrapingResult || {}).substring(0, 200)}`);

                const metadata = await OmniBox.getScrapeMetadata(sourceId);
                scrapeData = metadata?.scrapeData || null;
                videoMappings = metadata?.videoMappings || [];
                scrapeType = metadata?.scrapeType || "";
                logInfo("刮削元数据读取完成", { hasScrapeData: !!scrapeData, mappingCount: videoMappings.length, scrapeType });
            } catch (error) {
                logError("刮削处理失败", error);
            }
        }

        for (const source of playSources) {
            for (const ep of source.episodes || []) {
                const mapping = videoMappings.find((m) => m?.fileId === ep._fid);
                if (!mapping) continue;
                const oldName = ep.name;
                const newName = buildScrapedEpisodeName(scrapeData, mapping, oldName);
                if (newName && newName !== oldName) {
                    ep.name = newName;
                    OmniBox.log("info", `[ZXZJ-DEBUG] 应用刮削后源文件名: ${oldName} -> ${newName}`);
                }
                ep._seasonNumber = mapping.seasonNumber;
                ep._episodeNumber = mapping.episodeNumber;
            }

            const hasEpisodeNumber = (source.episodes || []).some(
                (ep) => ep._episodeNumber !== undefined && ep._episodeNumber !== null
            );
            if (hasEpisodeNumber) {
                source.episodes.sort((a, b) => {
                    const seasonA = a._seasonNumber || 0;
                    const seasonB = b._seasonNumber || 0;
                    if (seasonA !== seasonB) return seasonA - seasonB;
                    const episodeA = a._episodeNumber || 0;
                    const episodeB = b._episodeNumber || 0;
                    return episodeA - episodeB;
                });
            }
        }

        const normalizedPlaySources = playSources.map((source) => ({
            name: source.name,
            episodes: (source.episodes || []).map((ep) => ({
                name: ep.name,
                playId: ep.playId,
            })),
        }));

        const finalTitle = scrapeData?.title || title;
        const finalPic = scrapeData?.posterPath ? `https://image.tmdb.org/t/p/w500${scrapeData.posterPath}` : vodPic;
        const finalYear = scrapeData?.releaseDate ? String(scrapeData.releaseDate).substring(0, 4) : findInfo('年份');
        const finalActor = (scrapeData?.credits?.cast || []).slice(0, 5).map((c) => c?.name).filter(Boolean).join(',') || findInfo('主演');
        const finalDirector =
            (scrapeData?.credits?.crew || [])
                .filter((c) => c?.job === 'Director' || c?.department === 'Directing')
                .slice(0, 3)
                .map((c) => c?.name)
                .filter(Boolean)
                .join(',') || findInfo('导演');
        const finalContent = scrapeData?.overview || $('.detail-content').text().trim() || $('.detail-sketch').text().trim() || '';

        return {
            list: [{
                vod_id: videoId,
                vod_name: finalTitle,
                vod_pic: finalPic,
                vod_type: findInfo('类型'),
                vod_year: finalYear,
                vod_area: findInfo('地区'),
                vod_actor: finalActor,
                vod_director: finalDirector,
                vod_remarks: findInfo('更新'),
                vod_lang: '中文字幕',
                vod_content: finalContent,
                vod_play_sources: normalizedPlaySources, // 关键:荐片架构必须返回此数组
            }]
        };
    } catch (e) {
        logError("详情获取失败", e);
        return { list: [] };
    }
}

async function search(params) {
    const wd = params.keyword || params.wd || "";
    const pg = parseInt(params.page) || 1;
    logInfo(`搜索关键词: ${wd}, 页码: ${pg}`);

    try {
        const url = `${host}/index.php/vod/search/page/${pg}/wd/${encodeURIComponent(wd)}.html`;
        const res = await axiosInstance.get(url, { headers: def_headers });
        const $ = cheerio.load(res.data);
        const list = parseVideoList($);

        logInfo("搜索返回数据", { count: list.length });

        return {
            list: list,
            page: pg,
            pagecount: pg // 简化处理
        };
    } catch (e) {
        logError("搜索失败", e);
        return { list: [], page: pg, pagecount: 0 };
    }
}

async function play(params) {
    const rawPlayId = params.playId;
    logInfo(`准备播放 ID: ${rawPlayId}`);

    let playId = rawPlayId || '';
    let playMeta = {};
    if (playId.includes('|||')) {
        const [mainPlayId, metaB64] = playId.split('|||');
        playId = mainPlayId || '';
        playMeta = decodeMeta(metaB64 || '');
    }

    try {
        const videoIdFromParam = params.vodId ? String(params.vodId) : '';
        const videoIdFromMeta = playMeta?.sid ? String(playMeta.sid) : '';
        const videoIdForScrape = videoIdFromParam || videoIdFromMeta;
        const sourceId = videoIdForScrape
            ? `spider_source_${await OmniBox.getSourceId()}_${videoIdForScrape}`
            : '';
        if (sourceId) {
            await OmniBox.getScrapeMetadata(sourceId);
        }
    } catch (error) {
        logInfo(`读取刮削元数据失败: ${error.message}`);
    }

    const finalUrl = playId;
    logInfo(`最终播放地址: ${finalUrl}`);

    return {
        urls: [{ name: "在线播放", url: finalUrl }],
        parse: 1, // 需要解析
        header: { ...def_headers, 'referer': host }
    };
}

module.exports = { home, category, search, detail, play };

const runner = require("spider_runner");
runner.run(module.exports);
