"""
草稿管理工具 - 管理微信公众号图文草稿
"""
import logging
import time
import re
from typing import Dict, Any, List, Optional
from mcp.types import Tool

logger = logging.getLogger(__name__)

# 常量定义
ARTICLE_TYPE_NEWS = 'news'
ARTICLE_TYPE_NEWSPIC = 'newspic'
ARTICLE_TYPE_TEXT_MAP = {
    ARTICLE_TYPE_NEWS: '图文消息',
    ARTICLE_TYPE_NEWSPIC: '图片消息'
}
MAX_CONTENT_PREVIEW_LENGTH = 200
MAX_DIGEST_PREVIEW_LENGTH = 100
MAX_LIST_DIGEST_LENGTH = 50
MAX_IMAGE_DISPLAY_COUNT = 5
MAX_LIST_IMAGE_DISPLAY_COUNT = 3
COUNT_MIN = 1
COUNT_MAX = 20


def clean_html_content(content: str) -> str:
    """
    清理HTML内容，提取body内的内容，移除DOCTYPE、html、head等标签
    
    微信公众号图文消息只需要body内的HTML片段，不需要完整的HTML文档结构
    
    Args:
        content: 原始HTML内容
        
    Returns:
        清理后的HTML内容
    """
    if not content:
        return content
    
    # 移除DOCTYPE声明
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    # 尝试提取body内的内容
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
    if body_match:
        # 提取body标签内的内容
        body_content = body_match.group(1)
        # 移除script和style标签及其内容（微信公众号不支持）
        body_content = re.sub(r'<script[^>]*>.*?</script>', '', body_content, flags=re.DOTALL | re.IGNORECASE)
        body_content = re.sub(r'<style[^>]*>.*?</style>', '', body_content, flags=re.DOTALL | re.IGNORECASE)
        return body_content.strip()
    
    # 如果没有body标签，尝试移除html和head标签
    content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    return content.strip()


def format_article_data(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化文章数据，将前端格式转换为API格式
    
    Args:
        article: 前端格式的文章数据
        
    Returns:
        API格式的文章数据
    """
    # 清理HTML内容，移除完整的HTML文档结构，只保留body内的内容
    raw_content = article.get('content', '')
    cleaned_content = clean_html_content(raw_content)
    
    article_data = {
        'title': article.get('title', ''),
        'content': cleaned_content
    }
    
    # 文章类型
    article_type = article.get('articleType', ARTICLE_TYPE_NEWS)
    if article_type:
        article_data['article_type'] = article_type
    
    # 基础字段
    if article.get('author'):
        article_data['author'] = article.get('author')
    if article.get('digest'):
        article_data['digest'] = article.get('digest')
    if article.get('contentSourceUrl'):
        article_data['content_source_url'] = article.get('contentSourceUrl')
    if article.get('thumbMediaId'):
        article_data['thumb_media_id'] = article.get('thumbMediaId')
    if article.get('showCoverPic') is not None:
        article_data['show_cover_pic'] = article.get('showCoverPic')
    if article.get('needOpenComment') is not None:
        article_data['need_open_comment'] = article.get('needOpenComment')
    if article.get('onlyFansCanComment') is not None:
        article_data['only_fans_can_comment'] = article.get('onlyFansCanComment')
    
    # 封面裁剪坐标
    if article.get('picCrop2351'):
        article_data['pic_crop_235_1'] = article.get('picCrop2351')
    if article.get('picCrop11'):
        article_data['pic_crop_1_1'] = article.get('picCrop11')
    
    # 图片消息的图片信息
    image_info = article.get('imageInfo')
    if image_info:
        image_list = image_info.get('imageList', [])
        if image_list:
            article_data['image_info'] = {
                'image_list': [
                    {'image_media_id': img.get('imageMediaId')}
                    for img in image_list
                    if img.get('imageMediaId')
                ]
            }
    
    # 封面信息
    cover_info = article.get('coverInfo')
    if cover_info:
        crop_percent_list = cover_info.get('cropPercentList', [])
        if crop_percent_list:
            article_data['cover_info'] = {
                'crop_percent_list': [
                    {
                        'ratio': crop.get('ratio'),
                        'x1': crop.get('x1'),
                        'y1': crop.get('y1'),
                        'x2': crop.get('x2'),
                        'y2': crop.get('y2')
                    }
                    for crop in crop_percent_list
                    if crop.get('ratio')
                ]
            }
    
    # 商品信息
    product_info = article.get('productInfo')
    if product_info:
        footer_product_info = product_info.get('footerProductInfo')
        if footer_product_info and footer_product_info.get('productKey'):
            article_data['product_info'] = {
                'footer_product_info': {
                    'product_key': footer_product_info.get('productKey')
                }
            }
    
    return article_data


def format_article_info(news_item: Dict[str, Any], index: int, indent: str = '') -> str:
    """
    格式化文章信息用于显示
    
    Args:
        news_item: 文章数据
        index: 文章索引（从1开始）
        indent: 缩进字符串，用于列表显示
        
    Returns:
        格式化后的文章信息字符串
    """
    article_type = news_item.get('article_type', ARTICLE_TYPE_NEWS)
    article_type_text = ARTICLE_TYPE_TEXT_MAP.get(article_type, '未知类型')
    
    lines = [f"{indent}第{index}篇 ({article_type_text}):"]
    lines.append(f"{indent}标题: {news_item.get('title', '未知')}")
    
    if article_type == ARTICLE_TYPE_NEWS:
        # 图文消息
        if news_item.get('author'):
            lines.append(f"{indent}作者: {news_item.get('author')}")
        if news_item.get('digest'):
            digest = news_item.get('digest', '')
            max_length = MAX_DIGEST_PREVIEW_LENGTH if indent == '' else MAX_LIST_DIGEST_LENGTH
            if len(digest) > max_length:
                digest = digest[:max_length] + '...'
            lines.append(f"{indent}摘要: {digest}")
        
        content = news_item.get('content', '')
        if content:
            content_preview = (content[:MAX_CONTENT_PREVIEW_LENGTH] + '...' 
                             if len(content) > MAX_CONTENT_PREVIEW_LENGTH else content)
            lines.append(f"{indent}内容预览: {content_preview}")
        
        if news_item.get('content_source_url'):
            lines.append(f"{indent}原文链接: {news_item.get('content_source_url')}")
        if news_item.get('thumb_media_id'):
            lines.append(f"{indent}封面图ID: {news_item.get('thumb_media_id')}")
        if news_item.get('show_cover_pic') is not None:
            show_cover = '是' if news_item.get('show_cover_pic', 0) else '否'
            lines.append(f"{indent}显示封面: {show_cover}")
    else:
        # 图片消息
        content = news_item.get('content', '')
        if content:
            content_preview = (content[:MAX_CONTENT_PREVIEW_LENGTH] + '...' 
                             if len(content) > MAX_CONTENT_PREVIEW_LENGTH else content)
            lines.append(f"{indent}内容预览: {content_preview}")
        
        image_info = news_item.get('image_info', {})
        image_list = image_info.get('image_list', [])
        if image_list:
            lines.append(f"{indent}图片数量: {len(image_list)}")
            max_display = MAX_IMAGE_DISPLAY_COUNT if indent == '' else MAX_LIST_IMAGE_DISPLAY_COUNT
            if len(image_list) <= max_display:
                for idx, img in enumerate(image_list):
                    lines.append(f"{indent}  {'图片' if indent == '' else '-'} {idx+1} ID: {img.get('image_media_id', '')}")
            else:
                image_ids = [img.get('image_media_id', '') for img in image_list[:max_display]]
                prefix = '前' if indent == '' else '- 前'
                lines.append(f"{indent}  {prefix}{max_display}张图片ID: {', '.join(image_ids)}")
                if indent == '':
                    lines.append(f"{indent}  ... 还有 {len(image_list) - max_display} 张图片")
    
    # 评论设置
    need_open_comment = news_item.get('need_open_comment', 0)
    only_fans_can_comment = news_item.get('only_fans_can_comment', 0)
    if need_open_comment == 1:
        comment_text = "仅粉丝可评论" if only_fans_can_comment == 1 else "所有人可评论"
        lines.append(f"{indent}评论: 已开启 ({comment_text})")
    else:
        if indent == '':  # 只在详情中显示未开启
            lines.append(f"{indent}评论: 未开启")
    
    # 商品信息
    product_info = news_item.get('product_info', {})
    footer_product_info = product_info.get('footer_product_info', {})
    if footer_product_info.get('product_key'):
        lines.append(f"{indent}商品: 已关联 (key: {footer_product_info.get('product_key')})")
    
    # 临时链接
    url = news_item.get('url', '')
    if url:
        lines.append(f"{indent}临时链接: {url}")
    
    return '\n'.join(lines)


def validate_article(article: Dict[str, Any], index: int) -> Optional[str]:
    """
    验证文章必填字段
    
    Args:
        article: 文章数据
        index: 文章索引（从1开始）
        
    Returns:
        错误信息，如果验证通过则返回None
    """
    article_type = article.get('articleType', ARTICLE_TYPE_NEWS)
    
    if article_type == ARTICLE_TYPE_NEWS:
        if not article.get('thumbMediaId'):
            return f"错误：第{index}篇文章为图文消息，必须提供封面图片ID（thumbMediaId）"
    elif article_type == ARTICLE_TYPE_NEWSPIC:
        image_info = article.get('imageInfo')
        if not image_info or not image_info.get('imageList'):
            return f"错误：第{index}篇文章为图片消息，必须提供图片信息（imageInfo.imageList）"
    
    return None


def format_timestamp(timestamp: int) -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: Unix时间戳
        
    Returns:
        格式化后的时间字符串
    """
    if timestamp:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
    return '未知'


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
                        "enum": ["add", "get", "delete", "list", "count", "update", "switch"],
                        "description": "操作类型：add(创建), get(获取), delete(删除), list(列表), count(统计), update(更新), switch(设置/查询草稿箱开关)"
                    },
                    "checkonly": {
                        "type": "boolean",
                        "description": "仅查询开关状态时传true，设置开关时传false或不传（switch操作时使用）"
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
                                "articleType": {"type": "string", "enum": ["news", "newspic"], "description": "文章类型：news(图文消息), newspic(图片消息)，默认为news"},
                                "title": {"type": "string", "description": "文章标题"},
                                "author": {"type": "string", "description": "作者"},
                                "digest": {"type": "string", "description": "摘要"},
                                "content": {"type": "string", "description": "文章内容"},
                                "contentSourceUrl": {"type": "string", "description": "原文链接"},
                                "thumbMediaId": {"type": "string", "description": "封面图片媒体ID（必须是永久MediaID，图文消息时必填）"},
                                "showCoverPic": {"type": "number", "description": "是否显示封面图片"},
                                "needOpenComment": {"type": "number", "description": "是否开启评论，0不打开(默认)，1打开"},
                                "onlyFansCanComment": {"type": "number", "description": "是否粉丝才可评论，0所有人可评论(默认)，1粉丝才可评论"},
                                "picCrop2351": {"type": "string", "description": "图文消息封面裁剪为2.35:1规格的坐标字段，格式：X1_Y1_X2_Y2"},
                                "picCrop11": {"type": "string", "description": "图文消息封面裁剪为1:1规格的坐标字段，格式：X1_Y1_X2_Y2"},
                                "imageInfo": {
                                    "type": "object",
                                    "description": "图片消息里的图片相关信息（图片消息时必需）",
                                    "properties": {
                                        "imageList": {
                                            "type": "array",
                                            "description": "图片列表，最多20张",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "imageMediaId": {"type": "string", "description": "图片素材ID（必须是永久MediaID）"}
                                                },
                                                "required": ["imageMediaId"]
                                            }
                                        }
                                    },
                                    "required": ["imageList"]
                                },
                                "coverInfo": {
                                    "type": "object",
                                    "description": "图片消息的封面信息",
                                    "properties": {
                                        "cropPercentList": {
                                            "type": "array",
                                            "description": "封面裁剪信息",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "ratio": {"type": "string", "description": "裁剪比例，支持：1_1、16_9、2.35_1"},
                                                    "x1": {"type": "string", "description": "左上角X坐标"},
                                                    "y1": {"type": "string", "description": "左上角Y坐标"},
                                                    "x2": {"type": "string", "description": "右下角X坐标"},
                                                    "y2": {"type": "string", "description": "右下角Y坐标"}
                                                }
                                            }
                                        }
                                    }
                                },
                                "productInfo": {
                                    "type": "object",
                                    "description": "商品信息",
                                    "properties": {
                                        "footerProductInfo": {
                                            "type": "object",
                                            "description": "文末插入商品相关信息",
                                            "properties": {
                                                "productKey": {"type": "string", "description": "商品key"}
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["title", "content"]
                        }
                    },
                    "index": {
                        "type": "integer",
                        "description": "要更新的文章在图文消息中的位置（更新时使用，多图文消息时此字段才有意义），第一篇为0"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "偏移量（列表时使用，从0开始）"
                    },
                    "count": {
                        "type": "integer",
                        "description": "数量（列表时使用，取值在1到20之间）"
                    },
                    "noContent": {
                        "type": "boolean",
                        "description": "是否不返回content字段，true表示不返回，false或不传表示正常返回（列表时使用）"
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
            if not articles:
                return "错误：文章内容不能为空"
            
            # 验证并转换文章格式
            formatted_articles = []
            for idx, article in enumerate(articles, 1):
                error = validate_article(article, idx)
                if error:
                    return error
                formatted_articles.append(format_article_data(article))
            
            result = await api_client.add_draft(formatted_articles)
            return f"草稿创建成功！\n草稿ID: {result.get('media_id')}\n包含文章数: {len(articles)}"
        
        elif action == 'get':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            result = await api_client.get_draft(media_id)
            news_items = result.get('news_item', [])
            
            if not news_items:
                return f"获取草稿成功！\n草稿ID: {media_id}\n内容: 无"
            
            articles_text_parts = [
                format_article_info(item, i + 1)
                for i, item in enumerate(news_items)
            ]
            
            articles_text = '\n\n'.join(articles_text_parts)
            return f"获取草稿成功！\n草稿ID: {media_id}\n包含文章数: {len(news_items)}\n\n{articles_text}"
        
        elif action == 'delete':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            await api_client.delete_draft(media_id)
            return f"草稿删除成功！\n草稿ID: {media_id}\n注意：此操作无法撤销，草稿已永久删除。"
        
        elif action == 'list':
            offset = arguments.get('offset', 0)
            count = arguments.get('count', 20)
            no_content = arguments.get('noContent', False)
            
            if not (COUNT_MIN <= count <= COUNT_MAX):
                return f"错误：count参数必须在{COUNT_MIN}到{COUNT_MAX}之间"
            
            request_data = {'offset': offset, 'count': count}
            if no_content:
                request_data['no_content'] = 1
            
            result = await api_client._request('POST', '/cgi-bin/draft/batchget', data=request_data)
            
            items = result.get('item', [])
            total_count = result.get('total_count', 0)
            item_count = result.get('item_count', len(items))
            
            if not items:
                return f"草稿列表为空（总数: {total_count}）"
            
            draft_list_parts = []
            for i, item in enumerate(items):
                media_id = item.get('media_id', '')
                update_time = item.get('update_time', 0)
                content = item.get('content', {})
                news_items = content.get('news_item', [])
                
                draft_info = f"{offset + i + 1}. 草稿ID: {media_id}\n"
                draft_info += f"   更新时间: {format_timestamp(update_time)}\n"
                
                if news_items:
                    draft_info += f"   包含文章数: {len(news_items)}\n"
                    for j, news_item in enumerate(news_items):
                        draft_info += f"\n{format_article_info(news_item, j + 1, indent='   ')}"
                else:
                    draft_info += "   内容: 无（可能设置了no_content参数）\n"
                
                draft_list_parts.append(draft_info)
            
            draft_list = '\n\n'.join(draft_list_parts)
            return f"草稿列表 ({offset + 1}-{offset + item_count}/{total_count}):\n\n{draft_list}"
        
        elif action == 'count':
            result = await api_client._request('GET', '/cgi-bin/draft/count')
            total_count = result.get('total_count', 0)
            return f"草稿统计信息：\n草稿总数: {total_count} 个"
        
        elif action == 'update':
            media_id = arguments.get('mediaId')
            if not media_id:
                return "错误：草稿ID不能为空"
            
            articles = arguments.get('articles')
            if not articles:
                return "错误：文章内容不能为空"
            
            specified_index = arguments.get('index')
            
            if specified_index is not None:
                if len(articles) > 1:
                    return "错误：指定index时，只能更新一篇文章"
                
                article_data = format_article_data(articles[0])
                update_data = {
                    'media_id': media_id,
                    'index': specified_index,
                    'articles': article_data
                }
                await api_client._request('POST', '/cgi-bin/draft/update', data=update_data)
                return f"草稿更新成功！\n草稿ID: {media_id}\n更新文章索引: {specified_index}"
            else:
                # 批量更新
                for idx, article in enumerate(articles):
                    article_data = format_article_data(article)
                    update_data = {
                        'media_id': media_id,
                        'index': idx,
                        'articles': article_data
                    }
                    await api_client._request('POST', '/cgi-bin/draft/update', data=update_data)
                
                return f"草稿更新成功！\n草稿ID: {media_id}\n更新文章数: {len(articles)}"
        
        elif action == 'switch':
            checkonly = arguments.get('checkonly', False)
            result = await api_client.draft_switch(checkonly=checkonly)
            
            if checkonly:
                is_open = result.get('is_open', 0)
                status_text = "已开启" if is_open == 1 else "已关闭"
                return f"草稿箱开关状态查询成功！\n当前状态: {status_text} (is_open={is_open})"
            else:
                is_open = result.get('is_open', 0)
                if is_open == 1:
                    return "草稿箱开关已成功开启！\n注意：此开关开启后不可逆，无法从开启状态回到关闭状态。"
                else:
                    return "草稿箱开关设置完成。\n当前状态: 关闭 (is_open=0)"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f'草稿操作失败: {error_detail}', exc_info=True)
        return f"草稿操作失败: {error_detail}"
