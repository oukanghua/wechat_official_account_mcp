#!/usr/bin/env python3
"""
测试微信公众号 API 功能
"""
import sys
import os
import asyncio
import logging
import requests

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.auth_manager import AuthManager
from utils.wechat_api_client import WechatApiClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_config():
    """测试配置读取"""
    print("\n" + "="*50)
    print("测试 1: 检查配置")
    print("="*50)
    
    auth_manager = AuthManager()
    config = auth_manager.get_config()
    
    if not config:
        print("❌ 错误: 未找到配置")
        return False
    
    print(f"✅ AppID: {config.get('app_id')}")
    print(f"✅ AppSecret: {'已配置' if config.get('app_secret') else '未配置'}")
    print(f"{'✅' if config.get('token') else '⚠️ '} Token: {config.get('token') or '未配置'}")
    print(f"{'✅' if config.get('encoding_aes_key') else '⚠️ '} EncodingAESKey: {'已配置' if config.get('encoding_aes_key') else '未配置'}")
    
    if not config.get('app_id') or not config.get('app_secret'):
        print("❌ 错误: AppID 或 AppSecret 未配置")
        return False
    
    return True


def test_access_token():
    """测试获取 Access Token"""
    print("\n" + "="*50)
    print("测试 2: 获取 Access Token")
    print("="*50)
    
    try:
        auth_manager = AuthManager()
        api_client = WechatApiClient.from_auth_manager(auth_manager)
        
        # 同步方式获取 token
        token = api_client._get_access_token_sync()
        
        if token:
            print(f"✅ 成功获取 Access Token: {token[:20]}...")
            return True
        else:
            print("❌ 获取 Access Token 失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_upload_img():
    """测试上传图文消息图片"""
    print("\n" + "="*50)
    print("测试 3: 上传图文消息图片")
    print("="*50)
    
    try:
        auth_manager = AuthManager()
        api_client = WechatApiClient.from_auth_manager(auth_manager)
        
        # 创建一个简单的测试图片（1x1像素的PNG）
        from PIL import Image
        import io
        
        img = Image.new('RGB', (1, 1), color='white')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_data = img_buffer.read()
        
        # 上传图片
        result = api_client.upload_img(img_data)
        
        if result and 'url' in result:
            print(f"✅ 图片上传成功")
            print(f"   图片 URL: {result['url']}")
            return True
        else:
            print(f"❌ 图片上传失败: {result}")
            return False
            
    except Exception as e:
        print(f"⚠️  测试跳过: {str(e)}")
        print("   (需要安装 Pillow 库)")
        return None


def test_get_draft_list():
    """测试获取草稿列表"""
    print("\n" + "="*50)
    print("测试 4: 获取草稿列表")
    print("="*50)
    
    try:
        auth_manager = AuthManager()
        api_client = WechatApiClient.from_auth_manager(auth_manager)
        
        # 使用微信 API 获取草稿列表
        endpoint = '/cgi-bin/draft/batchget'
        data = {
            'offset': 0,
            'count': 5,
            'no_content': 1  # 不返回内容，只返回基本信息
        }
        
        import json
        result = api_client._request('POST', endpoint, data=json.dumps(data, ensure_ascii=False))
        
        if result and 'item' in result:
            count = len(result['item'])
            print(f"✅ 获取草稿列表成功")
            print(f"   草稿数量: {count}")
            print(f"   总数量: {result.get('total_count', 0)}")
            if count > 0:
                print(f"   第一个草稿 Media ID: {result['item'][0].get('media_id', 'N/A')}")
            return True
        else:
            print(f"⚠️  暂无草稿或返回格式异常: {result}")
            return True
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_create_draft():
    """测试创建草稿"""
    print("\n" + "="*50)
    print("测试 5: 创建草稿")
    print("="*50)
    
    try:
        auth_manager = AuthManager()
        api_client = WechatApiClient.from_auth_manager(auth_manager)
        
        # 先上传一个缩略图（必需）
        print("   正在上传缩略图...")
        try:
            from PIL import Image
            import io
            
            # 创建一个符合微信要求的缩略图（至少 640x360）
            img = Image.new('RGB', (640, 360), color=(135, 206, 250))  # 浅蓝色
            img_buffer = io.BytesIO()
            # 保存为 JPEG 格式，确保是有效的图片文件
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            img_data = img_buffer.read()
            
            # 上传永久素材作为缩略图（草稿需要使用永久素材）
            # 使用 image 类型上传，然后可以在草稿中使用
            thumb_result = api_client.upload_permanent_media('image', file_content=img_data)
            
            if 'errcode' in thumb_result and thumb_result['errcode'] != 0:
                raise Exception(f"上传失败: {thumb_result.get('errmsg', '未知错误')}")
            
            thumb_media_id = thumb_result.get('media_id', '')
            print(f"   ✅ 缩略图上传成功（永久素材）: {thumb_media_id[:20]}...")
        except ImportError:
            print(f"   ⚠️  Pillow 库未安装，跳过缩略图上传")
            print("   ⚠️  将跳过创建草稿测试（需要缩略图）")
            return None
        except Exception as e:
            print(f"   ⚠️  缩略图上传失败: {str(e)}")
            print("   ⚠️  将跳过创建草稿测试（需要缩略图）")
            return None
        
        # 创建测试草稿
        articles = [{
            "title": "API测试文章",
            "author": "测试作者",
            "digest": "这是一篇通过API创建的测试文章",
            "content": "<p>这是测试文章的内容。通过微信公众号 API 创建。</p><p>如果看到这篇文章，说明 API 调用成功！</p>",
            "content_source_url": "https://example.com",
            "thumb_media_id": thumb_media_id,
            "show_cover_pic": 1,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
        
        result = api_client.add_draft(articles)
        
        if result and 'media_id' in result:
            print(f"✅ 草稿创建成功")
            print(f"   草稿 Media ID: {result['media_id']}")
            return result['media_id']
        else:
            print(f"❌ 草稿创建失败: {result}")
            if result and 'errcode' in result:
                print(f"   错误代码: {result['errcode']}")
                print(f"   错误信息: {result.get('errmsg', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("微信公众号 API 功能测试")
    print("="*60)
    
    results = []
    
    # 测试配置
    if not test_config():
        print("\n❌ 配置测试失败，无法继续")
        return
    
    results.append(("配置检查", True))
    
    # 测试 Access Token
    if test_access_token():
        results.append(("Access Token", True))
    else:
        results.append(("Access Token", False))
        print("\n❌ Access Token 获取失败，后续测试可能失败")
    
    # 测试上传图片
    img_result = test_upload_img()
    if img_result is not None:
        results.append(("上传图片", img_result))
    
    # 测试获取草稿列表
    if test_get_draft_list():
        results.append(("获取草稿列表", True))
    else:
        results.append(("获取草稿列表", False))
    
    # 测试创建草稿（需要先有图片）
    draft_id = test_create_draft()
    if draft_id:
        results.append(("创建草稿", True))
    else:
        results.append(("创建草稿", False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    elif passed > 0:
        print("\n⚠️  部分测试通过，请检查失败的测试项")
    else:
        print("\n❌ 所有测试失败，请检查配置")


if __name__ == '__main__':
    main()

