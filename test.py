#!/usr/bin/env python3
"""
Content Collector Skill - 测试用例
验证优化功能是否正常工作
"""

import re
import json

# ============================================
# 测试 1: 触发词扩展
# ============================================
def test_trigger_words():
    """测试触发词检测"""
    
    # 扩展后的触发词列表
    trigger_words = [
        # 基础触发词
        "收录", "转存", "保存", "存档", "存一下", "归档", "备份", "收藏",
        "存到知识库", "加入知识库", "转飞书",
        # 扩展触发词
        "推荐", "mark", "mark 一下", "记一下",
        "转发", "整理", "标记",
        "值得收藏", "这个不错", "分享这个"
    ]
    
    test_cases = [
        ("这个链接收录一下", True),
        ("mark 一下这个", True),
        ("推荐这篇文章", True),
        ("转存到知识库", True),
        ("记一下这个", True),
        ("今天天气不错", False),  # 无触发词
        ("随便看看", False),    # 无触发词
    ]
    
    print("=" * 50)
    print("测试 1: 触发词扩展")
    print("=" * 50)
    
    for text, should_trigger in test_cases:
        # 检测是否包含触发词
        matched = any(word in text for word in trigger_words)
        status = "✅" if matched == should_trigger else "❌"
        print(f"{status} '{text}' -> 预期: {should_trigger}, 实际: {matched}")
    
    print()

# ============================================
# 测试 2: 批量链接提取
# ============================================
def test_batch_url_extraction():
    """测试批量 URL 提取"""
    
    test_cases = [
        ("https://x.com/1 收藏\nhttps://x.com/2 收藏", ["https://x.com/1", "https://x.com/2"]),
        ("https://a.com 测试 https://b.com 收藏", ["https://a.com", "https://b.com"]),
        ("只有一个链接 https://x.com", ["https://x.com"]),
        ("没有链接的内容", []),
    ]
    
    print("=" * 50)
    print("测试 2: 批量链接提取")
    print("=" * 50)
    
    for text, expected in test_cases:
        urls = re.findall(r'https?://[^\s]+', text)
        status = "✅" if urls == expected else "❌"
        print(f"{status} '{text[:30]}...'")
        print(f"   预期: {expected}")
        print(f"   实际: {urls}")
    
    print()

# ============================================
# 测试 3: 分类智能化
# ============================================
def test_auto_classification():
    """测试自动分类"""
    
    # 分类规则
    category_rules = {
        "📖 技术教程": ["prompt", "agent", "model", "LLM", "GPT", "训练", "微调", "RAG"],
        "💡 产品想法": ["产品", "功能", "需求", "用户体验", "UE", "UX", "竞品"],
        "🔧 工具推荐": ["工具", "软件", "app", "插件", "开源", "github"],
        "🔥 热点资讯": ["热点", "新闻", "事件", "今日", "最新"],
        "🛠️ 实战案例": ["案例", "实战", "项目", "经验", "分享"],
    }
    
    test_cases = [
        ("这篇prompt技巧教程太棒了", "📖 技术教程"),
        ("这个AI产品功能很有意思", "💡 产品想法"),
        ("推荐一个开源工具", "🔧 工具推荐"),
        ("今日热点新闻", "🔥 热点资讯"),
        ("实战项目经验分享", "🛠️ 实战案例"),
    ]
    
    print("=" * 50)
    print("测试 3: 分类智能化")
    print("=" * 50)
    
    for text, expected in test_cases:
        # 根据关键词匹配分类
        matched_category = None
        for category, keywords in category_rules.items():
            if any(kw in text for kw in keywords):
                matched_category = category
                break
        
        status = "✅" if matched_category == expected else "❌"
        print(f"{status} '{text}'")
        print(f"   预期: {expected}, 实际: {matched_category}")
    
    print()

# ============================================
# 测试 4: 多平台支持
# ============================================
def test_platform_detection():
    """测试平台检测"""
    
    platform_rules = [
        (r"x\.com|twitter\.com", "X/Twitter"),
        (r"mp\.weixin\.qq\.com", "微信公众号"),
        (r"feishu\.cn", "飞书"),
        (r"xiaohongshu\.com", "小红书"),
        (r"douyin\.com", "抖音/视频号"),
        (r"zhihu\.com", "知乎"),
        (r"juejin\.cn", "掘金"),
    ]
    
    test_cases = [
        ("https://x.com/i/status/123", "X/Twitter"),
        ("https://mp.weixin.qq.com/s/abc", "微信公众号"),
        ("https://feishu.cn/docx/xxx", "飞书"),
        ("https://xiaohongshu.com/discovery/xxx", "小红书"),
        ("https://www.douyin.com/video/123", "抖音/视频号"),
        ("https://zhuanlan.zhihu.com/p/123", "知乎"),
        ("https://juejin.cn/post/123", "掘金"),
        ("https://example.com/article", "通用网页"),
    ]
    
    print("=" * 50)
    print("测试 4: 多平台支持")
    print("=" * 50)
    
    for url, expected in test_cases:
        detected = "通用网页"
        for pattern, platform in platform_rules:
            if re.search(pattern, url):
                detected = platform
                break
        
        status = "✅" if detected == expected else "❌"
        print(f"{status} {url[:40]}...")
        print(f"   预期: {expected}, 实际: {detected}")
    
    print()

# ============================================
# 测试 5: 去重检测
# ============================================
def test_duplicate_detection():
    """测试去重逻辑"""
    
    # 模拟已收藏的链接
    existing_urls = [
        "https://x.com/i/status/123",
        "https://mp.weixin.qq.com/s/abc",
    ]
    
    test_cases = [
        ("https://x.com/i/status/123", True),   # 已存在
        ("https://new.com/article", False),     # 不存在
    ]
    
    print("=" * 50)
    print("测试 5: 去重检测")
    print("=" * 50)
    
    for url, should_duplicate in test_cases:
        is_duplicate = url in existing_urls
        status = "✅" if is_duplicate == should_duplicate else "❌"
        print(f"{status} {url}")
        print(f"   预期重复: {should_duplicate}, 实际: {is_duplicate}")
    
    print()

# ============================================
# 测试 6: 图片URL检测
# ============================================
def test_image_detection():
    """测试图片URL检测"""
    
    test_cases = [
        ("这是内容图片 https://example.com/img.jpg 结束了", ["https://example.com/img.jpg"]),
        ("文章包含 https://a.png 和 https://b.gif", ["https://a.png", "https://b.gif"]),
        ("纯文本内容没有图片", []),
    ]
    
    print("=" * 50)
    print("测试 6: 图片URL检测")
    print("=" * 50)
    
    # 图片URL正则
    image_pattern = r'https?://[^\s]+\.(jpg|jpeg|png|gif|webp)(?:\?[^\s]*)?'
    
    for text, expected in test_cases:
        images = re.findall(image_pattern, text, re.IGNORECASE)
        # 还原完整URL
        found_urls = re.findall(r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)(?:\?[^\s]*)?', text, re.IGNORECASE)
        
        status = "✅" if found_urls == expected else "❌"
        print(f"{status} '{text[:30]}...'")
        print(f"   预期: {expected}")
        print(f"   实际: {found_urls}")
    
    print()

# ============================================
# 运行所有测试
# ============================================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Content Collector Skill - 测试用例")
    print("=" * 50 + "\n")
    
    test_trigger_words()
    test_batch_url_extraction()
    test_auto_classification()
    test_platform_detection()
    test_duplicate_detection()
    test_image_detection()
    
    print("=" * 50)
    print("测试完成!")
    print("=" * 50)