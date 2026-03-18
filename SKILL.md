---
name: content-collector
description: "自动收集社交媒体内容（X/Twitter、即刻、公众号、Reddit 等）并整理成结构化笔记存入飞书多维表格。当用户发送链接或截图时使用此技能。"
version: "1.4.0"
---

# Content Collector - 社交内容收藏助手

自动收集社交媒体精彩内容，AI 整理后存入飞书文档。

## 触发条件

当用户发送以下内容时自动触发：
- **链接**：X/Twitter、即刻、微信公众号、Reddit、知乎、Bilibili、Hacker News 等
- **图片**：截图（OCR 识别后提取链接）
- **混合**：链接 + 截图

## 依赖的 Skill

> **重要**：本 skill 不直接调用外部脚本或路径，而是输出指引，由 Agent 在运行时调用对应 skill。
> 以下是当前环境中实际使用的 skill，请确保已安装。

### 必需 Skill

| Skill | 用途 | 安装位置 |
|:---|:---|:---|
| **feishu-doc** | 读写飞书文档（追加内容、读取已有内容做去重） | `~/.agents/skills/feishu-doc*` |
| **defuddle** | 通用网页正文提取（微信公众号、即刻、Reddit、知乎等） | `~/.opencode/skills/defuddle/` |

### 推荐 Skill（按平台）

| Skill | 用途 | 安装位置 |
|:---|:---|:---|
| **x-tweet-fetcher** | X/Twitter 推文、文章、时间线提取（零依赖 FxTwitter API） | `~/.opencode/skills/x-tweet-fetcher/` |
| **web-content-fetcher** | 微信公众号抓取（Scrapling 方案，完美绕过反爬） | `~/.openclaw/workspace/skills/web-content-fetcher/` |
| **baoyu-url-to-markdown** | 通用 URL 转 Markdown（fallback 方案） | `~/.opencode/skills/baoyu-url-to-markdown/` |

### 可选 Skill

| Skill | 用途 |
|:---|:---|
| **feishu-cron-reminder** | 每日定时提醒查看收藏内容 |
| **feishu-send-file** | 将收藏导出文件发送到飞书群 |

### 可选本地依赖

| 依赖 | 用途 | 安装方式 |
|:---|:---|:---|
| pytesseract + pillow | 本地图片 OCR | `pip install pytesseract pillow` |
| tesseract-ocr | OCR 引擎 | macOS: `brew install tesseract`; Linux: `apt-get install tesseract-ocr tesseract-ocr-chi-sim` |

## 工作流程

```
用户发送链接/图片
  → 平台检测 (extract_content.py)
  → 去重检查 (deduplicate.py)
  → Agent 调用对应 skill 提取内容
  → AI 整理成结构化格式
  → 格式化 (append_to_feishu.py)
  → Agent 调用 feishu-doc 追加到文档
```

### Step 1: 平台检测

运行 `extract_content.py` 检测链接来源，获取推荐的 skill 和提取方式：

```bash
python3 scripts/extract_content.py "https://x.com/user/status/123"
```

输出示例：
```json
{
  "platform_id": "twitter",
  "platform_label": "X/Twitter",
  "url": "https://x.com/user/status/123",
  "skill": "x-tweet-fetcher",
  "fallback_skills": [],
  "note": "使用 x-tweet-fetcher skill 提取推文/文章内容"
}
```

**支持的平台映射**：

| 平台 | 域名 | 首选 Skill | Fallback |
|:---|:---|:---|:---|
| X/Twitter | x.com, twitter.com | x-tweet-fetcher | — |
| 微信公众号 | mp.weixin.qq.com | **web-content-fetcher (Scrapling)** | defuddle |
| 即刻 | okjike.com, jike.cn | defuddle | baoyu-url-to-markdown |
| Reddit | reddit.com | defuddle | baoyu-url-to-markdown |
| Hacker News | news.ycombinator.com | defuddle | — |
| 知乎 | zhihu.com | defuddle | baoyu-url-to-markdown |
| Bilibili | bilibili.com, b23.tv | defuddle | baoyu-url-to-markdown |
| 其他 | * | defuddle | baoyu-url-to-markdown |

### Step 2: 去重检查

```bash
python3 scripts/deduplicate.py "https://x.com/user/status/123"
```

检查方式：
1. **本地缓存**：`.cache/collected_urls.json`
2. **文档检查**：传入飞书文档内容文件做匹配
3. **URL 标准化**：自动去除 utm_source、fbclid 等追踪参数

### Step 3: 内容提取

Agent 根据 Step 1 的输出，调用对应 skill 提取内容。例如：

- **X/Twitter**：调用 `x-tweet-fetcher` skill
- **微信公众号**：调用 `defuddle` skill
- **其他平台**：调用 `defuddle` 或 `baoyu-url-to-markdown` skill

> Agent 负责调用 skill，本 skill 的脚本只做检测和格式化，不直接调用外部 skill。

**平台特殊提示**（内嵌在 extract_content.py 的 selectors 字段中）：

- **微信公众号** CSS selectors：`#activity-name`（标题）、`#js_name`（作者）、`#js_content`（正文）、`#publish_time`（时间）
- **即刻** CSS selectors：`meta[property="og:title"]`（作者）、`meta[property="og:description"]`（内容）、`time`（时间）
- **Reddit**：支持 JSON API，在 URL 末尾加 `.json` 获取结构化数据

### Step 4: AI 整理

提取到原始内容后，AI 整理为结构化信息：

- **标题**：内容标题
- **来源**：作者/平台
- **分类**：按内容类型分类
- **摘要内容**：AI 生成的摘要，3-5 句话概括核心内容
- **原文链接**：原始链接
- **原文文件**：飞书云空间 .md 文件链接

### Step 5: 存入多维表格（推荐）

**优化后的流程**（v1.4.0）：

```
1. 抓取内容 → 保存为 .md 文件
2. 上传到飞书云空间 → 获取文件链接
3. LLM 只输出短字段（标题、来源、分类、摘要内容）
4. 写入多维表格，原文通过文件链接跳转
```

**Agent 工作流**：
1. 调用对应 skill 抓取内容
2. 保存为本地 `.md` 文件（如 `/tmp/content_{id}.md`）
3. 调用 `feishu_drive_file upload` 上传到云空间
4. 获取文件链接（如 `https://my.feishu.cn/file/xxx`）
5. 调用 `feishu_bitable_app_table_record` 写入多维表格

**优势**：
- ✅ 省钱：LLM 不输出长文本内容
- ✅ 稳定：文件内容完整，不会截断
- ✅ 可查看：飞书中直接打开 .md 文件
- ✅ 可搜索：摘要内容+标题可搜索

**字段结构**：

| 字段 | 类型 | 用途 |
|:---|:---|:---|
| 标题 | 文本 | 可搜索 |
| 来源 | 文本 | 可筛选 |
| 分类 | 单选 | 可筛选 |
| 原文链接 | 超链接 | 原始来源 |
| 摘要内容 | 文本 | AI 生成的摘要，可搜索 |
| 记录时间 | 创建时间 | 自动记录 |
| 原文文件 | 超链接 | 飞书云空间 .md 文件 |

**多维表格配置**：
- App Token: `ND8ObCuSya5Dv3sREZYc03Ilngh`
- Table ID: `tblaHDM5kjtikIl9`

### Step 5 (备用): 格式化为 Markdown 文档

如果需要存入普通飞书文档（非多维表格），使用：

```bash
python3 scripts/append_to_feishu.py '<json_content>'
```

输出为格式化的 Markdown，供 Agent 调用 feishu-doc 的 append 操作写入文档。

### Step 6: 图片 OCR（可选）

当用户发送截图而非链接时：

```bash
python3 scripts/ocr_image.py /path/to/image.png
```

- 如果本地安装了 pytesseract → 直接 OCR 识别
- 否则 → 返回图片路径，提示 Agent 使用外部 OCR 服务
- 识别后自动提取文本中的 URL，回到 Step 1

## 脚本清单

| 脚本 | 用途 | 是否直接可用 |
|:---|:---|:---|
| `scripts/extract_content.py` | 平台检测 + skill 路由 | ✅ 独立运行 |
| `scripts/deduplicate.py` | URL 去重（本地缓存 + 文档匹配） | ✅ 独立运行 |
| `scripts/append_to_feishu.py` | 内容格式化为飞书 Markdown（备用） | ✅ 独立运行 |
| `scripts/ocr_image.py` | 图片 OCR（需 pytesseract 或外部服务） | ⚠️ 需可选依赖 |

> **注意**：v1.4.0 后不再需要 `save_to_bitable.py`，改用飞书云空间上传方案。

## 去重机制

### URL 标准化

自动去除以下追踪参数：
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`
- `fbclid`, `gclid`
- `ref`, `source`

### 缓存存储

```
.cache/collected_urls.json
{
  "https://x.com/user/status/123": {
    "original_url": "https://x.com/...",
    "date": "2026-03-14T10:00:00",
    "metadata": {...}
  }
}
```

## 配置

**飞书文档 Token**：首次使用时创建文档，后续追加到同一文档。
文档标题建议：`社交内容收藏 - 每日精选`

**每日提醒**（可选，需 feishu-cron-reminder skill）：
每天 18:00 推送当日收藏数量、标题列表和文档链接。

## 更新日志

### v1.4.0 (2026-03-18)
- 🎉 **长文本优化**：原文上传到飞书云空间，用 URL 字段存储链接
- ✅ 新增"原文文件"字段，"原文内容"改名为"摘要内容"
- ✅ LLM 不再输出长文本，大幅节省 token
- ✅ 原文通过飞书文件链接跳转查看，支持 .md 格式

### v1.3.0 (2026-03-17)
- 🎉 **微信公众号抓取能力升级**：改用 Scrapling 方案，完美绕过微信反爬
- 🔧 更新平台映射：微信公众号首选 web-content-fetcher skill
- 🔧 添加 scrapling_command 字段，直接输出抓取命令

### v1.2.0 (2026-03-14)
- 🔧 移除所有硬编码路径，适配多环境部署
- 🔧 重写 extract_content.py 为平台检测 + skill 路由模式
- 🔧 删除空壳提取脚本（extract_jike/weixin/reddit.py），selector 信息内嵌到 extract_content.py
- 🔧 更新依赖声明为当前环境实际使用的 skill
- 🔧 修复 type annotation 和 bare except 问题

### v1.1.0 (2026-03-14)
- ✅ 添加去重机制（本地缓存 + 文档检查）
- ✅ 支持更多平台（即刻、公众号、Reddit 专用提取器）
- ✅ 添加图片 OCR 识别脚本
- ✅ 优化飞书文档格式（自动序号、互动数据格式化）

### v1.0.0 (2026-03-14)
- 初始版本
- 支持 X/Twitter、即刻、微信公众号
