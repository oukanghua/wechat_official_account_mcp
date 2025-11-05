"""
素材管理工具 - 上传和管理微信公众号素材
"""
import logging
import base64
import os
from typing import Dict, Any, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


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
            description="上传图文消息内所需的图片，不占用素材库限制",
            inputSchema={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "本地文件路径"
                    },
                    "fileData": {
                        "type": "string",
                        "description": "Base64编码的文件数据（与filePath二选一）"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="wechat_permanent_media",
            description="管理微信公众号永久素材",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "get", "delete", "list", "count"],
                        "description": "操作类型"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["image", "voice", "video", "thumb", "news"],
                        "description": "素材类型"
                    },
                    "filePath": {
                        "type": "string",
                        "description": "本地文件路径"
                    },
                    "fileData": {
                        "type": "string",
                        "description": "Base64编码的文件数据"
                    },
                    "mediaId": {
                        "type": "string",
                        "description": "媒体文件ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "视频素材的标题"
                    },
                    "introduction": {
                        "type": "string",
                        "description": "视频素材的描述"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "偏移量（列表时使用）"
                    },
                    "count": {
                        "type": "integer",
                        "description": "数量（列表时使用）"
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
            
            file_path = arguments.get('filePath')
            file_data = arguments.get('fileData')
            
            if not file_path and not file_data:
                return "错误：必须提供 filePath 或 fileData"
            
            # 读取文件数据
            if file_data:
                file_content = base64.b64decode(file_data)
                file_name = arguments.get('fileName', f'media.{media_type}')
            else:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_name = os.path.basename(file_path)
            
            # 上传素材（临时素材不支持 title 和 introduction，只有视频永久素材才需要）
            result = api_client.upload_media(
                media_type=media_type,
                file_content=file_content,
                filename=file_name
            )
            
            # 保存到本地存储
            storage_manager.save_media({
                'media_id': result.get('media_id'),
                'type': result.get('type', media_type),
                'created_at': result.get('created_at', 0),
                'url': file_name
            })
            
            return f"临时素材上传成功！\n素材ID: {result.get('media_id')}\n类型: {result.get('type')}\n创建时间: {result.get('created_at', 0)}"
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：获取素材时 mediaId 是必需的"
            
            media_content = api_client.get_media(media_id)
            
            return f"获取临时素材成功！\n素材ID: {media_id}\n素材大小: {len(media_content)} 字节"
        
        elif action == 'list':
            return "临时素材列表功能暂不支持，临时素材有效期为3天，建议使用永久素材功能"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        logger.error(f'素材操作失败: {str(e)}', exc_info=True)
        return f"素材操作失败: {str(e)}"


async def handle_upload_img_tool(arguments: Dict[str, Any], api_client) -> str:
    """处理图文消息图片上传工具"""
    try:
        file_path = arguments.get('filePath')
        file_data = arguments.get('fileData')
        
        if not file_path and not file_data:
            return "错误：必须提供 filePath 或 fileData"
        
        # 读取文件数据
        if file_data:
            file_content = base64.b64decode(file_data)
        else:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        
        # 上传图片
        result = api_client.upload_img(file_content=file_content)
        
        if result.get('errcode'):
            return f"上传图片失败: {result.get('errmsg', '未知错误')}"
        
        return f"图片上传成功！\n图片URL: {result.get('url')}"
    
    except Exception as e:
        logger.error(f'上传图片失败: {str(e)}', exc_info=True)
        return f"上传图片失败: {str(e)}"


async def handle_permanent_media_tool(arguments: Dict[str, Any], api_client, storage_manager) -> str:
    """处理永久素材工具"""
    action = arguments.get('action')
    
    try:
        if action == 'add':
            media_type = arguments.get('type')
            if not media_type:
                return "错误：添加永久素材时 type 是必需的"
            
            file_path = arguments.get('filePath')
            file_data = arguments.get('fileData')
            
            if not file_path and not file_data:
                return "错误：必须提供 filePath 或 fileData"
            
            # 读取文件数据
            if file_data:
                file_content = base64.b64decode(file_data)
            else:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            
            # 上传永久素材（图片类型不需要 title 和 introduction）
            if media_type == 'video':
                result = api_client.upload_permanent_media(
                    media_type=media_type,
                    file_content=file_content,
                    title=arguments.get('title'),
                    introduction=arguments.get('introduction')
                )
            else:
                result = api_client.upload_permanent_media(
                    media_type=media_type,
                    file_content=file_content
                )
            
            # 保存到本地存储
            storage_manager.save_media({
                'media_id': result.get('media_id'),
                'type': media_type,
                'created_at': 0,
                'url': file_path or 'uploaded'
            })
            
            return f"永久素材上传成功！\n素材ID: {result.get('media_id')}\n类型: {media_type}"
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：获取永久素材时 mediaId 是必需的"
            
            media_content = api_client.get_permanent_media(media_id)
            
            return f"获取永久素材成功！\n素材ID: {media_id}\n素材大小: {len(media_content)} 字节"
        
        elif action == 'delete':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：删除永久素材时 mediaId 是必需的"
            
            result = api_client.delete_permanent_media(media_id)
            
            return f"永久素材删除成功！\n素材ID: {media_id}"
        
        elif action == 'list':
            media_type = arguments.get('type', 'image')
            offset = arguments.get('offset', 0)
            count = arguments.get('count', 20)
            
            result = api_client._request('POST', '/cgi-bin/material/batchget_material', data={
                'type': media_type,
                'offset': offset,
                'count': count
            })
            
            items = result.get('item', [])
            item_list = '\n'.join([
                f"{i+1}. 素材ID: {item.get('media_id')}\n   文件名: {item.get('name', '未知')}\n   更新时间: {item.get('update_time', 0)}"
                for i, item in enumerate(items)
            ])
            
            return f"永久素材列表 ({offset + 1}-{offset + len(items)}/{result.get('total_count', 0)}):\n\n{item_list}"
        
        elif action == 'count':
            result = api_client._request('GET', '/cgi-bin/material/get_materialcount')
            
            return f"永久素材统计：\n图片: {result.get('image_count', 0)}\n语音: {result.get('voice_count', 0)}\n视频: {result.get('video_count', 0)}\n图文: {result.get('news_count', 0)}"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        logger.error(f'永久素材操作失败: {str(e)}', exc_info=True)
        return f"永久素材操作失败: {str(e)}"

