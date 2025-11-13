"""
模板工具 - 根据P站样式模板生成公众号文章内容
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


def load_template(template_name: str = "phub_template.html") -> str:
    """
    加载模板文件
    
    Args:
        template_name: 模板文件名
        
    Returns:
        模板内容
    """
    try:
        # 获取项目根目录
        script_dir = Path(__file__).parent.parent
        template_path = script_dir / "templates" / template_name
        
        if not template_path.exists():
            logger.error(f"模板文件不存在: {template_path}")
            return ""
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载模板失败: {e}", exc_info=True)
        return ""


def format_number(index: int) -> str:
    """
    格式化数字为两位数字符串（01, 02, ...）
    
    Args:
        index: 索引（从0开始）
        
    Returns:
        格式化后的数字字符串
    """
    return f"{index + 1:02d}"


def escape_html(text: str) -> str:
    """转义HTML特殊字符"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


def generate_html_from_template(content_data: Dict[str, Any], template_name: str = "phub_template.html") -> str:
    """
    根据模板和内容数据生成HTML
    
    Args:
        content_data: 内容数据字典
        template_name: 模板文件名
        
    Returns:
        生成的HTML内容
    """
    template = load_template(template_name)
    if not template:
        return "错误：无法加载模板文件"
    
    try:
        import re
        
        # 构建HTML内容
        html_parts = []
        
        # 提取模板的前半部分（从开始到article-container）
        start_match = re.search(r'(.*?)<div class="article-container">', template, re.DOTALL)
        if start_match:
            html_parts.append(start_match.group(1))
            html_parts.append('    <div class="article-container">\n')
        
        # 标题
        title = content_data.get('title', '')
        html_parts.append(f'        <h1>{escape_html(title)}</h1>\n        ')
        
        # 顶部图片
        image = content_data.get('image', '')
        if image:
            html_parts.append(f'''        <div class="image-container">
            <div class="image-placeholder">{escape_html(image)}</div>
        </div>
        ''')
        
        # 介绍段落
        intro = content_data.get('intro', '')
        if intro:
            html_parts.append(f'        <p>{escape_html(intro)}</p>\n        ')
        
        # 警告提示
        warning = content_data.get('warning', '')
        if warning:
            html_parts.append(f'''        <div class="warning-note">
            <strong>注意：</strong>{escape_html(warning)}
        </div>
        ''')
        
        # 处理章节
        sections = content_data.get('sections', [])
        for idx, section in enumerate(sections):
            section_title = section.get('title', '')
            html_parts.append(f'        <h2 data-number="{format_number(idx)}">{escape_html(section_title)}</h2>\n        ')
            
            # 章节内容
            if section.get('content'):
                html_parts.append(f'        <p>{escape_html(section.get("content"))}</p>\n        ')
            
            # 统计数据
            if section.get('stats'):
                html_parts.append('        <div class="stats-container">\n')
                for stat in section.get('stats', []):
                    html_parts.append(f'            <div class="stat-item">\n')
                    html_parts.append(f'                <div class="stat-number">{escape_html(str(stat.get("number", "")))}</div>\n')
                    html_parts.append(f'                <div class="stat-label">{escape_html(stat.get("label", ""))}</div>\n')
                    html_parts.append(f'            </div>\n')
                html_parts.append('        </div>\n        ')
            
            # 引用块
            if section.get('quote'):
                html_parts.append(f'''        <div class="quote-block">
            "{escape_html(section.get("quote"))}"
        </div>
        ''')
            
            # 功能网格
            if section.get('features'):
                html_parts.append('        <div class="feature-grid">\n')
                for feature in section.get('features', []):
                    html_parts.append(f'            <div class="feature-item">\n')
                    html_parts.append(f'                <span class="bold-text">{escape_html(feature.get("title", ""))}</span><br>\n')
                    html_parts.append(f'                {escape_html(feature.get("description", ""))}\n')
                    html_parts.append(f'            </div>\n')
                html_parts.append('        </div>\n        ')
            
            # 代码块（不转义）
            if section.get('code'):
                code_content = section.get('code')
                html_parts.append(f'        <div class="code-block">\n{code_content}\n        </div>\n        ')
            
            # 进度条
            if section.get('progress') is not None:
                progress = section.get('progress')
                html_parts.append(f'''        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress}%"></div>
            </div>
            <div>技术成熟度：{progress}%</div>
        </div>
        ''')
            
            # 章节图片
            if section.get('image'):
                html_parts.append(f'''        <div class="image-container">
            <div class="image-placeholder">{escape_html(section.get("image"))}</div>
        </div>
        ''')
        
        # 标签部分
        tags = content_data.get('tags', [])
        if tags:
            html_parts.append(f'        <h2 data-number="{format_number(len(sections))}">技术标签</h2>\n        ')
            html_parts.append('        <div>\n')
            for tag in tags:
                html_parts.append(f'            <span class="tag">{escape_html(tag)}</span>\n')
            html_parts.append('        </div>\n        ')
        
        # 行动按钮
        action_button = content_data.get('actionButton')
        if action_button:
            button_text = action_button.get('text', '')
            button_url = action_button.get('url', '')
            html_parts.append(f'        <a href="{escape_html(button_url)}" class="action-button">{escape_html(button_text)}</a>\n        ')
        
        # 页脚
        footer = content_data.get('footer', [])
        if footer:
            html_parts.append('        <div class="footer">\n')
            for footer_line in footer:
                html_parts.append(f'            <p>{escape_html(footer_line)}</p>\n')
            html_parts.append('        </div>\n        ')
        
        # 结束部分（从</div>到</body>）
        html_parts.append('    </div>\n\n')
        
        # 提取脚本部分
        script_match = re.search(r'(<script>.*?</script>)', template, re.DOTALL)
        if script_match:
            html_parts.append(script_match.group(1))
            html_parts.append('\n')
        
        # 提取结束标签
        end_match = re.search(r'</body>', template)
        if end_match:
            html_parts.append('</body>')
        
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f"生成HTML失败: {e}", exc_info=True)
        import traceback
        return f"错误：生成HTML时出错 - {str(e)}\n\n{traceback.format_exc()}"


def register_template_tools() -> List[Tool]:
    """注册模板工具"""
    return [
        Tool(
            name="wechat_template",
            description="根据P站样式模板生成公众号文章HTML内容。当用户说'使用p站模板'或'使用phub模板'时，使用此工具根据提供的内容生成符合P站样式的HTML文章。",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate", "get_template"],
                        "description": "操作类型：generate(根据内容生成HTML), get_template(获取模板内容)"
                    },
                    "title": {
                        "type": "string",
                        "description": "文章标题"
                    },
                    "intro": {
                        "type": "string",
                        "description": "文章介绍段落（可选）"
                    },
                    "image": {
                        "type": "string",
                        "description": "顶部图片占位符文本（可选）"
                    },
                    "warning": {
                        "type": "string",
                        "description": "警告提示文本（可选）"
                    },
                    "sections": {
                        "type": "array",
                        "description": "文章章节列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "章节标题"},
                                "content": {"type": "string", "description": "章节正文内容"},
                                "stats": {
                                    "type": "array",
                                    "description": "统计数据（可选）",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "number": {"type": "string", "description": "统计数字"},
                                            "label": {"type": "string", "description": "统计标签"}
                                        }
                                    }
                                },
                                "quote": {"type": "string", "description": "引用文本（可选）"},
                                "features": {
                                    "type": "array",
                                    "description": "功能列表（可选）",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string", "description": "功能标题"},
                                            "description": {"type": "string", "description": "功能描述"}
                                        }
                                    }
                                },
                                "code": {"type": "string", "description": "代码块内容（可选）"},
                                "progress": {"type": "number", "description": "进度条百分比（0-100，可选）"},
                                "image": {"type": "string", "description": "章节图片占位符文本（可选）"}
                            },
                            "required": ["title"]
                        }
                    },
                    "tags": {
                        "type": "array",
                        "description": "标签列表（可选）",
                        "items": {"type": "string"}
                    },
                    "actionButton": {
                        "type": "object",
                        "description": "行动按钮（可选）",
                        "properties": {
                            "text": {"type": "string", "description": "按钮文本"},
                            "url": {"type": "string", "description": "按钮链接"}
                        }
                    },
                    "footer": {
                        "type": "array",
                        "description": "页脚文本列表（可选）",
                        "items": {"type": "string"}
                    },
                    "templateName": {
                        "type": "string",
                        "description": "模板文件名（默认为phub_template.html）"
                    }
                },
                "required": ["action"]
            }
        )
    ]


async def handle_template_tool(arguments: Dict[str, Any]) -> str:
    """处理模板工具"""
    action = arguments.get('action')
    
    try:
        if action == 'generate':
            # 构建内容数据
            content_data = {
                'title': arguments.get('title', ''),
                'intro': arguments.get('intro', ''),
                'image': arguments.get('image', ''),
                'warning': arguments.get('warning', ''),
                'sections': arguments.get('sections', []),
                'tags': arguments.get('tags', []),
                'actionButton': arguments.get('actionButton'),
                'footer': arguments.get('footer', [])
            }
            
            template_name = arguments.get('templateName', 'phub_template.html')
            html = generate_html_from_template(content_data, template_name)
            
            if html.startswith('错误'):
                return html
            
            return f"HTML内容生成成功！\n\n{html}"
        
        elif action == 'get_template':
            template_name = arguments.get('templateName', 'phub_template.html')
            template = load_template(template_name)
            
            if not template:
                return "错误：无法加载模板文件"
            
            return f"模板内容：\n\n{template}"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f'模板操作失败: {error_detail}', exc_info=True)
        return f"模板操作失败: {error_detail}"

