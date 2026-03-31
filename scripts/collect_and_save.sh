#!/bin/bash
#
# 内容收藏完整流程脚本
# 强制使用 save_to_bitable.py，禁止直接调用工具
#
# 用法:
#   ./collect_and_save.sh \
#       --url "https://x.com/i/status/..." \
#       --title "文章标题" \
#       --source "X/Twitter" \
#       --category "🔧工具推荐"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENT_FILE="/tmp/collect_content_$$.md"

# 解析参数
URL=""
TITLE=""
SOURCE=""
CATEGORY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            URL="$2"
            shift 2
            ;;
        --title)
            TITLE="$2"
            shift 2
            ;;
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 参数校验
if [[ -z "$URL" || -z "$TITLE" || -z "$SOURCE" || -z "$CATEGORY" ]]; then
    echo "错误: 缺少必需参数"
    echo "用法: $0 --url <url> --title <title> --source <source> --category <category>"
    exit 1
fi

echo "📝 步骤 1: 提取内容..."
python3 "${SCRIPT_DIR}/extract_content.py" "$URL" > "$CONTENT_FILE"

if [[ ! -s "$CONTENT_FILE" ]]; then
    echo "❌ 内容提取失败"
    rm -f "$CONTENT_FILE"
    exit 1
fi

echo "✅ 内容已保存到 $CONTENT_FILE"

echo "📝 步骤 2: 调用 save_to_bitable.py 写入..."
python3 "${SCRIPT_DIR}/save_to_bitable.py" \
    --title "$TITLE" \
    --source "$SOURCE" \
    --category "$CATEGORY" \
    --url "$URL" \
    --content-file "$CONTENT_FILE"

SAVE_RESULT=$?

# 清理临时文件
rm -f "$CONTENT_FILE"

if [[ $SAVE_RESULT -eq 0 ]]; then
    echo "✅ 收藏完成"
    
    echo "📝 步骤 3: 更新去重缓存..."
    python3 "${SCRIPT_DIR}/deduplicate.py" --add "$URL"
    
    exit 0
else
    echo "❌ 保存失败"
    exit 1
fi
