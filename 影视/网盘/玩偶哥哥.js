// @name 玩偶系模板
// 引入 OmniBox SDK
const OmniBox = require("omnibox_sdk");

// 引入 cheerio（用于 HTML 解析）
// 注意：cheerio 需要在全局 node_modules 中安装
// 安装方法：在项目根目录执行 npm install cheerio（会安装到 data/spiders/node_modules）
// 或者通过环境变量 NODE_PATH 指定包含 cheerio 的目录
let cheerio;
try {
  cheerio = require("cheerio");
} catch (error) {
  throw new Error("cheerio 模块未找到，请先安装：npm install cheerio");
}

// ==================== 配置区域 ====================
// 网站地址（可以通过环境变量配置）
const WEB_SITE = process.env.WEB_SITE_WOGG || "";

/**
 * 筛选配置
 */
const FILTERS = {
  "1": [{
    "key": "class",
    "name": "剧情",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "喜剧",
      "value": "喜剧"
    }, {
      "name": "爱情",
      "value": "爱情"
    }, {
      "name": "恐怖",
      "value": "恐怖"
    }, {
      "name": "动作",
      "value": "动作"
    }, {
      "name": "科幻",
      "value": "科幻"
    }, {
      "name": "剧情",
      "value": "剧情"
    }, {
      "name": "战争",
      "value": "战争"
    }, {
      "name": "警匪",
      "value": "警匪"
    }, {
      "name": "犯罪",
      "value": "犯罪"
    }, {
      "name": "古装",
      "value": "古装"
    }, {
      "name": "奇幻",
      "value": "奇幻"
    }, {
      "name": "武侠",
      "value": "武侠"
    }, {
      "name": "冒险",
      "value": "冒险"
    }, {
      "name": "枪战",
      "value": "枪战"
    }, {
      "name": "悬疑",
      "value": "悬疑"
    }, {
      "name": "惊悚",
      "value": "惊悚"
    }, {
      "name": "经典",
      "value": "经典"
    }, {
      "name": "青春",
      "value": "青春"
    }, {
      "name": "文艺",
      "value": "文艺"
    }, {
      "name": "微电影",
      "value": "微电影"
    }, {
      "name": "历史",
      "value": "历史"
    }]
  }, {
    "key": "area",
    "name": "地区",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "中国大陆",
      "value": "中国大陆"
    }, {
      "name": "中国香港",
      "value": "中国香港"
    }, {
      "name": "中国台湾",
      "value": "中国台湾"
    }, {
      "name": "美国",
      "value": "美国"
    }, {
      "name": "西班牙",
      "value": "西班牙"
    }, {
      "name": "法国",
      "value": "法国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "日本",
      "value": "日本"
    }, {
      "name": "韩国",
      "value": "韩国"
    }, {
      "name": "泰国",
      "value": "泰国"
    }, {
      "name": "德国",
      "value": "德国"
    }, {
      "name": "印度",
      "value": "印度"
    }, {
      "name": "意大利",
      "value": "意大利"
    }, {
      "name": "加拿大",
      "value": "加拿大"
    }, {
      "name": "其他",
      "value": "其他"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "2": [{
    "key": "class",
    "name": "剧情",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "喜剧",
      "value": "喜剧"
    }, {
      "name": "爱情",
      "value": "爱情"
    }, {
      "name": "恐怖",
      "value": "恐怖"
    }, {
      "name": "动作",
      "value": "动作"
    }, {
      "name": "科幻",
      "value": "科幻"
    }, {
      "name": "剧情",
      "value": "剧情"
    }, {
      "name": "战争",
      "value": "战争"
    }, {
      "name": "警匪",
      "value": "警匪"
    }, {
      "name": "犯罪",
      "value": "犯罪"
    }, {
      "name": "古装",
      "value": "古装"
    }, {
      "name": "奇幻",
      "value": "奇幻"
    }, {
      "name": "武侠",
      "value": "武侠"
    }, {
      "name": "冒险",
      "value": "冒险"
    }, {
      "name": "枪战",
      "value": "枪战"
    }, {
      "name": "悬疑",
      "value": "悬疑"
    }, {
      "name": "惊悚",
      "value": "惊悚"
    }, {
      "name": "经典",
      "value": "经典"
    }, {
      "name": "青春",
      "value": "青春"
    }, {
      "name": "文艺",
      "value": "文艺"
    }, {
      "name": "微电影",
      "value": "微电影"
    }, {
      "name": "历史",
      "value": "历史"
    }]
  }, {
    "key": "area",
    "name": "地区",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "中国大陆",
      "value": "中国大陆"
    }, {
      "name": "中国香港",
      "value": "中国香港"
    }, {
      "name": "中国台湾",
      "value": "中国台湾"
    }, {
      "name": "美国",
      "value": "美国"
    }, {
      "name": "西班牙",
      "value": "西班牙"
    }, {
      "name": "法国",
      "value": "法国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "日本",
      "value": "日本"
    }, {
      "name": "韩国",
      "value": "韩国"
    }, {
      "name": "泰国",
      "value": "泰国"
    }, {
      "name": "德国",
      "value": "德国"
    }, {
      "name": "印度",
      "value": "印度"
    }, {
      "name": "意大利",
      "value": "意大利"
    }, {
      "name": "加拿大",
      "value": "加拿大"
    }, {
      "name": "其他",
      "value": "其他"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "44": [{
    "key": "class",
    "name": "剧情",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "喜剧",
      "value": "喜剧"
    }, {
      "name": "爱情",
      "value": "爱情"
    }, {
      "name": "恐怖",
      "value": "恐怖"
    }, {
      "name": "动作",
      "value": "动作"
    }, {
      "name": "科幻",
      "value": "科幻"
    }, {
      "name": "剧情",
      "value": "剧情"
    }, {
      "name": "战争",
      "value": "战争"
    }, {
      "name": "警匪",
      "value": "警匪"
    }, {
      "name": "犯罪",
      "value": "犯罪"
    }, {
      "name": "古装",
      "value": "古装"
    }, {
      "name": "奇幻",
      "value": "奇幻"
    }, {
      "name": "武侠",
      "value": "武侠"
    }, {
      "name": "冒险",
      "value": "冒险"
    }, {
      "name": "枪战",
      "value": "枪战"
    }, {
      "name": "悬疑",
      "value": "悬疑"
    }, {
      "name": "惊悚",
      "value": "惊悚"
    }, {
      "name": "经典",
      "value": "经典"
    }, {
      "name": "青春",
      "value": "青春"
    }, {
      "name": "文艺",
      "value": "文艺"
    }, {
      "name": "微电影",
      "value": "微电影"
    }, {
      "name": "历史",
      "value": "历史"
    }]
  }, {
    "key": "area",
    "name": "地区",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "中国大陆",
      "value": "中国大陆"
    }, {
      "name": "中国香港",
      "value": "中国香港"
    }, {
      "name": "中国台湾",
      "value": "中国台湾"
    }, {
      "name": "美国",
      "value": "美国"
    }, {
      "name": "西班牙",
      "value": "西班牙"
    }, {
      "name": "法国",
      "value": "法国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "日本",
      "value": "日本"
    }, {
      "name": "韩国",
      "value": "韩国"
    }, {
      "name": "泰国",
      "value": "泰国"
    }, {
      "name": "德国",
      "value": "德国"
    }, {
      "name": "印度",
      "value": "印度"
    }, {
      "name": "意大利",
      "value": "意大利"
    }, {
      "name": "加拿大",
      "value": "加拿大"
    }, {
      "name": "其他",
      "value": "其他"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "6": [{
    "key": "class",
    "name": "剧情",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "男频",
      "value": "男频"
    }, {
      "name": "女频",
      "value": "女频"
    }, {
      "name": "都市",
      "value": "都市"
    }, {
      "name": "甜宠",
      "value": "甜宠"
    }, {
      "name": "年代",
      "value": "年代"
    }, {
      "name": "穿越",
      "value": "穿越"
    }, {
      "name": "古装",
      "value": "古装"
    }, {
      "name": "亲情",
      "value": "亲情"
    }, {
      "name": "奇幻",
      "value": "奇幻"
    }, {
      "name": "萌宝",
      "value": "萌宝"
    }, {
      "name": "重生",
      "value": "重生"
    }, {
      "name": "冒险",
      "value": "冒险"
    }, {
      "name": "逆袭",
      "value": "逆袭"
    }, {
      "name": "虐恋",
      "value": "虐恋"
    }, {
      "name": "鉴宝",
      "value": "鉴宝"
    }, {
      "name": "复仇",
      "value": "复仇"
    }, {
      "name": "修仙",
      "value": "修仙"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "3": [{
    "key": "class",
    "name": "剧情",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "情感",
      "value": "情感"
    }, {
      "name": "科幻",
      "value": "科幻"
    }, {
      "name": "热血",
      "value": "热血"
    }, {
      "name": "推理",
      "value": "推理"
    }, {
      "name": "搞笑",
      "value": "搞笑"
    }, {
      "name": "冒险",
      "value": "冒险"
    }, {
      "name": "萝莉",
      "value": "萝莉"
    }, {
      "name": "校园",
      "value": "校园"
    }, {
      "name": "动作",
      "value": "动作"
    }, {
      "name": "机战",
      "value": "机战"
    }, {
      "name": "运动",
      "value": "运动"
    }, {
      "name": "战争",
      "value": "战争"
    }, {
      "name": "少年",
      "value": "少年"
    }, {
      "name": "少女",
      "value": "少女"
    }, {
      "name": "社会",
      "value": "社会"
    }, {
      "name": "原创",
      "value": "原创"
    }, {
      "name": "亲子",
      "value": "亲子"
    }, {
      "name": "益智",
      "value": "益智"
    }, {
      "name": "励志",
      "value": "励志"
    }, {
      "name": "其他",
      "value": "其他"
    }]
  }, {
    "key": "area",
    "name": "地区",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "中国大陆",
      "value": "中国大陆"
    }, {
      "name": "日本",
      "value": "日本"
    }, {
      "name": "美国",
      "value": "美国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "西班牙",
      "value": "西班牙"
    }, {
      "name": "法国",
      "value": "法国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "其他",
      "value": "其他"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "4": [{
    "key": "area",
    "name": "地区",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "中国大陆",
      "value": "中国大陆"
    }, {
      "name": "中国台湾",
      "value": "中国台湾"
    }, {
      "name": "美国",
      "value": "美国"
    }, {
      "name": "法国",
      "value": "法国"
    }, {
      "name": "英国",
      "value": "英国"
    }, {
      "name": "日本",
      "value": "日本"
    }, {
      "name": "韩国",
      "value": "韩国"
    }]
  }, {
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "46": [{
    "key": "year",
    "name": "时间",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "2026",
      "value": "2026"
    }, {
      "name": "2025",
      "value": "2025"
    }, {
      "name": "2024",
      "value": "2024"
    }, {
      "name": "2023",
      "value": "2023"
    }, {
      "name": "2022",
      "value": "2022"
    }, {
      "name": "2021",
      "value": "2021"
    }, {
      "name": "2020",
      "value": "2020"
    }, {
      "name": "2019",
      "value": "2019"
    }, {
      "name": "2018",
      "value": "2018"
    }, {
      "name": "2017",
      "value": "2017"
    }, {
      "name": "2016",
      "value": "2016"
    }, {
      "name": "2015",
      "value": "2015"
    }, {
      "name": "2014",
      "value": "2014"
    }, {
      "name": "2013",
      "value": "2013"
    }, {
      "name": "2012",
      "value": "2012"
    }, {
      "name": "2011",
      "value": "2011"
    }, {
      "name": "2010",
      "value": "2010"
    }]
  }, {
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }],
  "5": [{
    "key": "letter",
    "name": "字母",
    "init": "",
    "value": [{
      "name": "全部",
      "value": ""
    }, {
      "name": "A",
      "value": "A"
    }, {
      "name": "B",
      "value": "B"
    }, {
      "name": "C",
      "value": "C"
    }, {
      "name": "D",
      "value": "D"
    }, {
      "name": "E",
      "value": "E"
    }, {
      "name": "F",
      "value": "F"
    }, {
      "name": "G",
      "value": "G"
    }, {
      "name": "H",
      "value": "H"
    }, {
      "name": "I",
      "value": "I"
    }, {
      "name": "J",
      "value": "J"
    }, {
      "name": "K",
      "value": "K"
    }, {
      "name": "L",
      "value": "L"
    }, {
      "name": "M",
      "value": "M"
    }, {
      "name": "N",
      "value": "N"
    }, {
      "name": "O",
      "value": "O"
    }, {
      "name": "P",
      "value": "P"
    }, {
      "name": "Q",
      "value": "Q"
    }, {
      "name": "R",
      "value": "R"
    }, {
      "name": "S",
      "value": "S"
    }, {
      "name": "T",
      "value": "T"
    }, {
      "name": "U",
      "value": "U"
    }, {
      "name": "V",
      "value": "V"
    }, {
      "name": "W",
      "value": "W"
    }, {
      "name": "X",
      "value": "X"
    }, {
      "name": "Y",
      "value": "Y"
    }, {
      "name": "Z",
      "value": "Z"
    }, {
      "name": "0-9",
      "value": "0-9"
    }]
  }, {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [{
      "name": "默认",
      "value": ""
    }, {
      "name": "人气",
      "value": "hits"
    }, {
      "name": "评分",
      "value": "score"
    }]
  }]
}

// ==================== 配置区域结束 ====================

/**
 * 移除 URL 末尾的斜杠
 * @param {string} url - URL 字符串
 * @returns {string} 处理后的 URL
 */
function removeTrailingSlash(url) {
  if (!url) return "";
  return url.replace(/\/+$/, "");
}

/**
 * 判断是否为视频文件
 * @param {Object} file - 文件对象
 * @returns {boolean} 是否为视频文件
 */
function isVideoFile(file) {
  if (!file || !file.file_name) {
    return false;
  }

  const fileName = file.file_name.toLowerCase();
  const videoExtensions = [".mp4", ".mkv", ".avi", ".flv", ".mov", ".wmv", ".m3u8", ".ts", ".webm", ".m4v"];

  // 检查文件扩展名
  for (const ext of videoExtensions) {
    if (fileName.endsWith(ext)) {
      return true;
    }
  }

  // 检查format_type字段
  if (file.format_type) {
    const formatType = String(file.format_type).toLowerCase();
    if (formatType.includes("video") || formatType.includes("mpeg") || formatType.includes("h264")) {
      return true;
    }
  }

  return false;
}

/**
 * 递归获取所有视频文件（带错误收集）
 * @param {string} shareURL - 分享链接
 * @param {Array} files - 文件列表
 * @param {Array} errors - 错误收集数组（可选）
 * @returns {Promise<Array>} 所有视频文件列表
 */
async function getAllVideoFiles(shareURL, files, errors = []) {
  if (!files || !Array.isArray(files)) {
    return [];
  }

  const tasks = files.map(async (file) => {
    if (file.file && isVideoFile(file)) {
      return [file];
    } else if (file.dir) {
      try {
        const subFileList = await OmniBox.getDriveFileList(shareURL, file.fid);
        if (subFileList?.files && Array.isArray(subFileList.files)) {
          return await getAllVideoFiles(shareURL, subFileList.files, errors);
        }
        return [];
      } catch (error) {
        const errorInfo = {
          path: file.name || file.fid,
          fid: file.fid,
          message: error.message,
          timestamp: new Date().toISOString()
        };
        errors.push(errorInfo);
        OmniBox.log("warn", `获取子目录失败: ${JSON.stringify(errorInfo)}`);
        return [];
      }
    }
    return [];
  });

  const results = await Promise.all(tasks);
  return results.flat();
}

/**
 * 格式化文件大小，返回如 "1.65G" 的格式
 * @param {number} size - 文件大小（字节）
 * @returns {string} 格式化后的文件大小
 */
function formatFileSize(size) {
  if (!size || size <= 0) {
    return "";
  }

  const unit = 1024;
  const units = ["B", "K", "M", "G", "T", "P"];

  if (size < unit) {
    return `${size}B`;
  }

  let exp = 0;
  let sizeFloat = size;
  while (sizeFloat >= unit && exp < units.length - 1) {
    sizeFloat /= unit;
    exp++;
  }

  // 保留两位小数，但如果是整数则显示整数
  if (sizeFloat === Math.floor(sizeFloat)) {
    return `${Math.floor(sizeFloat)}${units[exp]}`;
  }
  return `${sizeFloat.toFixed(2)}${units[exp]}`;
}

/**
 * 获取首页数据
 * @param {Object} params - 参数对象
 * @returns {Object} 返回分类列表和推荐视频列表
 */
async function home(params) {
  try {
    OmniBox.log("info", "获取首页数据");

    let classes = [];
    let list = [];

    try {
      // 请求网站首页，从导航菜单中提取分类，同时提取首页影片列表
      const homeUrl = removeTrailingSlash(WEB_SITE);
      OmniBox.log("info", `请求首页URL: ${homeUrl}`);

      const response = await OmniBox.request(homeUrl, {
        method: "GET",
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
      });

      if (response.statusCode === 200 && response.body) {
        // 解析 HTML
        const $ = cheerio.load(response.body);

        // 从导航菜单中提取分类
        // 导航在 .module-tab-items 中，分类项是 .module-tab-item
        const tabItems = $(".module-tab-items .module-tab-item");

        tabItems.each((_, element) => {
          const $item = $(element);
          const typeId = $item.attr("data-id");
          const typeName = $item.attr("data-name");

          // 排除 data-id="0" 的"全部"项
          if (typeId && typeId !== "0" && typeName) {
            classes.push({
              type_id: typeId,
              type_name: typeName.trim(),
            });
            OmniBox.log("info", `提取分类: ${typeId} - ${typeName}`);
          }
        });

        OmniBox.log("info", `从首页导航提取到 ${classes.length} 个分类`);

        // 提取首页影片列表
        // 找到第一个 class="module" 的元素
        const firstModule = $(".module").first();

        if (firstModule.length > 0) {
          // 在这个 module 元素内找到所有 .module-item 元素
          const moduleItems = firstModule.find(".module-item");

          moduleItems.each((_, element) => {
            const $item = $(element);

            // 获取链接（从 .module-item-pic a 或 .module-item-title a）
            const href = $item.find(".module-item-pic a").attr("href") || $item.find(".module-item-title").attr("href");

            // 获取影片名称（优先从 img alt，其次从 .module-item-title title 或文本）
            const vodName = $item.find(".module-item-pic img").attr("alt") || $item.find(".module-item-title").attr("title") || $item.find(".module-item-title").text().trim();

            // 获取封面图片（优先 data-src，其次 src）
            const vodPic = $item.find(".module-item-pic img").attr("data-src") || $item.find(".module-item-pic img").attr("src");

            // 获取备注信息（更新状态）
            const vodRemarks = $item.find(".module-item-text").text().trim();

            // 获取年份（从 .module-item-caption 的第一个 span）
            const vodYear = $item.find(".module-item-caption span").first().text().trim();

            if (href && vodName) {
              list.push({
                vod_id: href,
                vod_name: vodName,
                vod_pic: vodPic || "",
                type_id: "",
                type_name: "",
                vod_remarks: vodRemarks || "",
                vod_year: vodYear || "",
              });
            }
          });

          OmniBox.log("info", `从首页提取到 ${list.length} 个影片`);
        } else {
          OmniBox.log("warn", "未找到 .module 元素");
        }
      } else {
        OmniBox.log("warn", `首页请求失败或响应体为空: HTTP ${response.statusCode}`);
      }
    } catch (error) {
      OmniBox.log("warn", `从首页提取数据失败: ${error.message}`);
      if (error.stack) {
        OmniBox.log("warn", `错误堆栈: ${error.stack}`);
      }
    }

    return {
      class: classes,
      list: list,
      filters: FILTERS,
    };
  } catch (error) {
    OmniBox.log("error", `获取首页数据失败: ${error.message}`);
  }
}

/**
 * 获取分类数据
 * @param {Object} params - 参数对象
 *   - categoryId: 分类ID（必填）
 *   - page: 页码（可选，默认1）
 * @returns {Object} 返回视频列表
 */
async function category(params) {
  try {
    const categoryId = params.categoryId || params.type_id || "";
    const page = parseInt(params.page || "1", 10);
    const filters = params.filters || {};

    OmniBox.log(params)

    OmniBox.log("info", `获取分类数据: categoryId=${categoryId}, page=${page}`);

    if (!categoryId) {
      OmniBox.log("warn", "分类ID为空");
      return {
        list: [],
        page: 1,
        pagecount: 0,
        total: 0,
      };
    }

    // 构建请求 URL（UZ 格式：/index.php/vod/show/id/{categoryId}/page/{page}.html）
    // https://wogg.333232.xyz/vodshow/2-----------.html
    // 
    const area = filters?.area || '';
    const sort = filters?.sort || '';
    const cls = filters?.class || '';
    const letter = filters?.letter || '';
    const year = filters?.year || '';

    const url = removeTrailingSlash(WEB_SITE) + `/vodshow/${categoryId}-${area}-${sort}-${cls}--${letter}---${page}---${year}.html`;

    OmniBox.log("info", `请求URL: ${url}`);

    // 发送请求
    const response = await OmniBox.request(url, {
      method: "GET",
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });

    if (response.statusCode !== 200) {
      OmniBox.log("error", `请求失败: HTTP ${response.statusCode}`);
      return {
        list: [],
        page: page,
        pagecount: 0,
        total: 0,
      };
    }

    if (!response.body) {
      OmniBox.log("warn", "响应体为空");
      return {
        list: [],
        page: page,
        pagecount: 0,
        total: 0,
      };
    }

    // 解析 HTML
    const $ = cheerio.load(response.body);
    const videos = [];

    const vodItems = $("#main .module-item");
    vodItems.each((_, e) => {
      const $item = $(e);
      const href = $item.find(".module-item-pic a").attr("href");
      const vodName = $item.find(".module-item-pic img").attr("alt");
      const vodPic = $item.find(".module-item-pic img").attr("data-src");
      const vodRemarks = $item.find(".module-item-text").text();
      const vodYear = $item.find(".module-item-caption span").first().text();

      if (href && vodName) {
        videos.push({
          vod_id: href,
          vod_name: vodName,
          vod_pic: vodPic || "",
          type_id: categoryId,
          type_name: "", // 分类名称可以从首页数据中获取
          vod_remarks: vodRemarks || "",
          vod_year: vodYear || "",
        });
      }
    });

    OmniBox.log("info", `解析完成，找到 ${videos.length} 个视频`);

    // 注意：这里无法获取总页数和总数，返回默认值
    return {
      list: videos,
      page: page,
      pagecount: 0, // 无法确定总页数
      total: videos.length,
    };
  } catch (error) {
    OmniBox.log("error", `获取分类数据失败: ${error.message}`);
    if (error.stack) {
      OmniBox.log("error", `错误堆栈: ${error.stack}`);
    }
    return {
      list: [],
      page: params.page || 1,
      pagecount: 0,
      total: 0,
    };
  }
}

/**
 * 获取视频详情
 * @param {Object} params - 参数对象
 *   - videoId: 视频ID（必填，即详情页的相对路径）
 * @returns {Object} 返回视频详情
 */
async function detail(params) {
  try {
    const videoId = params.videoId || "";

    if (!videoId) {
      throw new Error("视频ID不能为空");
    }

    // 获取来源参数（可选）
    const source = params.source || "";

    OmniBox.log("info", `获取视频详情: videoId=${videoId}, source=${source}`);

    // 构建完整 URL
    const webUrl = removeTrailingSlash(WEB_SITE) + videoId;

    OmniBox.log("info", `请求URL: ${webUrl}`);

    // 发送请求
    const response = await OmniBox.request(webUrl, {
      method: "GET",
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });

    if (response.statusCode !== 200) {
      throw new Error(`请求失败: HTTP ${response.statusCode}`);
    }

    if (!response.body) {
      throw new Error("响应体为空");
    }

    // 解析 HTML
    const $ = cheerio.load(response.body);

    // 获取基本信息
    const vodName = $(".page-title")[0]?.children?.[0]?.data || "";
    const vodPic = $($(".mobile-play")).find(".lazyload")[0]?.attribs?.["data-src"] || "";

    // 获取详细信息
    let vodYear = "";
    let vodDirector = "";
    let vodActor = "";
    let vodContent = "";

    const videoItems = $(".video-info-itemtitle");
    for (const item of videoItems) {
      const key = $(item).text();
      const vItems = $(item).next().find("a");
      const value = vItems
        .map((i, el) => {
          const text = $(el).text().trim();
          return text ? text : null;
        })
        .get()
        .filter(Boolean)
        .join(", ");

      if (key.includes("剧情")) {
        vodContent = $(item).next().find("p").text().trim();
      } else if (key.includes("导演")) {
        vodDirector = value.trim();
      } else if (key.includes("主演")) {
        vodActor = value.trim();
      }
    }

    // 获取网盘链接列表
    const panUrls = [];
    const items = $(".module-row-info");
    for (const item of items) {
      const shareUrl = $(item).find("p")[0]?.children?.[0]?.data;
      if (shareUrl) {
        panUrls.push(shareUrl.trim());
      }
    }

    OmniBox.log("info", `解析完成，找到 ${panUrls.length} 个网盘链接`);

    // 构建新格式的播放源(vod_play_sources)
    const playSources = [];

    // 先统计每种网盘类型的数量
    const driveTypeCountMap = {};
    for (const shareURL of panUrls) {
      const driveInfo = await OmniBox.getDriveInfoByShareURL(shareURL);
      const displayName = driveInfo.displayName || "未知网盘";
      driveTypeCountMap[displayName] = (driveTypeCountMap[displayName] || 0) + 1;
    }

    // 记录每种网盘类型当前的序号
    const driveTypeCurrentIndexMap = {};

    for (const shareURL of panUrls) {
      try {
        OmniBox.log("info", `处理网盘链接: ${shareURL}`);

        // 获取网盘信息
        const driveInfo = await OmniBox.getDriveInfoByShareURL(shareURL);
        let displayName = driveInfo.displayName || "未知网盘";

        // 如果该类型网盘有多个，给当前网盘添加序号
        const totalCount = driveTypeCountMap[displayName] || 0;
        if (totalCount > 1) {
          driveTypeCurrentIndexMap[displayName] = (driveTypeCurrentIndexMap[displayName] || 0) + 1;
          displayName = `${displayName}${driveTypeCurrentIndexMap[displayName]}`;
        }

        OmniBox.log("info", `网盘类型: ${displayName}, driveType: ${driveInfo.driveType}`);

        // 获取文件列表
        const fileList = await OmniBox.getDriveFileList(shareURL, "0");
        if (!fileList || !fileList.files || !Array.isArray(fileList.files)) {
          OmniBox.log("warn", `获取文件列表失败: ${shareURL}`);
          continue;
        }

        OmniBox.log("info", `获取文件列表成功,文件数量: ${fileList.files.length}`);

        // 递归获取所有视频文件
        const allVideoFiles = await getAllVideoFiles(shareURL, fileList.files, "0");

        if (allVideoFiles.length === 0) {
          OmniBox.log("warn", `未找到视频文件: ${shareURL}`);
          continue;
        }

        OmniBox.log("info", `递归获取视频文件完成,视频文件数量: ${allVideoFiles.length}`);

        // 确定播放源列表（线路） 
        let sourceNames = [displayName]; // 默认使用网盘名称
        if (driveInfo.driveType === "quark" || driveInfo.driveType === "uc") {
          // 夸克和UC网盘支持多线路
          sourceNames = ["本地代理", "服务端代理", "直连"];
          OmniBox.log("info", `${displayName}支持多线路: ${sourceNames.join(", ")}`);

          // 如果来源是网页端，过滤掉"本地代理"线路
          if (source === "web") {
            sourceNames = sourceNames.filter((name) => name !== "本地代理");
            OmniBox.log("info", `来源为网页端，已过滤掉"本地代理"线路`);
          }

          // const isIntranet = (url) => {
          //   try {
          //     const hostname = new URL(url).hostname;
          //     return hostname === 'localhost'
          //       || /^127\./.test(hostname)
          //       || /^10\./.test(hostname)
          //       || /^172\.(1[6-9]|2[0-9]|3[01])\./.test(hostname)
          //       || /^192\.168\./.test(hostname)
          //       || /^169\.254\./.test(hostname);
          //   } catch {
          //     return false;
          //   }
          // };
          // const baseUrl = process.env.OMNIBOX_BASE_URL;
          // OmniBox.log("info", `OMNIBOX_BASE_URL: ${baseUrl}`);

          // if (!isIntranet(baseUrl)) {
          //   sourceNames = sourceNames.filter((name) => name !== "服务端代理");
          //   OmniBox.log("info", `来源为外网，已过滤掉"服务端代理"线路`);
          // }
        }

        // 为每个线路构建剧集列表
        for (const sourceName of sourceNames) {
          const episodes = [];
          for (const file of allVideoFiles) {
            const fileName = file.file_name || "";
            const fileId = file.fid || "";
            const fileSize = file.size || file.file_size || 0;

            if (!fileName || !fileId) {
              continue;
            }

            // 格式化文件大小,在文件名前添加 [大小] 前缀
            let displayFileName = fileName;
            if (fileSize > 0) {
              const fileSizeStr = formatFileSize(fileSize);
              if (fileSizeStr) {
                displayFileName = `[${fileSizeStr}] ${fileName}`;
              }
            }

            // 构建剧集对象
            const episode = {
              name: displayFileName,
              playId: `${shareURL}|${fileId}`,
              size: fileSize > 0 ? fileSize : undefined,
            };

            episodes.push(episode);
          }

          if (episodes.length > 0) {
            // 如果是夸克/UC的多线路，使用 "网盘名-线路名" 作为播放源名称
            let finalSourceName = sourceName;
            if (driveInfo.driveType === "quark" || driveInfo.driveType === "uc") {
              finalSourceName = `${displayName}-${sourceName}`;
            }

            playSources.push({
              name: finalSourceName,
              episodes: episodes,
            });
          }
        }
      } catch (error) {
        OmniBox.log("error", `处理网盘链接失败: ${shareURL}, 错误: ${error.message}`);
        if (error.stack) {
          OmniBox.log("error", `错误堆栈: ${error.stack}`);
        }
      }
    }

    OmniBox.log("info", `构建播放源完成，网盘数量: ${playSources.length}`);

    // 构建视频详情对象
    const vodDetail = {
      vod_id: videoId,
      vod_name: vodName,
      vod_pic: vodPic,
      vod_year: vodYear,
      vod_director: vodDirector,
      vod_actor: vodActor,
      vod_content: vodContent || `网盘资源，共${panUrls.length}个网盘链接`,
      vod_play_sources: playSources.length > 0 ? playSources : undefined,
      vod_remarks: "",
    };

    return {
      list: [vodDetail],
    };
  } catch (error) {
    OmniBox.log("error", `获取视频详情失败: ${error.message}`);
    if (error.stack) {
      OmniBox.log("error", `错误堆栈: ${error.stack}`);
    }
    return {
      list: [],
    };
  }
}

/**
 * 搜索视频
 * @param {Object} params - 参数对象
 *   - keyword: 搜索关键词（必填）
 *   - page: 页码（可选，默认1）
 * @returns {Object} 返回搜索结果
 */
async function search(params) {
  try {
    const keyword = params.keyword || "";
    const page = parseInt(params.page || "1", 10);

    OmniBox.log("info", `搜索视频: keyword=${keyword}, page=${page}`);

    if (!keyword) {
      OmniBox.log("warn", "搜索关键词为空");
      return {
        list: [],
        page: 1,
        pagecount: 0,
        total: 0,
      };
    }

    // 构建搜索 URL（UZ 格式：/index.php/vod/search/page/{page}/wd/{keyword}.html）
    // https://wogg.333232.xyz/vodsearch/-------------.html?wd=%E6%88%90%E4%BD%95%E4%BD%93%E7%BB%9F
    const searchUrl = `${removeTrailingSlash(WEB_SITE)}/vodsearch/-------------.html?wd=${keyword}`;

    OmniBox.log("info", `请求URL: ${searchUrl}`);

    // 发送请求
    const response = await OmniBox.request(searchUrl, {
      method: "GET",
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });

    if (response.statusCode !== 200) {
      OmniBox.log("error", `请求失败: HTTP ${response.statusCode}`);
      return {
        list: [],
        page: page,
        pagecount: 0,
        total: 0,
      };
    }

    if (!response.body) {
      OmniBox.log("warn", "响应体为空");
      return {
        list: [],
        page: page,
        pagecount: 0,
        total: 0,
      };
    }

    // 解析 HTML
    const $ = cheerio.load(response.body);
    const videos = [];

    const items = $(".module-search-item");
    for (const item of items) {
      const $item = $(item);
      const videoSerial = $item.find(".video-serial")[0];
      const vodPicImg = $item.find(".module-item-pic > img")[0];

      if (videoSerial && videoSerial.attribs) {
        const vodId = videoSerial.attribs.href || "";
        const vodName = videoSerial.attribs.title || "";
        const vodPic = vodPicImg?.attribs?.["data-src"] || "";
        const vodRemarks = $($item.find(".video-serial")[0]).text() || "";

        if (vodId && vodName) {
          videos.push({
            vod_id: vodId,
            vod_name: vodName,
            vod_pic: vodPic,
            type_id: "",
            type_name: "",
            vod_remarks: vodRemarks,
          });
        }
      }
    }

    OmniBox.log("info", `搜索完成，找到 ${videos.length} 个结果`);

    return {
      list: videos,
      page: page,
      pagecount: 0, // 无法确定总页数
      total: videos.length,
    };
  } catch (error) {
    OmniBox.log("error", `搜索视频失败: ${error.message}`);
    if (error.stack) {
      OmniBox.log("error", `错误堆栈: ${error.stack}`);
    }
    return {
      list: [],
      page: params.page || 1,
      pagecount: 0,
      total: 0,
    };
  }
}

/**
 * 获取播放地址
 * @param {Object} params - 参数对象
 *   - flag: 播放源标识（可选，网盘名称）
 *   - playId: 播放地址ID（必填，格式：分享链接|文件ID）
 * @returns {Object} 返回播放地址信息
 *
 * 注意：playId 是从 detail 接口返回的 vod_play_url 中解析出来的
 * 格式：文件名$分享链接|文件ID，playId 就是 "分享链接|文件ID" 部分
 */
async function play(params) {
  try {
    const flag = params.flag || "";
    const playId = params.playId || "";

    OmniBox.log("info", `获取播放地址: flag=${flag}, playId=${playId}`);

    if (!playId) {
      throw new Error("播放参数不能为空");
    }

    // 解析playId：格式为 分享链接|文件ID
    const parts = playId.split("|");
    if (parts.length < 2) {
      throw new Error("播放参数格式错误，应为：分享链接|文件ID");
    }
    const shareURL = parts[0] || "";
    const fileId = parts[1] || "";

    if (!shareURL || !fileId) {
      throw new Error("分享链接或文件ID不能为空");
    }

    OmniBox.log("info", `解析参数: shareURL=${shareURL}, fileId=${fileId}`);

    // 获取刮削元数据，用于弹幕匹配（使用通用API）
    let danmakuList = [];
    try {
      // 使用新的通用元数据API，shareURL作为resourceId（网盘场景下，分享链接就是资源唯一标识）
      const metadata = await OmniBox.getScrapeMetadata(shareURL);
      if (metadata && metadata.scrapeData && metadata.videoMappings) {
        // 构建用于匹配映射关系的文件ID格式：{shareURL}|${fileId}
        const formattedFileId = fileId ? `${shareURL}|${fileId}` : "";

        // 根据文件ID查找对应的视频映射
        let matchedMapping = null;
        for (const mapping of metadata.videoMappings) {
          // 使用格式化后的文件ID进行匹配（因为刮削SDK返回的fileId是 {shareURL}|${fileId} 格式）
          if (mapping.fileId === formattedFileId) {
            matchedMapping = mapping;
            break;
          }
        }

        if (matchedMapping && metadata.scrapeData) {
          const scrapeData = metadata.scrapeData;
          OmniBox.log("info", `找到文件映射，fileId: ${formattedFileId}, tmdbEpisodeId: ${matchedMapping.tmdbEpisodeId || "N/A"}`);

          // 生成fileName用于弹幕匹配
          let fileName = "";
          const scrapeType = metadata.scrapeType || ""; // 从元数据获取类型（movie 或 tv）
          if (scrapeType === "movie") {
            // 电影直接用片名
            fileName = scrapeData.title || "";
          } else {
            // 电视剧根据集数生成：{Title}.{SeasonAirYear}.S{SeasonNumber}E{EpisodeNumber}
            const title = scrapeData.title || "";
            const seasonAirYear = scrapeData.seasonAirYear || "";
            const seasonNumber = matchedMapping.seasonNumber || 1;
            const episodeNumber = matchedMapping.episodeNumber || 1;
            fileName = `${title}.${seasonAirYear}.S${String(seasonNumber).padStart(2, "0")}E${String(episodeNumber).padStart(2, "0")}`;
          }

          if (fileName) {
            OmniBox.log("info", `生成fileName用于弹幕匹配: ${fileName}`);
            // 调用弹幕匹配API
            danmakuList = await OmniBox.getDanmakuByFileName(fileName);
            if (danmakuList && danmakuList.length > 0) {
              OmniBox.log("info", `弹幕匹配成功，找到 ${danmakuList.length} 条弹幕`);
            } else {
              OmniBox.log("info", "弹幕匹配未找到结果");
            }
          }
        } else {
          OmniBox.log("info", `未找到文件映射，fileId: ${fileId}`);
        }
      } else {
        OmniBox.log("info", "未找到刮削元数据，跳过弹幕匹配");
      }
    } catch (error) {
      OmniBox.log("warn", `弹幕匹配失败: ${error.message}`);
      // 弹幕匹配失败不影响播放，继续执行
    }

    // 从flag中提取线路类型
    // flag格式：夸克网盘1-本地代理
    let routeType = "服务端代理"; // 默认使用服务端代理
    if (flag && flag.includes("-")) {
      const parts = flag.split("-");
      routeType = parts[parts.length - 1]; // 取最后一部分作为线路类型
    }

    OmniBox.log("info", `使用线路: ${routeType}`);

    // 使用SDK获取播放信息
    const playInfo = await OmniBox.getDriveVideoPlayInfo(shareURL, fileId, routeType);

    if (!playInfo || !playInfo.url || !Array.isArray(playInfo.url) || playInfo.url.length === 0) {
      throw new Error("无法获取播放地址");
    }

    // 使用后端返回的url数组（格式：[{name: "RAW", url: "..."}, ...]）
    // 对于夸克和UC网盘，如果flag是"服务端代理"或"本地代理"，URL已经包含前缀
    const urlList = playInfo.url || [];

    // 统一使用数组格式，每个元素包含 name 和 url，类似 danmaku 格式
    // 直接使用后端返回的URL（已经根据flag处理过前缀）
    let urlsResult = [];
    for (const item of urlList) {
      urlsResult.push({
        name: item.name || "播放",
        url: item.url,
      });
    }

    let header = playInfo.header || {};

    // 合并弹幕列表：优先使用匹配到的弹幕，如果没有则使用playInfo中的弹幕
    let finalDanmakuList = danmakuList && danmakuList.length > 0 ? danmakuList : playInfo.danmaku || [];

    return {
      urls: urlsResult,
      flag: shareURL, // 返回网盘分享链接作为flag
      header: header,
      parse: 0,
      danmaku: finalDanmakuList,
    };
  } catch (error) {
    OmniBox.log("error", `播放接口失败: ${error.message}`);
    if (error.stack) {
      OmniBox.log("error", `错误堆栈: ${error.stack}`);
    }
    return {
      urls: [],
      flag: params.flag || "",
      header: {},
      danmaku: [],
    };
  }
}

// 导出接口（用于模块化引用）
module.exports = {
  home,
  category,
  search,
  detail,
  play,
};

// 使用公共 runner 处理标准输入/输出
// runner 通过 NODE_PATH 环境变量自动解析，无需手动指定路径
const runner = require("spider_runner");
runner.run(module.exports);
