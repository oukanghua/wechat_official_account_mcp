from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class WechatMessage:
    """微信消息基础类"""
    msg_id: str
    msg_type: str
    from_user: str
    to_user: str
    create_time: int
    content: Optional[str] = None
    media_id: Optional[str] = None
    pic_url: Optional[str] = None
    media_url: Optional[str] = None
    format: Optional[str] = None
    recognition: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    event: Optional[str] = None
    event_key: Optional[str] = None
    ticket: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    precision: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WechatMessage':
        """
        从字典创建消息对象
        
        Args:
            data: 消息数据字典
            
        Returns:
            WechatMessage: 消息对象
        """
        # 基础字段
        msg_id = data.get('MsgId', '')
        msg_type = data.get('MsgType', '').lower()
        from_user = data.get('FromUserName', '')
        to_user = data.get('ToUserName', '')
        create_time = data.get('CreateTime', 0)
        
        # 根据消息类型处理不同字段
        content = data.get('Content', '')
        media_id = data.get('MediaId', '')
        
        # 图片消息字段
        pic_url = data.get('PicUrl', '')
        
        # 语音消息字段
        format = data.get('Format', '')
        recognition = data.get('Recognition', '')
        
        # 视频/短视频消息字段
        media_url = data.get('MediaUrl', '')
        description = data.get('Description', '')
        
        # 链接消息字段
        title = data.get('Title', '')
        url = data.get('Url', '')
        
        # 事件消息字段
        event = data.get('Event', '')
        event_key = data.get('EventKey', '')
        ticket = data.get('Ticket', '')
        
        # 位置消息字段
        latitude = data.get('Location_X')
        longitude = data.get('Location_Y')
        precision = data.get('Scale')
        
        return cls(
            msg_id=msg_id,
            msg_type=msg_type,
            from_user=from_user,
            to_user=to_user,
            create_time=create_time,
            content=content,
            media_id=media_id,
            pic_url=pic_url,
            media_url=media_url,
            format=format,
            recognition=recognition,
            title=title,
            description=description,
            url=url,
            event=event,
            event_key=event_key,
            ticket=ticket,
            latitude=latitude,
            longitude=longitude,
            precision=precision
        )