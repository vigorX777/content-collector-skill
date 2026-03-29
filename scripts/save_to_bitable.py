#!/usr/bin/env python3
"""
保存内容到飞书多维表格

解决长文本写入问题：
- 短文本字段由 LLM 输出（标题、来源、分类、链接）
- 长文本字段通过文件路径传入（原文内容）
- 跳过 LLM 输出长文本的 token 消耗

使用方式：
    python3 save_to_bitable.py \
        --title "标题" \
        --source "来源" \
        --category "分类" \
        --url "https://..." \
        --content-file /path/to/content.md \
        [--app-token TOKEN] \
        [--table-id ID]

环境变量：
    FEISHU_USER_ACCESS_TOKEN: 用户访问令牌（必需）
    或通过 --token 参数传入

多维表格配置（默认值）：
    App Token: ND8ObCuSya5Dv3sREZYc03Ilngh
    Table ID: tblaHDM5kjtikIl9
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


# 默认配置（从环境变量读取）
DEFAULT_APP_TOKEN = os.environ.get("FEISHU_BITABLE_APP_TOKEN", "")
DEFAULT_TABLE_ID = os.environ.get("FEISHU_BITABLE_TABLE_ID", "")

# 飞书 API 配置
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def get_user_access_token() -> Optional[str]:
    """获取用户访问令牌"""
    # 优先从环境变量获取
    token = os.environ.get("FEISHU_USER_ACCESS_TOKEN")
    if token:
        return token
    
    # 尝试从 OpenClaw token store 读取
    # 路径: ~/.openclaw/tokens/feishu/default/user_access_token
    token_path = Path.home() / ".openclaw" / "tokens" / "feishu" / "default" / "user_access_token"
    if token_path.exists():
        try:
            data = json.loads(token_path.read_text())
            token = data.get("access_token") or data.get("user_access_token")
            if token:
                return token
        except (json.JSONDecodeError, KeyError):
            pass
    
    return None


def call_feishu_api(
    method: str,
    path: str,
    token: str,
    body: Optional[dict] = None,
) -> dict:
    """调用飞书开放平台 API"""
    url = f"{FEISHU_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    data = None
    if body:
        data = json.dumps(body).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("code") != 0:
                raise Exception(f"API error: {result.get('msg', result)}")
            return result.get("data", {})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_body}")


def upload_file_to_feishu(
    file_path: str,
    token: str,
    parent_token: str = "nodcnCk8EyTpvvn9plx0OLTdSlg",
) -> dict:
    """上传文件到飞书云空间"""
    import mimetypes
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    
    # 1. 获取上传凭证
    path = "/drive/v1/files/upload_prepare"
    body = {
        "file_name": file_name,
        "size": file_size,
        "parent_type": "explorer",
        "parent_node": parent_token,
    }
    
    prepare_result = call_feishu_api("POST", path, token, body)
    upload_ticket = prepare_result.get("upload_ticket")
    
    # 2. 上传文件内容
    upload_url = f"{FEISHU_API_BASE}/drive/v1/files/upload_content"
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    # 构造 multipart/form-data 请求
    import io
    import uuid
    
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    # 构建请求体
    body_parts = []
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="upload_ticket"\r\n\r\n'.encode())
    body_parts.append(f"{upload_ticket}\r\n".encode())
    
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode())
    body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode())
    body_parts.append(file_data)
    body_parts.append(b"\r\n")
    
    body_parts.append(f"--{boundary}--\r\n".encode())
    
    data = b"".join(body_parts)
    
    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("code") != 0:
                raise Exception(f"Upload error: {result.get('msg', result)}")
            return result.get("data", {})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Upload HTTP {e.code}: {error_body}")


def save_to_bitable(
    app_token: str,
    table_id: str,
    token: str,
    title: str,
    source: str,
    category: str,
    url: str,
    content: str,
    content_file: str = None,
) -> dict:
    """保存内容到多维表格"""
    
    # 上传文件到云空间（如果提供了文件路径）
    file_url = None
    upload_success = False
    if content_file and os.path.exists(content_file):
        try:
            upload_result = upload_file_to_feishu(content_file, token)
            file_token = upload_result.get("file_token")
            if file_token:
                file_url = f"https://my.feishu.cn/file/{file_token}"
                upload_success = True
                print(f"✅ 文件上传成功: {file_url}", file=sys.stderr)
            else:
                print(f"⚠️ 文件上传返回空token", file=sys.stderr)
        except Exception as e:
            print(f"❌ 文件上传失败: {e}", file=sys.stderr)
    
    # 构建记录字段
    fields = {
        "标题": title,
        "来源": source,
        "分类": category,
        "原文链接": {"text": "查看原文", "link": url},
        "摘要内容": content[:2000] if len(content) > 2000 else content,  # 摘要限制长度
    }
    
    # 只有文件上传成功时，才添加原文文件字段
    if upload_success and file_url:
        fields["原文文件"] = {"text": "查看完整内容", "link": file_url}
    else:
        print(f"⚠️ 原文文件字段未写入（上传失败或未提供文件）", file=sys.stderr)
    
    # 调用 API 创建记录
    path = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    body = {
        "fields": fields,
    }
    
    result = call_feishu_api("POST", path, token, body)
    return result


def update_content_field(
    app_token: str,
    table_id: str,
    token: str,
    record_id: str,
    content: str,
) -> dict:
    """更新多维表格记录的"原文内容"字段
    
    用于两步写入场景：
    1. Agent 先写入短字段（标题、来源、分类、链接）
    2. 脚本更新长字段（原文内容）
    """
    
    fields = {
        "原文内容": content,
    }
    
    path = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    body = {
        "fields": fields,
    }
    
    result = call_feishu_api("PUT", path, token, body)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="保存内容到飞书多维表格（支持文件路径传入长文本）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 创建完整记录
  python3 save_to_bitable.py \
      --title "OpenClaw 发布新版本" \
      --source "Twitter" \
      --category "🔧 工具推荐" \
      --url "https://x.com/..." \
      --content-file /tmp/content.md

  # 更新已有记录的长文本字段（两步写入）
  python3 save_to_bitable.py \
      --record-id "recXXXXXX" \
      --content-file /tmp/content.md

注意：
    需要设置环境变量 FEISHU_USER_ACCESS_TOKEN 或通过 --token 传入
        """
    )
    
    # 模式选择
    parser.add_argument("--record-id", help="更新已有记录（只更新原文内容字段）")
    
    # 创建记录所需参数
    parser.add_argument("--title", help="内容标题（创建模式必需）")
    parser.add_argument("--source", help="来源（创建模式必需）")
    parser.add_argument("--category", help="分类（创建模式必需）")
    parser.add_argument("--url", help="原文链接（创建模式必需）")
    
    # 通用参数
    parser.add_argument("--content-file", required=True, help="原文内容的 .md 文件路径")
    parser.add_argument("--app-token", default=DEFAULT_APP_TOKEN, help="多维表格 App Token")
    parser.add_argument("--table-id", default=DEFAULT_TABLE_ID, help="数据表 ID")
    parser.add_argument("--token", help="用户访问令牌（优先于环境变量）")
    
    args = parser.parse_args()
    
    # 参数校验
    if args.record_id:
        # 更新模式
        mode = "update"
    elif all([args.title, args.source, args.category, args.url]):
        # 创建模式
        mode = "create"
    else:
        print("错误：需要提供 --record-id（更新模式）或 --title/--source/--category/--url（创建模式）", file=sys.stderr)
        sys.exit(1)
    
    # 获取 token
    token = args.token or get_user_access_token()
    if not token:
        print("错误：未找到用户访问令牌", file=sys.stderr)
        print("请设置环境变量 FEISHU_USER_ACCESS_TOKEN 或使用 --token 参数", file=sys.stderr)
        sys.exit(1)
    
    # 读取内容文件
    content_path = Path(args.content_file)
    if not content_path.exists():
        print(f"错误：文件不存在: {content_path}", file=sys.stderr)
        sys.exit(1)
    
    content = content_path.read_text(encoding="utf-8")
    
    # 调用 API
    try:
        if mode == "create":
            result = save_to_bitable(
                app_token=args.app_token,
                table_id=args.table_id,
                token=token,
                title=args.title,
                source=args.source,
                category=args.category,
                url=args.url,
                content=content,
                content_file=str(content_path),
            )
            
            output = {
                "success": True,
                "mode": "create",
                "record_id": result.get("record", {}).get("record_id"),
                "app_token": args.app_token,
                "table_id": args.table_id,
                "title": args.title,
                "content_length": len(content),
                "message": "✅ 内容已保存到多维表格",
                "url": f"https://my.feishu.cn/base/{args.app_token}?table={args.table_id}",
            }
        else:
            # 更新模式
            result = update_content_field(
                app_token=args.app_token,
                table_id=args.table_id,
                token=token,
                record_id=args.record_id,
                content=content,
            )
            
            output = {
                "success": True,
                "mode": "update",
                "record_id": args.record_id,
                "content_length": len(content),
                "message": "✅ 原文内容已更新",
                "url": f"https://my.feishu.cn/base/{args.app_token}?table={args.table_id}",
            }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        output = {
            "success": False,
            "error": str(e),
            "message": f"❌ 保存失败: {e}",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()