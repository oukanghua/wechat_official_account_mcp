"""
发布管理工具 - 管理微信公众号文章发布
"""
import logging
from typing import Dict, Any, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


def register_publish_tools() -> List[Tool]:
    """注册发布工具"""
    return [
        Tool(
            name="wechat_publish",
            description="管理微信公众号文章发布",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["submit", "get", "delete", "list"],
                        "description": "操作类型：submit(发布草稿), get(获取发布状态), delete(删除发布), list(获取发布列表)"
                    },
                    "mediaId": {
                        "type": "string",
                        "description": "草稿 Media ID（发布时必需）"
                    },
                    "publishId": {
                        "type": "string",
                        "description": "发布任务ID（获取状态时必需）"
                    },
                    "articleId": {
                        "type": "string",
                        "description": "文章ID（删除发布时必需）"
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


async def handle_publish_tool(arguments: Dict[str, Any], api_client) -> str:
    """处理发布工具"""
    action = arguments.get('action')
    
    try:
        if action == 'submit':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：发布草稿时 mediaId 是必需的"
            
            result = api_client.publish_draft(media_id)
            
            publish_id = result.get('publish_id', '')
            msg_data_id = result.get('msg_data_id', '')
            
            return f"草稿发布成功！\n草稿ID: {media_id}\n发布任务ID: {publish_id}\n消息数据ID: {msg_data_id}\n文章将在审核通过后发布到公众号"
        
        elif action == 'get':
            publish_id = arguments.get('publishId')
            if not publish_id:
                return "错误：获取发布状态时 publishId 是必需的"
            
            result = api_client._request('POST', '/cgi-bin/freepublish/get', data={
                'publish_id': publish_id
            })
            
            publish_status = result.get('publish_status', 0)
            status_text = {
                0: '审核中',
                1: '审核通过',
                2: '审核失败',
                3: '已发布'
            }.get(publish_status, '未知')
            
            return f"发布状态：\n发布任务ID: {publish_id}\n状态: {status_text}({publish_status})\n文章ID: {result.get('article_id', '')}"
        
        elif action == 'delete':
            article_id = arguments.get('articleId')
            if not article_id:
                return "错误：删除发布时 articleId 是必需的"
            
            index = arguments.get('index', 1)  # 默认删除第一篇
            
            result = api_client._request('POST', '/cgi-bin/freepublish/delete', data={
                'article_id': article_id,
                'index': index
            })
            
            return f"发布删除成功！\n文章ID: {article_id}"
        
        elif action == 'list':
            offset = arguments.get('offset', 0)
            count = arguments.get('count', 20)
            
            result = api_client._request('POST', '/cgi-bin/freepublish/batchget', data={
                'offset': offset,
                'count': count,
                'no_content': 1  # 不返回文章内容
            })
            
            items = result.get('item', [])
            publish_list = '\n\n'.join([
                f"{offset + i + 1}. 文章ID: {item.get('article_id', '')}\n"
                f"   标题: {item.get('content', {}).get('news_item', [{}])[0].get('title', '未知')}\n"
                f"   发布时间: {item.get('publish_time', 0)}\n"
                f"   更新状态: {item.get('update_time', 0)}"
                for i, item in enumerate(items)
            ])
            
            return f"发布列表 ({offset + 1}-{offset + len(items)}/{result.get('total_count', 0)}):\n\n{publish_list}"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        logger.error(f'发布操作失败: {str(e)}', exc_info=True)
        return f"发布操作失败: {str(e)}"

