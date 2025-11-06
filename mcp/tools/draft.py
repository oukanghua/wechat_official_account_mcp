"""
草稿管理工具 - 管理微信公众号图文草稿
"""
import logging
from typing import Dict, Any, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


def register_draft_tools() -> List[Tool]:
    """注册草稿工具"""
    return [
        Tool(
            name="wechat_draft",
            description="管理微信公众号图文草稿",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "get", "delete", "list", "count", "update"],
                        "description": "操作类型：add(创建), get(获取), delete(删除), list(列表), count(统计), update(更新)"
                    },
                    "mediaId": {
                        "type": "string",
                        "description": "草稿 Media ID（获取、删除、更新时必需）"
                    },
                    "articles": {
                        "type": "array",
                        "description": "文章列表（创建/更新时必需）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "文章标题"},
                                "author": {"type": "string", "description": "作者"},
                                "digest": {"type": "string", "description": "摘要"},
                                "content": {"type": "string", "description": "文章内容"},
                                "contentSourceUrl": {"type": "string", "description": "原文链接"},
                                "thumbMediaId": {"type": "string", "description": "封面图片媒体ID"},
                                "showCoverPic": {"type": "number", "description": "是否显示封面图片"},
                                "needOpenComment": {"type": "number", "description": "是否开启评论"},
                                "onlyFansCanComment": {"type": "number", "description": "是否仅粉丝可评论"}
                            },
                            "required": ["title", "content", "thumbMediaId"]
                        }
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


async def handle_draft_tool(arguments: Dict[str, Any], api_client) -> str:
    """处理草稿工具"""
    action = arguments.get('action')
    
    try:
        if action == 'add':
            articles = arguments.get('articles')
            if not articles or len(articles) == 0:
                return "错误：文章内容不能为空"
            
            # 转换文章格式
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'title': article.get('title', ''),
                    'author': article.get('author', ''),
                    'digest': article.get('digest', ''),
                    'content': article.get('content', ''),
                    'content_source_url': article.get('contentSourceUrl', ''),
                    'thumb_media_id': article.get('thumbMediaId', ''),
                    'show_cover_pic': article.get('showCoverPic', 0),
                    'need_open_comment': article.get('needOpenComment', 0),
                    'only_fans_can_comment': article.get('onlyFansCanComment', 0)
                })
            
            result = api_client.add_draft(formatted_articles)
            
            return f"草稿创建成功！\n草稿ID: {result.get('media_id')}\n包含文章数: {len(articles)}"
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            result = api_client.get_draft(media_id)
            
            news_items = result.get('news_item', [])
            articles_text = '\n\n'.join([
                f"第{i+1}篇:\n"
                f"标题: {item.get('title', '')}\n"
                f"作者: {item.get('author', '未设置')}\n"
                f"摘要: {item.get('digest', '无')}\n"
                f"内容: {item.get('content', '')[:100]}{'...' if len(item.get('content', '')) > 100 else ''}\n"
                f"原文链接: {item.get('content_source_url', '无')}\n"
                f"封面图ID: {item.get('thumb_media_id', '')}\n"
                f"显示封面: {'是' if item.get('show_cover_pic', 0) else '否'}"
                for i, item in enumerate(news_items)
            ])
            
            return f"获取草稿成功！\n草稿ID: {media_id}\n创建时间: {result.get('create_time', 0)}\n更新时间: {result.get('update_time', 0)}\n\n{articles_text}"
        
        elif action == 'delete':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            result = api_client.delete_draft(media_id)
            
            return f"草稿删除成功！\n草稿ID: {media_id}"
        
        elif action == 'list':
            offset = arguments.get('offset', 0)
            count = arguments.get('count', 20)
            
            result = api_client._request('POST', '/cgi-bin/draft/batchget', data={
                'offset': offset,
                'count': count
            })
            
            items = result.get('item', [])
            draft_list = '\n\n'.join([
                f"{offset + i + 1}. 草稿ID: {item.get('media_id', '')}\n"
                f"   标题: {item.get('content', {}).get('news_item', [{}])[0].get('title', '未知')}\n"
                f"   作者: {item.get('content', {}).get('news_item', [{}])[0].get('author', '未设置')}\n"
                f"   创建时间: {item.get('content', {}).get('create_time', 0)}\n"
                f"   更新时间: {item.get('content', {}).get('update_time', 0)}"
                for i, item in enumerate(items)
            ])
            
            return f"草稿列表 ({offset + 1}-{offset + len(items)}/{result.get('total_count', 0)}):\n\n{draft_list}"
        
        elif action == 'count':
            result = api_client._request('POST', '/cgi-bin/draft/count')
            
            return f"草稿统计信息：\n草稿总数: {result.get('total_count', 0)} 个"
        
        elif action == 'update':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            articles = arguments.get('articles')
            if not articles or len(articles) == 0:
                return "错误：文章内容不能为空"
            
            # 更新每篇文章
            for index, article in enumerate(articles):
                update_data = {
                    'media_id': media_id,
                    'index': index,
                    'articles': {
                        'title': article.get('title', ''),
                        'author': article.get('author', ''),
                        'digest': article.get('digest', ''),
                        'content': article.get('content', ''),
                        'content_source_url': article.get('contentSourceUrl', ''),
                        'thumb_media_id': article.get('thumbMediaId', ''),
                        'show_cover_pic': article.get('showCoverPic', 0),
                        'need_open_comment': article.get('needOpenComment', 0),
                        'only_fans_can_comment': article.get('onlyFansCanComment', 0)
                    }
                }
                api_client._request('POST', '/cgi-bin/draft/update', data=update_data)
            
            return f"草稿更新成功！\n草稿ID: {media_id}\n更新文章数: {len(articles)}"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        import traceback
        error_detail = str(e)
        if logger.isEnabledFor(logging.DEBUG):
            error_detail += f"\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f'草稿操作失败: {error_detail}', exc_info=True)
        return f"草稿操作失败: {error_detail}"

