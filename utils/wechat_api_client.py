import requests
import json
import time
import os
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class WechatApiClient:
    """微信公众号API客户端"""
    
    def __init__(self, app_id: str, app_secret: str, proxy: str = None):
        """
        初始化微信API客户端
        
        Args:
            app_id: 微信公众号AppID
            app_secret: 微信公众号AppSecret
            proxy: 代理地址，默认为None
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expire_time = 0
        self.proxy = proxy or os.environ.get('WECHAT_API_PROXY', 'api.weixin.qq.com')
        self.base_url = f'https://{self.proxy}'
        self.timeout = int(os.environ.get('WECHAT_API_TIMEOUT', 30))
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取访问令牌
        
        Args:
            force_refresh: 是否强制刷新令牌
            
        Returns:
            str: 访问令牌
        """
        # 检查是否需要刷新令牌
        if not force_refresh and self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        try:
            url = f'{self.base_url}/cgi-bin/token'
            params = {
                'grant_type': 'client_credential',
                'appid': self.app_id,
                'secret': self.app_secret
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response_data = response.json()
            
            if 'errcode' in response_data and response_data['errcode'] != 0:
                logger.error(f'获取访问令牌失败: {response_data}')
                raise Exception(f'获取访问令牌失败: {response_data.get("errmsg", "未知错误")}')
            
            self.access_token = response_data['access_token']
            # 设置过期时间，提前10分钟过期
            expire_in = response_data.get('expires_in', 7200)
            self.token_expire_time = time.time() + expire_in - 600
            
            logger.info(f'成功获取访问令牌，有效期至: {self.token_expire_time}')
            return self.access_token
            
        except Exception as e:
            logger.error(f'获取访问令牌异常: {str(e)}')
            raise
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Any = None, 
                 headers: Dict = None, need_token: bool = True, files: Dict = None) -> Dict:
        """
        通用请求方法
        
        Args:
            method: 请求方法 GET/POST
            endpoint: API端点
            params: URL参数
            data: 请求数据
            headers: 请求头
            need_token: 是否需要添加访问令牌
            files: 文件数据
            
        Returns:
            Dict: 响应数据
        """
        try:
            url = f'{self.base_url}{endpoint}'
            
            # 添加访问令牌
            if need_token:
                token = self.get_access_token()
                if params is None:
                    params = {}
                params['access_token'] = token
            
            # 发送请求
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                files=files
            )
            
            # 解析响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {'content': response.text}
            
            # 检查错误
            if isinstance(response_data, dict) and 'errcode' in response_data and response_data['errcode'] != 0:
                logger.error(f'API请求失败: {response_data}')
                raise Exception(f'API请求失败: {response_data.get("errmsg", "未知错误")}')
            
            return response_data
            
        except Exception as e:
            logger.error(f'请求异常: {str(e)}')
            raise
    
    # 素材管理相关方法
    def upload_permanent_media(self, media_type: str, file_path: str = None, file_content: bytes = None, 
                             title: str = None, introduction: str = None) -> Dict:
        """
        上传永久素材
        
        Args:
            media_type: 素材类型 (image, voice, video, thumb)
            file_path: 文件路径
            file_content: 文件内容（字节）
            title: 视频素材标题
            introduction: 视频素材描述
            
        Returns:
            Dict: 上传结果
        """
        endpoint = f'/cgi-bin/material/add_material'
        params = {'type': media_type}
        
        files = {}
        if file_path:
            files['media'] = open(file_path, 'rb')
        elif file_content:
            files['media'] = ('file', file_content)
        else:
            raise ValueError('必须提供file_path或file_content')
        
        # 视频素材需要额外的描述信息
        if media_type == 'video' and (title or introduction):
            description = json.dumps({
                'title': title or '',
                'introduction': introduction or ''
            }, ensure_ascii=False)
            files['description'] = description
        
        try:
            return self._request('POST', endpoint, params=params, files=files)
        finally:
            # 关闭文件
            if 'media' in files and hasattr(files['media'], 'close'):
                files['media'].close()
    
    def get_permanent_media(self, media_id: str) -> bytes:
        """
        获取永久素材
        
        Args:
            media_id: 素材ID
            
        Returns:
            bytes: 素材内容
        """
        endpoint = '/cgi-bin/material/get_material'
        data = json.dumps({'media_id': media_id}, ensure_ascii=False)
        
        url = f'{self.base_url}{endpoint}?access_token={self.get_access_token()}'
        response = requests.post(url, data=data, timeout=self.timeout)
        
        # 检查是否返回错误信息
        try:
            json_response = response.json()
            if 'errcode' in json_response and json_response['errcode'] != 0:
                raise Exception(f'获取素材失败: {json_response.get("errmsg", "未知错误")}')
        except json.JSONDecodeError:
            # 非JSON响应，说明是文件内容
            pass
        
        return response.content
    
    def delete_permanent_media(self, media_id: str) -> Dict:
        """
        删除永久素材
        
        Args:
            media_id: 素材ID
            
        Returns:
            Dict: 删除结果
        """
        endpoint = '/cgi-bin/material/del_material'
        data = json.dumps({'media_id': media_id}, ensure_ascii=False)
        
        return self._request('POST', endpoint, data=data, need_token=True)
    
    # 草稿管理相关方法
    def add_draft(self, articles: list) -> Dict:
        """
        创建草稿
        
        Args:
            articles: 文章列表
            
        Returns:
            Dict: 创建结果
        """
        endpoint = '/cgi-bin/draft/add'
        data = json.dumps({'articles': articles}, ensure_ascii=False)
        
        return self._request('POST', endpoint, data=data)
    
    def get_draft(self, media_id: str) -> Dict:
        """
        获取草稿
        
        Args:
            media_id: 草稿ID
            
        Returns:
            Dict: 草稿内容
        """
        endpoint = '/cgi-bin/draft/get'
        data = json.dumps({'media_id': media_id}, ensure_ascii=False)
        
        return self._request('POST', endpoint, data=data)
    
    def delete_draft(self, media_id: str) -> Dict:
        """
        删除草稿
        
        Args:
            media_id: 草稿ID
            
        Returns:
            Dict: 删除结果
        """
        endpoint = '/cgi-bin/draft/delete'
        data = json.dumps({'media_id': media_id}, ensure_ascii=False)
        
        return self._request('POST', endpoint, data=data)
    
    # 发布相关方法
    def publish_draft(self, media_id: str, to_group: int = None, to_tag: int = None) -> Dict:
        """
        发布草稿
        
        Args:
            media_id: 草稿ID
            to_group: 分组ID（可选）
            to_tag: 标签ID（可选）
            
        Returns:
            Dict: 发布结果
        """
        endpoint = '/cgi-bin/freepublish/submit'
        
        data = {
            'media_id': media_id
        }
        
        if to_group:
            data['to_group'] = to_group
        elif to_tag:
            data['to_tag'] = to_tag
        
        return self._request('POST', endpoint, data=json.dumps(data, ensure_ascii=False))
    
    # 客服消息相关方法
    def send_custom_message(self, touser: str, msgtype: str, message_data: Dict) -> Dict:
        """
        发送客服消息
        
        Args:
            touser: 用户OpenID
            msgtype: 消息类型
            message_data: 消息数据
            
        Returns:
            Dict: 发送结果
        """
        endpoint = '/cgi-bin/message/custom/send'
        
        data = {
            'touser': touser,
            'msgtype': msgtype,
            msgtype: message_data
        }
        
        return self._request('POST', endpoint, data=json.dumps(data, ensure_ascii=False))
    
    # 用户管理相关方法
    def get_user_info(self, open_id: str, lang: str = 'zh_CN') -> Dict:
        """
        获取用户基本信息
        
        Args:
            open_id: 用户的openid
            lang: 返回国家地区语言版本，zh_CN 简体，zh_TW 繁体，en 英语
            
        Returns:
            Dict: 用户信息
        """
        endpoint = '/cgi-bin/user/info'
        params = {
            'openid': open_id,
            'lang': lang
        }
        
        return self._request('GET', endpoint, params=params)
    
    # 临时素材相关方法
    def upload_media(self, media_type: str, file_path: str = None, file_content: bytes = None, 
                    filename: str = 'media') -> Dict:
        """
        上传临时素材
        
        Args:
            media_type: 媒体类型 (image, voice, video, thumb)
            file_path: 文件路径
            file_content: 文件内容（字节）
            filename: 文件名
            
        Returns:
            Dict: 上传结果
        """
        endpoint = '/cgi-bin/media/upload'
        params = {'type': media_type}
        
        files = {}
        if file_path:
            files['media'] = open(file_path, 'rb')
        elif file_content:
            files['media'] = (filename, file_content)
        else:
            raise ValueError('必须提供file_path或file_content')
        
        try:
            return self._request('POST', endpoint, params=params, files=files)
        finally:
            # 关闭文件
            if 'media' in files and hasattr(files['media'], 'close'):
                files['media'].close()
    
    def get_media(self, media_id: str) -> bytes:
        """
        获取临时素材
        
        Args:
            media_id: 素材ID
            
        Returns:
            bytes: 素材内容
        """
        endpoint = '/cgi-bin/media/get'
        params = {'media_id': media_id}
        
        url = f'{self.base_url}{endpoint}?access_token={self.get_access_token()}'
        response = requests.get(url, params=params, timeout=self.timeout, stream=True)
        
        # 检查是否返回错误信息
        try:
            json_response = response.json()
            if 'errcode' in json_response and json_response['errcode'] != 0:
                raise Exception(f'获取素材失败: {json_response.get("errmsg", "未知错误")}')
        except json.JSONDecodeError:
            # 非JSON响应，说明是文件内容
            pass
        
        return response.content
    
    # 图文消息相关方法
    def upload_news(self, articles: list) -> Dict:
        """
        上传图文消息素材
        
        Args:
            articles: 图文消息列表
            
        Returns:
            Dict: 上传结果
        """
        endpoint = '/cgi-bin/material/add_news'
        data = json.dumps({'articles': articles}, ensure_ascii=False)
        
        return self._request('POST', endpoint, data=data)
    
    def upload_img(self, file_path: str = None, file_content: bytes = None) -> Dict:
        """
        上传图文消息内的图片获取URL
        
        Args:
            file_path: 图片文件路径
            file_content: 图片文件内容（字节）
            
        Returns:
            Dict: 上传结果，包含图片URL
        """
        endpoint = '/cgi-bin/media/uploadimg'
        
        files = {}
        if file_path:
            files['media'] = open(file_path, 'rb')
        elif file_content:
            files['media'] = ('image.jpg', file_content)
        else:
            raise ValueError('必须提供file_path或file_content')
        
        try:
            # 这个接口不需要access_token参数
            return self._request('POST', endpoint, files=files, need_token=False)
        finally:
            # 关闭文件
            if 'media' in files and hasattr(files['media'], 'close'):
                files['media'].close()