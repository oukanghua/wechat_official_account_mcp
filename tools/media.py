"""
素材管理工具 - 上传和管理微信公众号素材
"""
import json
import logging
import base64
import os
import traceback
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from mcp.types import Tool

logger = logging.getLogger(__name__)

# 常量定义
PERMANENT_MEDIA_ADD_TYPES = ['image', 'voice', 'video', 'thumb']
PERMANENT_MEDIA_LIST_TYPES = ['image', 'video', 'voice', 'news']
LIST_COUNT_MIN = 1
LIST_COUNT_MAX = 20
MATERIAL_LIMIT_IMAGE = 100000
MATERIAL_LIMIT_NEWS = 100000
MATERIAL_LIMIT_OTHER = 1000


def _read_file_content(file_path: Optional[str], file_data: Optional[str]) -> Tuple[bytes, Optional[str]]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        file_data: Base64编码的文件数据
        
    Returns:
        (文件内容, 文件名) 元组
    """
    if file_data:
        return base64.b64decode(file_data), None
    
    if not file_path:
        raise ValueError("必须提供 filePath 或 fileData")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        content = f.read()
    return content, filename


def _format_timestamp(timestamp: int) -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: Unix时间戳
        
    Returns:
        格式化后的时间字符串
    """
    if not timestamp:
        return '未知'
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, OSError):
        return str(timestamp)


def _format_news_item(news_item: Dict[str, Any], index: int) -> List[str]:
    """
    格式化图文消息项
    
    Args:
        news_item: 图文消息项数据
        index: 索引
        
    Returns:
        格式化后的字符串列表
    """
    lines = [f"  文章 {index}:"]
    lines.append(f"    标题: {news_item.get('title', '无')}")
    lines.append(f"    作者: {news_item.get('author', '无')}")
    
    if news_item.get('digest'):
        lines.append(f"    摘要: {news_item.get('digest')}")
    
    lines.append(f"    封面图片ID: {news_item.get('thumb_media_id', '无')}")
    lines.append(f"    显示封面: {'是' if news_item.get('show_cover_pic', 0) == 1 else '否'}")
    
    if news_item.get('url'):
        lines.append(f"    图文页URL: {news_item.get('url')}")
    
    if news_item.get('content_source_url'):
        lines.append(f"    原文地址: {news_item.get('content_source_url')}")
    
    return lines


def _handle_error(e: Exception, operation: str) -> str:
    """
    统一错误处理
    
    Args:
        e: 异常对象
        operation: 操作名称
        
    Returns:
        错误消息
    """
    error_detail = str(e)
    if logger.isEnabledFor(logging.DEBUG):
        error_detail += f"\n详细错误信息:\n{traceback.format_exc()}"
    logger.error(f'{operation}失败: {error_detail}', exc_info=True)
    return f"{operation}失败: {error_detail}"


def register_media_tools() -> List[Tool]:
    """注册素材工具"""
    return [
        Tool(
            name="wechat_media_upload",
            description="上传和管理微信公众号临时素材（图片、语音、视频、缩略图）",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["upload", "get", "list"],
                        "description": "操作类型：upload-上传素材, get-获取素材, list-列表素材"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["image", "voice", "video", "thumb"],
                        "description": "素材类型：image-图片, voice-语音, video-视频, thumb-缩略图"
                    },
                    "filePath": {
                        "type": "string",
                        "description": "本地文件路径（upload操作可选）"
                    },
                    "fileData": {
                        "type": "string",
                        "description": "Base64编码的文件数据（upload操作可选，与filePath二选一）"
                    },
                    "fileName": {
                        "type": "string",
                        "description": "文件名（upload操作可选）"
                    },
                    "mediaId": {
                        "type": "string",
                        "description": "媒体文件ID（get操作必需）"
                    },
                    "title": {
                        "type": "string",
                        "description": "视频素材的标题（video类型upload操作可选）"
                    },
                    "introduction": {
                        "type": "string",
                        "description": "视频素材的描述（video类型upload操作可选）"
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="wechat_upload_img",
            description="上传图文消息内所需的图片，不占用素材库限制（仅支持jpg/png格式，大小必须在1MB以下）",
            inputSchema={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "本地文件路径（仅支持jpg/png格式，大小必须在1MB以下）"
                    },
                    "fileData": {
                        "type": "string",
                        "description": "Base64编码的文件数据（与filePath二选一，仅支持jpg/png格式，大小必须在1MB以下）"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="wechat_permanent_media",
            description="管理微信公众号永久素材（添加、根据mediaId获取单个素材、分类型获取永久素材列表、删除、统计）",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "get", "delete", "list", "count"],
                        "description": "操作类型：add(添加永久素材), get(根据mediaId获取单个永久素材), delete(删除永久素材，需先通过获取素材列表获取media_id), list(分类型获取永久素材列表), count(获取永久素材总数，包含图片/语音/视频/图文各类型数量)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["image", "voice", "video", "thumb", "news"],
                        "description": "素材类型：add操作支持image/voice/video/thumb（不支持news，图文素材请使用草稿接口），list操作支持image/video/voice/news（list操作时必填）"
                    },
                    "filePath": {
                        "type": "string",
                        "description": "本地文件路径（add操作时使用）"
                    },
                    "fileData": {
                        "type": "string",
                        "description": "Base64编码的文件数据（add操作时使用）"
                    },
                    "mediaId": {
                        "type": "string",
                        "description": "媒体文件ID（get和delete操作时必需，用于根据mediaId获取单个素材或删除素材。可通过获取素材列表获取media_id）"
                    },
                    "title": {
                        "type": "string",
                        "description": "视频素材的标题（add操作上传video类型时必填）"
                    },
                    "introduction": {
                        "type": "string",
                        "description": "视频素材的描述（add操作上传video类型时可选）"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "偏移量（list操作时使用，从0开始，表示从第几个素材开始返回）"
                    },
                    "count": {
                        "type": "integer",
                        "description": "数量（list操作时使用，取值在1到20之间）"
                    }
                },
                "required": ["action"]
            }
        )
    ]


async def handle_media_upload_tool(arguments: Dict[str, Any], api_client, storage_manager) -> str:
    """处理临时素材上传工具"""
    action = arguments.get('action')
    
    try:
        if action == 'upload':
            media_type = arguments.get('type')
            if not media_type:
                return "错误：上传素材时 type 是必需的"
            
            file_content, filename = _read_file_content(
                arguments.get('filePath'),
                arguments.get('fileData')
            )
            
            if not filename:
                filename = arguments.get('fileName', f'media.{media_type}')
            
            result = await api_client.upload_media(
                media_type=media_type,
                file_content=file_content,
                filename=filename
            )
            
            storage_manager.save_media({
                'media_id': result.get('media_id'),
                'type': result.get('type', media_type),
                'created_at': result.get('created_at', 0),
                'url': filename
            })
            
            return (f"临时素材上传成功！\n"
                   f"素材ID: {result.get('media_id')}\n"
                   f"类型: {result.get('type')}\n"
                   f"创建时间: {result.get('created_at', 0)}")
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：获取素材时 mediaId 是必需的"
            
            media_content = await api_client.get_media(media_id)
            return f"获取临时素材成功！\n素材ID: {media_id}\n素材大小: {len(media_content)} 字节"
        
        elif action == 'list':
            return "临时素材列表功能暂不支持，临时素材有效期为3天，建议使用永久素材功能"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        return _handle_error(e, '素材操作')


async def handle_upload_img_tool(arguments: Dict[str, Any], api_client) -> str:
    """处理图文消息图片上传工具"""
    try:
        file_content, filename = _read_file_content(
            arguments.get('filePath'),
            arguments.get('fileData')
        )
        
        result = await api_client.upload_img(file_content=file_content, filename=filename)
        
        errcode = result.get('errcode', -1)
        errmsg = result.get('errmsg', '未知错误')
        url = result.get('url', '')
        
        if errcode == 0:
            return f"图片上传成功！\n图片URL: {url}\n注意：此图片不占用素材库限制"
        else:
            return f"上传图片失败：{errcode} - {errmsg}"
    
    except Exception as e:
        return _handle_error(e, '上传图片')


async def _handle_permanent_media_add(
    arguments: Dict[str, Any],
    api_client,
    storage_manager
) -> str:
    """处理添加永久素材"""
    media_type = arguments.get('type')
    if not media_type:
        return "错误：添加永久素材时 type 是必需的（image/voice/video/thumb）"
    
    if media_type not in PERMANENT_MEDIA_ADD_TYPES:
        return (f"错误：add操作只支持以下类型: {', '.join(PERMANENT_MEDIA_ADD_TYPES)}"
               f"（图文素材请使用草稿接口）")
    
    if media_type == 'video':
        title = arguments.get('title')
        if not title:
            return "错误：上传视频素材时 title 是必需的"
    
    file_content, _ = _read_file_content(
        arguments.get('filePath'),
        arguments.get('fileData')
    )
    
    if media_type == 'video':
        result = await api_client.upload_permanent_media(
            media_type=media_type,
            file_content=file_content,
            title=arguments.get('title'),
            introduction=arguments.get('introduction')
        )
    else:
        result = await api_client.upload_permanent_media(
            media_type=media_type,
            file_content=file_content
        )
    
    storage_manager.save_media({
        'media_id': result.get('media_id'),
        'type': media_type,
        'created_at': 0,
        'url': result.get('url') or arguments.get('filePath') or 'uploaded'
    })
    
    result_lines = [
        "永久素材上传成功！",
        f"素材ID: {result.get('media_id')}",
        f"类型: {media_type}"
    ]
    
    if media_type == 'image' and result.get('url'):
        result_lines.append(f"图片URL: {result.get('url')}")
    
    return '\n'.join(result_lines)


async def _handle_permanent_media_get(
    media_id: str,
    api_client
) -> str:
    """处理获取单个永久素材"""
    media_result = await api_client.get_permanent_media(media_id)
    
    if isinstance(media_result, dict):
        if 'news_item' in media_result:
            # 图文素材
            news_items = media_result.get('news_item', [])
            result_lines = [
                "获取永久素材成功！",
                f"素材ID: {media_id}",
                "素材类型: 图文素材",
                ""
            ]
            
            for idx, item in enumerate(news_items, 1):
                result_lines.append(f"【文章 {idx}】")
                result_lines.append(f"标题: {item.get('title', '无')}")
                result_lines.append(f"封面图片ID: {item.get('thumb_media_id', '无')}")
                result_lines.append(f"显示封面: {'是' if item.get('show_cover_pic', 0) == 1 else '否'}")
                result_lines.append(f"作者: {item.get('author', '无')}")
                
                if item.get('digest'):
                    result_lines.append(f"摘要: {item.get('digest')}")
                
                result_lines.append(f"内容长度: {len(item.get('content', ''))} 字符")
                result_lines.append(f"图文页URL: {item.get('url', '无')}")
                
                if item.get('content_source_url'):
                    result_lines.append(f"原文地址: {item.get('content_source_url')}")
            
            return '\n'.join(result_lines)
        
        elif 'title' in media_result or 'down_url' in media_result:
            # 视频素材
            return ('获取永久素材成功！\n'
                   f'素材ID: {media_id}\n'
                   '素材类型: 视频素材\n'
                   f"标题: {media_result.get('title', '无')}\n"
                   f"描述: {media_result.get('description', '无')}\n"
                   f"下载地址: {media_result.get('down_url', '无')}")
        
        else:
            # 未知的字典格式
            return (f"获取永久素材成功！\n"
                   f"素材ID: {media_id}\n"
                   f"素材类型: 未知格式\n"
                   f"内容: {json.dumps(media_result, ensure_ascii=False, indent=2)}")
    
    # 其他类型素材（图片、语音、缩略图）
    return (f"获取永久素材成功！\n"
           f"素材ID: {media_id}\n"
           f"素材类型: 文件素材\n"
           f"素材大小: {len(media_result)} 字节")


async def _handle_permanent_media_delete(
    media_id: str,
    api_client
) -> str:
    """处理删除永久素材"""
    result = await api_client.delete_permanent_media(media_id)
    
    errcode = result.get('errcode', -1)
    errmsg = result.get('errmsg', '未知错误')
    
    if errcode == 0:
        return f"永久素材删除成功！\n素材ID: {media_id}"
    else:
        return f"删除永久素材失败：{errcode} - {errmsg}\n素材ID: {media_id}"


async def _handle_permanent_media_list(
    arguments: Dict[str, Any],
    api_client
) -> str:
    """处理获取永久素材列表"""
    media_type = arguments.get('type')
    if not media_type:
        return "错误：获取永久素材列表时 type 是必需的（image/video/voice/news）"
    
    if media_type not in PERMANENT_MEDIA_LIST_TYPES:
        return f"错误：list操作只支持以下类型: {', '.join(PERMANENT_MEDIA_LIST_TYPES)}"
    
    offset = arguments.get('offset', 0)
    if offset < 0:
        return "错误：offset 参数必须大于等于 0"
    
    count = arguments.get('count', 20)
    if count < LIST_COUNT_MIN or count > LIST_COUNT_MAX:
        return f"错误：count 参数必须在 {LIST_COUNT_MIN} 到 {LIST_COUNT_MAX} 之间"
    
    result = await api_client._request('POST', '/cgi-bin/material/batchget_material', data={
        'type': media_type,
        'offset': offset,
        'count': count
    })
    
    total_count = result.get('total_count', 0)
    item_count = result.get('item_count', 0)
    items = result.get('item', [])
    
    result_lines = [
        f"永久素材列表（类型: {media_type}）",
        f"总数: {total_count}",
        f"本次获取: {item_count}",
        f"偏移位置: {offset}",
        ""
    ]
    
    if not items:
        result_lines.append("暂无素材")
    else:
        for idx, item in enumerate(items, 1):
            result_lines.append(f"【素材 {idx}】")
            result_lines.append(f"素材ID: {item.get('media_id', '无')}")
            result_lines.append(f"更新时间: {_format_timestamp(item.get('update_time', 0))}")
            
            if media_type == 'news' and 'content' in item:
                content = item.get('content', {})
                news_items = content.get('news_item', [])
                result_lines.append(f"文章数量: {len(news_items)}")
                
                for news_idx, news_item in enumerate(news_items, 1):
                    result_lines.extend(_format_news_item(news_item, news_idx))
            else:
                if item.get('name'):
                    result_lines.append(f"文件名: {item.get('name')}")
                if item.get('url'):
                    result_lines.append(f"素材URL: {item.get('url')}")
            
            result_lines.append("")
    
    return '\n'.join(result_lines)


async def _handle_permanent_media_count(api_client) -> str:
    """处理获取永久素材总数"""
    result = await api_client._request('GET', '/cgi-bin/material/get_materialcount')
    
    errcode = result.get('errcode', 0)
    if errcode != 0:
        errmsg = result.get('errmsg', '未知错误')
        return f"获取永久素材总数失败：{errcode} - {errmsg}"
    
    image_count = result.get('image_count', 0)
    voice_count = result.get('voice_count', 0)
    video_count = result.get('video_count', 0)
    news_count = result.get('news_count', 0)
    total_count = image_count + voice_count + video_count + news_count
    
    return '\n'.join([
        "永久素材总数统计",
        "=" * 30,
        f"图片素材: {image_count} 个（上限: {MATERIAL_LIMIT_IMAGE}）",
        f"语音素材: {voice_count} 个（上限: {MATERIAL_LIMIT_OTHER}）",
        f"视频素材: {video_count} 个（上限: {MATERIAL_LIMIT_OTHER}）",
        f"图文素材: {news_count} 个（上限: {MATERIAL_LIMIT_NEWS}）",
        "=" * 30,
        f"总计: {total_count} 个",
        "",
        "注意：",
        "- 总数包含公众平台官网素材管理中的素材",
        f"- 图片和图文消息素材（包括单图文和多图文）的总数上限为{MATERIAL_LIMIT_IMAGE}",
        f"- 其他素材（语音、视频）的总数上限为{MATERIAL_LIMIT_OTHER}"
    ])


async def handle_permanent_media_tool(
    arguments: Dict[str, Any],
    api_client,
    storage_manager
) -> str:
    """处理永久素材工具"""
    action = arguments.get('action')
    
    try:
        if action == 'add':
            return await _handle_permanent_media_add(arguments, api_client, storage_manager)
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：根据mediaId获取单个永久素材时，mediaId 是必需的"
            return await _handle_permanent_media_get(media_id, api_client)
        
        elif action == 'delete':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：删除永久素材时 mediaId 是必需的（可通过获取素材列表获取media_id）"
            return await _handle_permanent_media_delete(media_id, api_client)
        
        elif action == 'list':
            return await _handle_permanent_media_list(arguments, api_client)
        
        elif action == 'count':
            return await _handle_permanent_media_count(api_client)
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        return _handle_error(e, '永久素材操作')
