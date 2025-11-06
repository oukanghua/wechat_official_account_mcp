"""
微信公众号消息接收服务器
独立运行，用于接收和处理微信公众号消息
集成 dify_wechat_plugin 的超时和重试机制
"""
import logging
import os
import sys
import threading
import time
from typing import Any
from flask import Flask, request, Response
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 将项目根目录添加到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 导入消息处理模块
from server.handlers.text import TextMessageHandler
from server.handlers.image import ImageMessageHandler
from server.handlers.voice import VoiceMessageHandler
from server.handlers.link import LinkMessageHandler
from server.handlers.event import EventMessageHandler
from server.handlers.unsupported import UnsupportedMessageHandler
from server.utils.message_parser import MessageParser
from shared.utils.wechat_crypto import WechatMessageCrypto
from shared.storage.auth_manager import AuthManager
from server.utils.retry_tracker import MessageStatusTracker
from server.utils.waiting_manager import UserWaitingManager
from server.custom_message import WechatCustomMessageSender

# 初始化认证管理器
auth_manager = AuthManager()

# 启动时从环境变量加载配置（如果数据库中没有配置）
def _load_config_from_env():
    """从环境变量加载配置到数据库"""
    # 检查数据库中是否已有配置
    existing_config = auth_manager.get_config()
    if existing_config:
        logger.info("已存在数据库配置，跳过环境变量加载")
        return
    
    # 从环境变量读取配置
    app_id = os.getenv('WECHAT_APP_ID', '')
    app_secret = os.getenv('WECHAT_APP_SECRET', '')
    token = os.getenv('WECHAT_TOKEN', '')
    encoding_aes_key = os.getenv('WECHAT_ENCODING_AES_KEY', '')
    
    if app_id and app_secret:
        try:
            auth_manager.set_config({
                'app_id': app_id,
                'app_secret': app_secret,
                'token': token,
                'encoding_aes_key': encoding_aes_key
            })
            logger.info(f"已从环境变量加载配置: app_id={app_id}")
        except Exception as e:
            logger.error(f"从环境变量加载配置失败: {str(e)}")
    else:
        logger.warning("环境变量中未找到 WECHAT_APP_ID 或 WECHAT_APP_SECRET")

# 启动时加载配置
_load_config_from_env()

# 消息处理器映射
MESSAGE_HANDLERS = {
    'text': TextMessageHandler(),
    'image': ImageMessageHandler(),
    'voice': VoiceMessageHandler(),
    'link': LinkMessageHandler(),
    'event': EventMessageHandler(),
}

# 默认超时和响应设置
DEFAULT_HANDLER_TIMEOUT = 5.0  # 默认超时时间 5.0 秒（固定值，微信要求）
DEFAULT_TEMP_RESPONSE = "内容生成耗时较长，请稍等..."  # 默认临时响应消息
DEFAULT_RETRY_WAIT_TIMEOUT_RATIO = 0.7  # 默认重试等待超时系数
RETRY_WAIT_TIMEOUT = DEFAULT_HANDLER_TIMEOUT * DEFAULT_RETRY_WAIT_TIMEOUT_RATIO

# 清除历史标识消息
CLEAR_HISTORY_MESSAGE = "/clear"

# 新增默认配置项
DEFAULT_ENABLE_CUSTOM_MESSAGE = False  # 默认不启用客服消息
DEFAULT_CONTINUE_MESSAGE = "生成答复中，继续等待请回复1"
DEFAULT_MAX_CONTINUE_COUNT = 2


def verify_signature(signature: str, timestamp: str, nonce: str, echostr: str, token: str) -> str:
    """
    验证微信服务器签名
    
    Args:
        signature: 微信传来的签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        token: 配置的 token
        
    Returns:
        验证成功返回 echostr，失败返回空字符串
    """
    import hashlib
    
    # 按照字典序排序
    temp_list = [token, timestamp, nonce]
    temp_list.sort()
    
    # 拼接并加密
    temp_str = ''.join(temp_list)
    hash_str = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
    
    # 验证签名
    if hash_str == signature:
        return echostr
    return ''


@app.route('/wechat', methods=['GET'])
def wechat_get():
    """处理微信服务器验证请求"""
    try:
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 获取配置
        config = auth_manager.get_config()
        if not config:
            logger.error("未配置微信公众号信息")
            return Response('未配置', status=500)
        
        token = config.get('token', '')
        if not token:
            logger.error("未配置 token")
            return Response('未配置 token', status=500)
        
        # 验证签名
        result = verify_signature(signature, timestamp, nonce, echostr, token)
        
        if result:
            logger.info("微信服务器验证成功")
            return Response(result, status=200)
        else:
            logger.warning("微信服务器验证失败")
            return Response('验证失败', status=403)
    
    except Exception as e:
        logger.error(f"处理验证请求失败: {str(e)}", exc_info=True)
        return Response('服务器错误', status=500)


def _get_config_value(key: str, default):
    """从环境变量获取配置值"""
    value = os.getenv(key, '')
    if value:
        return value
    return default


@app.route('/wechat', methods=['POST'])
def wechat_post():
    """处理微信消息（带超时和重试机制）"""
    try:
        # 获取配置
        config = auth_manager.get_config()
        if not config:
            logger.error("未配置微信公众号信息")
            return Response('未配置', status=500)
        
        # 获取配置项
        temp_response_message = _get_config_value('WECHAT_TIMEOUT_MESSAGE', DEFAULT_TEMP_RESPONSE)
        enable_custom_message = _get_config_value('WECHAT_ENABLE_CUSTOM_MESSAGE', 'false').lower() == 'true'
        continue_waiting_message = _get_config_value('WECHAT_CONTINUE_WAITING_MESSAGE', DEFAULT_CONTINUE_MESSAGE)
        max_continue_count = int(_get_config_value('WECHAT_MAX_CONTINUE_COUNT', DEFAULT_MAX_CONTINUE_COUNT))
        retry_wait_timeout_ratio = float(_get_config_value('WECHAT_RETRY_WAIT_TIMEOUT_RATIO', DEFAULT_RETRY_WAIT_TIMEOUT_RATIO))
        retry_wait_timeout_ratio = max(0.1, min(1.0, retry_wait_timeout_ratio))
        retry_wait_timeout = DEFAULT_HANDLER_TIMEOUT * retry_wait_timeout_ratio
        
        # 创建加密工具
        crypto = WechatMessageCrypto(
            token=config.get('token', ''),
            encoding_aes_key=config.get('encoding_aes_key', ''),
            app_id=config.get('app_id', '')
        )
        
        # 解密消息
        try:
            msg_signature = request.args.get('msg_signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config.get('encoding_aes_key'):
                # 加密模式
                decrypted_xml = crypto.decrypt_message(
                    request.data.decode('utf-8'),
                    msg_signature,
                    timestamp,
                    nonce
                )
            else:
                # 明文模式
                decrypted_xml = request.data.decode('utf-8')
        
        except Exception as e:
            logger.error(f"消息解密失败: {str(e)}")
            return Response('解密失败', status=400)
        
        # 解析消息
        message = MessageParser.parse_xml(decrypted_xml)
        
        # 获取处理器
        handler = MESSAGE_HANDLERS.get(message.msg_type, UnsupportedMessageHandler())
        
        # 处理清除历史记录指令
        if message.content == CLEAR_HISTORY_MESSAGE:
            # 简化处理：直接回复
            result_message = "历史记录已清除"
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=result_message
            )
            if config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')
        
        # 使用 MessageStatusTracker 跟踪消息状态
        message_status = MessageStatusTracker.track_message(message)
        retry_count = message_status.get('retry_count', 0)
        
        # 检查是否为继续等待请求
        if (message.content == "1" and 
            not enable_custom_message and 
            UserWaitingManager.is_user_waiting(message.from_user)):
            waiting_info = UserWaitingManager.get_waiting_info(message.from_user)
            if waiting_info:
                message_status['is_continue_waiting'] = True
                message_status['original_waiting_info'] = waiting_info
                logger.info(f"检测到继续等待请求，当前等待次数: {waiting_info['continue_count']}")
        
        # 初始化结果返回标志
        message_status['result_returned'] = False
        
        # 处理重试请求
        if retry_count > 0:
            logger.info(f"微信重试请求: 第{retry_count}次")
            return _handle_retry(
                message, message_status, retry_count,
                temp_response_message, enable_custom_message,
                continue_waiting_message, max_continue_count,
                crypto, request, config, retry_wait_timeout
            )
        
        # 处理第一次请求
        return _handle_first_request(
            message, message_status, config,
            handler, enable_custom_message, crypto, request, retry_wait_timeout
        )
    
    except Exception as e:
        logger.error(f"处理消息失败: {str(e)}", exc_info=True)
        return Response('', status=200)  # 返回空响应避免微信重试


def _handle_first_request(message, message_status, config, handler, enable_custom_message, 
                         crypto: WechatMessageCrypto, request, retry_wait_timeout: float):
    """处理第一次请求"""
    # 检查是否为继续等待请求
    if message_status.get('is_continue_waiting', False):
        continue_waiting_message = _get_config_value('WECHAT_CONTINUE_WAITING_MESSAGE', DEFAULT_CONTINUE_MESSAGE)
        max_continue_count = int(_get_config_value('WECHAT_MAX_CONTINUE_COUNT', DEFAULT_MAX_CONTINUE_COUNT))
        return _handle_continue_waiting_retry(
            message, message_status, 0,
            continue_waiting_message, max_continue_count,
            crypto, request, retry_wait_timeout
        )
    
    # 创建完成事件
    completion_event = threading.Event()
    message_status['completion_event'] = completion_event
    
    # 创建重试完成事件，用于通知客服消息线程
    retry_completion_event = threading.Event()
    message_status['retry_completion_event'] = retry_completion_event
    
    # 初始化客服消息跳过标志为 False
    message_status['skip_custom_message'] = False
    
    # 发送"正在输入"状态
    if enable_custom_message:
        app_id = config.get('app_id', '')
        app_secret = config.get('app_secret', '')
        wechat_api_proxy_url = _get_config_value('WECHAT_API_PROXY_URL', 'api.weixin.qq.com')
        sender = WechatCustomMessageSender(app_id, app_secret, wechat_api_proxy_url)
        sender.set_typing_status(message.from_user, True)
    
    # 启动异步处理线程
    thread = threading.Thread(
        target=_async_process_message,
        args=(handler, message, config, message_status, completion_event),
        daemon=True,
        name=f"Msg-Processor-{message.from_user}"
    )
    
    # 记录处理开始时间并启动线程
    thread.start()
    
    # 等待处理完成或超时
    is_completed = completion_event.wait(timeout=DEFAULT_HANDLER_TIMEOUT)
    
    if is_completed:
        # 结束"正在输入"状态
        if enable_custom_message:
            sender.set_typing_status(message.from_user, False)
        
        # AI 处理完成，直接返回结果
        response_content = message_status.get('result', '') or "抱歉，处理结果为空"
        MessageStatusTracker.mark_result_returned(message)
        
        response_xml = MessageParser.build_text_reply(
            to_user=message.from_user,
            from_user=message.to_user,
            content=response_content
        )
        
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        if config.get('encoding_aes_key'):
            encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
            return Response(encrypted_response, mimetype='application/xml')
        else:
            return Response(response_xml, mimetype='application/xml')
    else:
        # 处理超时，启用重试机制
        logger.info("AI 处理超时，启用重试机制")
        
        if enable_custom_message:
            async_thread = threading.Thread(
                target=_wait_and_send_custom_message,
                args=(message, message_status, config, completion_event),
                daemon=True,
                name=f"CustomerMsgSender-{message.from_user}"
            )
            async_thread.start()
        
        return Response("", status=500)


def _handle_retry(message, message_status, retry_count, temp_message, enable_custom_message,
                 continue_waiting_message, max_continue_count, crypto: WechatMessageCrypto,
                 request, config, retry_wait_timeout: float):
    """处理重试请求"""
    # 检查是否为继续等待消息
    if message_status.get('is_continue_waiting', False):
        return _handle_continue_waiting_retry(
            message, message_status, retry_count,
            continue_waiting_message, max_continue_count,
            crypto, request, retry_wait_timeout
        )
    
    # 获取完成事件
    completion_event = message_status.get('completion_event')
    
    # 直接等待处理完成或超时
    is_completed = False
    if completion_event:
        is_completed = completion_event.wait(timeout=retry_wait_timeout)
    
    if is_completed or message_status.get('is_completed', False):
        # AI 处理完成，返回结果
        response_content = message_status.get('result', '') or "抱歉，处理结果为空"
        
        if not MessageStatusTracker.mark_result_returned(message):
            return Response("", status=200)
        
        message_status['skip_custom_message'] = True
        retry_completion_event = message_status.get('retry_completion_event')
        if retry_completion_event:
            retry_completion_event.set()
        
        response_xml = MessageParser.build_text_reply(
            to_user=message.from_user,
            from_user=message.to_user,
            content=response_content
        )
        
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        if config.get('encoding_aes_key'):
            encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
            return Response(encrypted_response, mimetype='application/xml')
        else:
            return Response(response_xml, mimetype='application/xml')
    
    # 处理未完成，继续重试策略
    if retry_count < 2:  # 前两次重试返回 500 状态码
        return Response("", status=500)
    else:  # 最后一次重试
        if enable_custom_message:
            # 客服消息模式
            logger.info("启用客服消息模式")
            retry_completion_event = message_status.get('retry_completion_event')
            if retry_completion_event:
                retry_completion_event.set()
            
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=temp_message
            )
            
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')
        else:
            # 交互等待模式
            logger.info("启用交互等待模式")
            UserWaitingManager.set_user_waiting(message.from_user, message_status, max_continue_count)
            
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=continue_waiting_message
            )
            
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')


def _handle_continue_waiting_retry(message, message_status, retry_count,
                                   continue_waiting_message, max_continue_count,
                                   crypto: WechatMessageCrypto, request, retry_wait_timeout: float):
    """处理继续等待消息的重试"""
    waiting_info = message_status.get('original_waiting_info')
    if not waiting_info:
        logger.warning("继续等待消息缺少原始等待信息")
        UserWaitingManager.clear_user_waiting(message.from_user)
        return Response("", status=500)
    
    # 获取原始 AI 任务的完成事件
    original_status = waiting_info['original_status']
    completion_event = original_status.get('completion_event')
    
    # 检查原始 AI 任务是否已完成
    if completion_event and original_status.get('is_completed', False):
        logger.info("继续等待期间 AI 任务已完成，返回结果")
        UserWaitingManager.clear_user_waiting(message.from_user)
        
        response_content = original_status.get('result', '') or "抱歉，处理结果为空"
        response_xml = MessageParser.build_text_reply(
            to_user=message.from_user,
            from_user=message.to_user,
            content=response_content
        )
        
        # 获取配置以确定是否需要加密
        config = auth_manager.get_config()
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        if config and config.get('encoding_aes_key'):
            encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
            return Response(encrypted_response, mimetype='application/xml')
        else:
            return Response(response_xml, mimetype='application/xml')
    
    # 等待原始 AI 任务完成
    is_completed = False
    if completion_event:
        is_completed = completion_event.wait(timeout=retry_wait_timeout)
    
    if is_completed and original_status.get('is_completed', False):
        # AI 任务在等待期间完成了
        logger.info("重试期间 AI 任务完成")
        UserWaitingManager.clear_user_waiting(message.from_user)
        
        response_content = original_status.get('result', '') or "抱歉，处理结果为空"
        response_xml = MessageParser.build_text_reply(
            to_user=message.from_user,
            from_user=message.to_user,
            content=response_content
        )
        
        config = auth_manager.get_config()
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        if config and config.get('encoding_aes_key'):
            encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
            return Response(encrypted_response, mimetype='application/xml')
        else:
            return Response(response_xml, mimetype='application/xml')
    
    # AI 任务仍未完成
    if retry_count < 2:  # 前两次重试返回 500 状态码，触发微信继续重试
        logger.debug(f"继续等待重试: 第{retry_count}次，返回 500 触发下次重试")
        return Response("", status=500)
    else:  # 最后一次重试
        # 增加 continue_count 并判断是否达到限制
        UserWaitingManager.handle_continue_request(message.from_user)
        updated_waiting_info = UserWaitingManager.get_waiting_info(message.from_user)
        
        if not updated_waiting_info:
            logger.warning("用户等待状态丢失")
            response_content = "处理时间较长，请稍后重新询问"
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=response_content
            )
            
            config = auth_manager.get_config()
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config and config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')
        
        # 检查是否达到最大继续次数
        if updated_waiting_info['continue_count'] >= updated_waiting_info['max_continue_count']:
            logger.info("达到最大继续次数，结束等待")
            UserWaitingManager.clear_user_waiting(message.from_user)
            
            response_content = "处理时间较长，请稍后重新询问"
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=response_content
            )
            
            config = auth_manager.get_config()
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config and config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')
        else:
            # 还可以继续等待
            remaining_count = updated_waiting_info['max_continue_count'] - updated_waiting_info['continue_count']
            if remaining_count > 0:
                response_content = f"{continue_waiting_message} (剩余{remaining_count}次机会)"
            else:
                response_content = f"{continue_waiting_message} (最后1次机会)"
            
            # 安全地更新用户等待状态
            with UserWaitingManager._waiting_lock:
                if message.from_user in UserWaitingManager._waiting_users:
                    current_waiting_info = UserWaitingManager._waiting_users[message.from_user]
                    current_waiting_info['start_time'] = time.time()
                    current_waiting_info['expire_time'] = time.time() + 30
            
            logger.info(f"继续等待，剩余{remaining_count}次, response_content: {response_content}")
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=response_content
            )
            
            config = auth_manager.get_config()
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config and config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')


def _async_process_message(handler, message, config, message_status, completion_event):
    """异步处理消息"""
    start_time = time.time()
    
    try:
        # 处理消息
        if hasattr(handler, 'handle_message'):
            result = handler.handle_message(message, auth_manager)
        else:
            result = handler.handle(message, None, {}) or "收到消息"
        
        message_status['result'] = result
        message_status['is_completed'] = True
        
        MessageStatusTracker.update_status(
            message,
            result=result,
            is_completed=True
        )
    except Exception as e:
        logger.error(f"异步处理消息失败: {str(e)}")
        
        error_msg = f"处理失败: {str(e)}"
        message_status['result'] = error_msg
        message_status['error'] = error_msg
        message_status['is_completed'] = True
        
        MessageStatusTracker.update_status(
            message,
            result=error_msg,
            error=str(e),
            is_completed=True
        )
    finally:
        completion_event.set()
        elapsed = time.time() - start_time
        logger.info(f"消息处理完成，耗时: {elapsed:.2f}秒")


def _wait_and_send_custom_message(message, message_status, config, completion_event):
    """等待处理完成并发送客服消息"""
    try:
        # 等待 AI 处理完成
        is_completed = completion_event.wait(timeout=300)
        
        app_id = config.get('app_id', '')
        app_secret = config.get('app_secret', '')
        wechat_api_proxy_url = _get_config_value('WECHAT_API_PROXY_URL', 'api.weixin.qq.com')
        
        if not app_id or not app_secret:
            logger.error("缺少 app_id 或 app_secret 配置")
            return
        
        sender = WechatCustomMessageSender(app_id, app_secret, wechat_api_proxy_url)
        sender.set_typing_status(message.from_user, False)
        
        if not is_completed:
            logger.warning("AI 处理超时(>5分钟)，强制结束")
            MessageStatusTracker.update_status(
                message.msg_id,
                result="处理超时，请稍后重试",
                is_completed=True,
                error="处理超时 (>5 分钟)"
            )
            return
        
        # 等待重试流程完成
        retry_completion_event = message_status.get('retry_completion_event')
        if retry_completion_event:
            retry_completed = retry_completion_event.wait(timeout=20)
            if not retry_completed:
                logger.warning("等待重试流程超时")
        
        # 检查是否需要跳过客服消息
        if message_status.get('skip_custom_message', False):
            return
        
        if not MessageStatusTracker.mark_result_returned(message):
            return
        
        # 获取处理结果并发送客服消息
        content = message_status.get('result', '') or "抱歉，无法获取处理结果"
        send_result = sender.send_text_message(
            open_id=message.from_user,
            content=content
        )
        
        if send_result.get('success'):
            logger.info("客服消息发送成功")
        else:
            error_msg = send_result.get('error', 'unknown error')
            logger.error(f"客服消息发送失败: {error_msg}")
    except Exception as e:
        logger.error(f"客服消息处理异常: {str(e)}")


def main():
    """启动 HTTP 服务器"""
    port = int(os.getenv('WECHAT_SERVER_PORT', 8000))
    host = os.getenv('WECHAT_SERVER_HOST', '0.0.0.0')
    
    logger.info(f"微信公众号消息服务器启动在 {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()

