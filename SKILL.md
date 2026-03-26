---
name: content-collector
description: >
  Collect social media content (X/Twitter, WeChat, Jike, Reddit, etc.) into Feishu bitable.
  **Use this skill whenever the user shares a link from any social platform, sends a screenshot,
  or mentions "收藏", "保存", "collect", "save this article".** Even if they don't explicitly
  ask to collect, trigger this skill proactively.
---

# Content Collector

Auto-collect social media content → AI summarize → Save to Feishu bitable.

## Quick Reference

| Trigger | Action |
|---------|--------|
| X/Twitter link | `x-tweet-fetcher` skill |
| WeChat article | `web-content-fetcher` (Scrapling) |
| Other platforms | `defuddle` → fallback to `baoyu-url-to-markdown` |
| Screenshot | OCR → extract URL → collect |

## Workflow

```
Link/Screenshot → Platform Detect → Dedupe → Extract → Summarize → Save to Bitable
```

### Step 1: Platform Detection

```bash
python3 scripts/extract_content.py "<url>"
```

Returns: `platform_id`, `skill` to use, `fallback_skills`, CSS `selectors`.

See `references/platforms.md` for full platform mapping.

### Step 2: Deduplication

```bash
python3 scripts/deduplicate.py "<url>"           # Check if exists
python3 scripts/deduplicate.py --add "<url>"     # Add to cache after saving
```

### Step 3: Extract Content

Call the skill returned by Step 1:

- **X/Twitter**: Use `x-tweet-fetcher` skill
- **WeChat**: Use `web-content-fetcher` skill (Scrapling)
- **Others**: Use `defuddle` skill

### Step 4: AI Summarize + 独立标签生成（v2.0）

> **2026-03-21 更新**：采用独立生成模式，不再依赖历史标签池

**核心原则**：
- **独立生成**：只根据当前文章内容生成标签，不参考历史标签
- **固定结构**：对象(2) + 场景(1) + 类型(1) + 方法(1) = 5个标签
- **格式规范**：英文小写+中线连接，中文简洁短语

---

#### 4.1 提取文章内容

从 Step 3 获取的文章内容（标题、正文、来源等）

---

#### 4.2 调用模型生成 5 个标签

**Prompt 模板**：
```
请阅读以下内容，并严格按照"对象、场景、类型、方法"四类标签体系输出 5 个标签。

【标签体系】
- 对象（2个）：内容涉及的核心主体/技术/工具，如 openclaude、agent、mcp、prompt、浏览器自动化、记忆系统、量化交易、学习资源、实战案例、产品思考
- 场景（1个）：内容应用的实际场景/用途，如 投资分析、自动化测试、知识管理、代码生成
- 类型（1个）：内容的表现形式，如 技术教程、实战案例、产品分析、工具推荐、观点分享
- 方法（1个）：内容涉及的方法论/技巧，如 工作流、评测、prompt优化、架构设计

【规则】
1. 对象 2 个，场景 1 个，类型 1 个，方法 1 个，共 5 个
2. 不参考历史标签，只根据当前文章内容生成
3. 英文标签小写，多个单词用 `-` 连接（如 claude-code）
4. 中文标签使用简洁固定短语（如 投资分析、技术教程）
5. 不输出空泛标签，如 AI、工具、技术、效率
6. 只输出 JSON，不输出解释

【输出格式】
{
  "tags": {
    "对象": ["标签1", "标签2"],
    "场景": ["标签3"],
    "类型": ["标签4"],
    "方法": ["标签5"]
  }
}

【内容】
{文章内容}
```

---

#### 4.3 标签规范化

对模型输出的标签进行规范化处理：

```python
def normalize_tag(tag):
    # 1. 去掉首尾空格
    tag = tag.strip()
    
    # 2. 英文转小写
    tag = tag.lower()
    
    # 3. 英文多个单词用 `-` 连接
    # 如 "Claude Code" -> "claude-code"
    if ' ' in tag and tag.replace(' ', '').isalpha():
        tag = '-'.join(tag.split())
    
    # 4. 去重（同一类别内）
    return tag
```

---

#### 4.4 标签校验

校验规范化后的标签结构：

```python
def validate_tags(tags):
    """
    校验规则：
    - 对象恰好 2 个
    - 场景恰好 1 个
    - 类型恰好 1 个
    - 方法恰好 1 个
    - 总数恰好 5 个
    - 标签无重复（跨类别也检查）
    """
    errors = []
    
    # 检查各类别数量
    if len(tags.get("对象", [])) != 2:
        errors.append(f"对象需要 2 个，当前 {len(tags.get('对象', []))} 个")
    if len(tags.get("场景", [])) != 1:
        errors.append(f"场景需要 1 个，当前 {len(tags.get('场景', []))} 个")
    if len(tags.get("类型", [])) != 1:
        errors.append(f"类型需要 1 个，当前 {len(tags.get('类型', []))} 个")
    if len(tags.get("方法", [])) != 1:
        errors.append(f"方法需要 1 个，当前 {len(tags.get('方法', []))} 个")
    
    # 检查总数
    total = sum(len(v) for v in tags.values())
    if total != 5:
        errors.append(f"标签总数需要 5 个，当前 {total} 个")
    
    # 检查重复（跨类别）
    all_tags = []
    for v in tags.values():
        all_tags.extend(v)
    if len(all_tags) != len(set(all_tags)):
        errors.append("存在重复标签")
    
    return errors
```

**重试机制**：如果校验失败，允许模型重试一次

---

#### 4.5 写入飞书

将最终 5 个标签写入飞书多维表格（扁平化为字符串数组）：

```
feishu_bitable_app_table_record(
  action="create",
  app_token="ND8ObCuSya5Dv3sREZYc03Ilngh",
  table_id="tblaHDM5kjtikIl9",
  fields={
    "标签": ["openclaude", "agent", "投资分析", "实战案例", "工作流"]
  }
)
```

---

### 完整流程（v2.0）

```
1. 提取文章内容（Step 3）
      ↓
2. 调用模型生成 5 个标签（固定结构）
      ↓
3. 规范化标签（小写、去空格、连字符）
      ↓
4. 校验标签结构（对象2 + 场景1 + 类型1 + 方法1）
      ↓
5. 写入飞书
```

---

#### 4.6 标签体系参考（仅供模型参考，不参与匹配）

| 类别 | 标签示例 |
|------|----------|
| 对象 | openclaude, agent, mcp, prompt, 浏览器自动化, 记忆系统, 量化交易, claude-code, 工作流, 评测 |
| 场景 | 投资分析, 自动化测试, 知识管理, 代码生成, 数据处理, 对话系统, 内容创作 |
| 类型 | 技术教程, 实战案例, 产品分析, 工具推荐, 观点分享, 行业洞察 |
| 方法 | 工作流, 评测, prompt优化, 架构设计, 性能优化, 安全加固 |

**注意**：本方案不再使用历史标签池、不做模糊匹配、语义近似匹配或旧标签吸附
- [ ] 数量 ≤ 5
- [ ] 使用了已有池中的标签或已自动创建

### Step 5: Save to Feishu Bitable

**Required fields**:
- `标题` - 文章标题
- `来源` - 来源平台（X/Twitter, 微信公众号等）
- `分类` - 内容分类（🔧工具推荐/📖技术教程/🛠️实战案例/💡产品想法）
- `摘要内容` - AI生成的内容摘要
- `原文链接` - 原始URL（URL类型）
- `原文文件` - 飞书云空间文件链接（URL类型）
- `标签` - 5个标签数组

**Complete flow (v1.5+)**:

1. **Extract content** using platform-specific skill (x-tweet-fetcher, web-content-fetcher, etc.)
2. **Generate summary** - AI summarize the content
3. **Generate tags** - 5 tags (对象2 + 场景1 + 类型1 + 方法1)
4. **Save as local `.md` file** - Full content preserved
5. **Upload to Feishu Drive** - Get file URL for `原文文件`
6. **Write to bitable** with both URLs:
   ```python
   feishu_bitable_app_table_record(
     action="create",
     app_token="...",
     table_id="...",
     fields={
       "标题": "文章标题",
       "来源": "X/Twitter",
       "分类": "🛠️实战案例",
       "摘要内容": "AI生成的摘要...",
       "原文链接": {"text": "查看原文", "link": "https://x.com/i/status/..."},
       "原文文件": {"text": "查看完整内容", "link": "https://my.feishu.cn/file/..."},
       "标签": ["tag1", "tag2", "tag3", "tag4", "tag5"]
     }
   )
   ```
7. **Update dedupe cache**
   ```bash
   python3 scripts/deduplicate.py --add "<url>"
   ```

**Important**: Always save BOTH `原文链接` (original URL) and `原文文件` (Feishu Drive backup). This ensures content remains accessible even if the original link becomes unavailable.

**Bitable config**: See `references/feishu_config.md` or use environment variables:
- `FEISHU_BITABLE_APP_TOKEN`
- `FEISHU_BITABLE_TABLE_ID`

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract_content.py` | Platform detection + skill routing |
| `scripts/deduplicate.py` | URL deduplication (cache + document check) |
| `scripts/append_to_feishu.py` | Format content for Feishu doc (backup) |
| `scripts/ocr_image.py` | OCR for screenshots (optional) |

## Dependencies

### Required Skills
- `feishu-doc` / `feishu-bitable` - Read/write Feishu
- `defuddle` - Generic web extraction

### Platform-Specific (install as needed)
- `x-tweet-fetcher` - X/Twitter
- `web-content-fetcher` - WeChat (Scrapling)
- `baoyu-url-to-markdown` - Fallback

### Optional
- `pytesseract` + `tesseract-ocr` - Local OCR

## Configuration

Set via environment variables or see `references/feishu_config.md`:

```bash
export FEISHU_BITABLE_APP_TOKEN="your_app_token"
export FEISHU_BITABLE_TABLE_ID="your_table_id"
```

## References

- `references/platforms.md` - Full platform mapping and selectors
- `references/feishu_config.md` - Feishu bitable configuration
- `references/tagging_spec.md` - **⚠️ 已停用（见 Step 4 v2.0）**