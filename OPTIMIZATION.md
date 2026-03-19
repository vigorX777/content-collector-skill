# Content Collector 变更记录

> 记录所有版本变更、优化方向和待办事项。
>
> **状态说明**：✅ 已完成 | 🔄 部分完成 | ❌ 待处理
> **最后更新**：2026-03-19

---

## 版本历史

### v1.5.0 (2026-03-19)

**重大重构 — 基于 skill-creator 最佳实践**

- 🎉 **SKILL.md 精简**：从 270 行减少到 115 行（↓58%）
- 🎉 **新增 references/ 目录**：
  - `platforms.md` - 平台映射 + CSS selectors
  - `feishu_config.md` - 飞书配置详情
- 🔧 **移除硬编码 Token**：App Token 改为环境变量读取
- 🔧 **移除更新日志**：从 SKILL.md 移除，归入本文件
- 📝 **README 重写**：中文版 + 作者信息 + 演示图片
- 🖼️ **新增 assets/ 目录**：从公众号文章抓取配图

**文件变更**：
```
+ references/platforms.md (69 行)
+ references/feishu_config.md (58 行)
+ assets/cover.png, chat-demo.png, bitable-demo.png, workflow.png
+ .env.example
~ SKILL.md (270 → 115 行)
~ README.md (重写)
~ scripts/deduplicate.py (移除硬编码 token)
~ scripts/save_to_bitable.py (移除硬编码 token)
```

### v1.4.0 (2026-03-18)

**长文本优化**

- 🎉 原文上传飞书云空间，URL 字段存储链接
- ✅ 新增"原文文件"字段
- ✅ "原文内容"改名为"摘要内容"
- ✅ LLM 不再输出长文本，大幅节省 token
- ✅ 原文通过飞书文件链接跳转查看

### v1.3.0 (2026-03-17)

**微信公众号抓取能力升级**

- 🎉 改用 Scrapling 方案，完美绕过微信反爬
- 🔧 更新平台映射：微信公众号首选 web-content-fetcher skill
- 🔧 添加 scrapling_command 字段

### v1.2.0 (2026-03-14)

**架构重构**

- 🔧 移除所有硬编码路径，适配多环境部署
- 🔧 重写 extract_content.py 为平台检测 + skill 路由模式
- 🔧 删除空壳提取脚本，selector 信息内嵌到 extract_content.py
- 🔧 修复 type annotation 和 bare except 问题

### v1.1.0 (2026-03-14)

**去重机制**

- ✅ 添加去重机制（本地缓存 + 文档检查）
- ✅ 支持更多平台（即刻、公众号、Reddit）
- ✅ 添加图片 OCR 识别脚本
- ✅ 优化飞书文档格式

### v1.0.0 (2026-03-14)

- 初始版本
- 支持 X/Twitter、即刻、微信公众号

---

## 待办事项

### P0 — 必须修复

（无）

### P1 — 架构基础

| # | 状态 | 问题 | 建议 |
|---|------|------|------|
| 1 | ❌ | 缺少统一输出 Schema | 定义 `CollectedItem` JSON Schema，所有提取器统一输出 |
| 2 | 🔄 | Bitable 存储 | 已支持，但 App Token 需要环境变量配置 |
| 3 | ❌ | 无错误处理标准 | 统一错误输出格式 |

### P2 — 体验提升

| # | 状态 | 问题 | 建议 |
|---|------|------|------|
| 4 | ❌ | 无语义去重 | 同内容不同 URL，需要内容指纹 |
| 5 | ❌ | 缺少 thread/长文支持 | X thread、公众号多图文 |
| 6 | ❌ | 无批量导入 | 导入书签列表、收藏夹 |
| 7 | ❌ | 每日提醒只是通知 | 应带摘要、分类、推荐 |
| 8 | ❌ | 无测试 | URL 标准化、去重、平台检测的单元测试 |

### P3 — 生态联动

| # | 状态 | 问题 | 建议 |
|---|------|------|------|
| 9 | ❌ | 无"回流"加工 | 周报汇总、趋势发现、自动生成笔记 |
| 10 | ❌ | 无 skill 联动接口 | 标准化输出供其他 skill 消费 |

---

## 已完成事项

### 架构优化 ✅

- [x] 移除所有硬编码路径
- [x] 删除空壳提取脚本
- [x] SKILL.md 精简到 115 行
- [x] 新增 references/ 目录分层
- [x] App Token 改为环境变量

### 去重机制 ✅

- [x] 短链 resolve (t.co/bit.ly 等)
- [x] Domain alias 映射 (twitter→x.com 等)
- [x] 缓存 TTL 30天 + LRU 1000 条上限

### 内容提取 ✅

- [x] X/Twitter 使用 x-tweet-fetcher
- [x] 微信公众号使用 Scrapling
- [x] 移除 500 字截断

### 工程质量 ✅

- [x] 修复 bare except
- [x] 移除对不存在文件的引用
- [x] README 重写 + 配图

---

## 维护信息

**作者**: vigor  
**公众号**: 懂点儿AI  
**GitHub**: https://github.com/vigorX777/content-collector-skill  
**制作过程**: [从零打造 AI 内容收藏助手](https://mp.weixin.qq.com/s/hw4uKk-9ezaJlDpL1nEUuA)