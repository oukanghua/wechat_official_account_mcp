#!/usr/bin/env python3
"""
测试微信服务器连接的工具
用于验证微信公众号服务器配置是否正确
"""
import sys
import os
import requests
import hashlib
import time

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

load_dotenv()


def generate_signature(token: str, timestamp: str, nonce: str) -> str:
    """生成微信签名"""
    temp_list = [token, timestamp, nonce]
    temp_list.sort()
    temp_str = ''.join(temp_list)
    return hashlib.sha1(temp_str.encode('utf-8')).hexdigest()


def test_health_check(server_url: str):
    """测试健康检查接口"""
    print("=" * 60)
    print("测试健康检查接口")
    print("=" * 60)
    
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False


def test_verification(server_url: str, token: str):
    """测试微信服务器验证接口"""
    print("\n" + "=" * 60)
    print("测试微信服务器验证接口")
    print("=" * 60)
    
    # 生成测试参数
    timestamp = str(int(time.time()))
    nonce = "test123"
    echostr = "test_echostr_12345"
    
    # 生成签名
    signature = generate_signature(token, timestamp, nonce)
    
    print(f"Token: {token}")
    print(f"Timestamp: {timestamp}")
    print(f"Nonce: {nonce}")
    print(f"Echostr: {echostr}")
    print(f"Signature: {signature}")
    print()
    
    # 发送验证请求
    try:
        params = {
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce,
            'echostr': echostr
        }
        
        response = requests.get(f"{server_url}/wechat", params=params, timeout=5)
        print(f"请求 URL: {response.url}")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200 and response.text == echostr:
            print("✅ 微信服务器验证成功！")
            print("   可以在微信公众平台配置此服务器 URL")
            return True
        else:
            print("❌ 微信服务器验证失败")
            print(f"   期望返回: {echostr}")
            print(f"   实际返回: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 验证请求失败: {str(e)}")
        return False


def test_wrong_signature(server_url: str):
    """测试错误的签名（应该失败）"""
    print("\n" + "=" * 60)
    print("测试错误签名（应该返回 403）")
    print("=" * 60)
    
    try:
        params = {
            'signature': 'wrong_signature',
            'timestamp': str(int(time.time())),
            'nonce': 'test123',
            'echostr': 'test_echostr'
        }
        
        response = requests.get(f"{server_url}/wechat", params=params, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 403:
            print("✅ 正确拒绝了错误的签名")
            return True
        else:
            print("❌ 应该返回 403，但返回了其他状态码")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("微信公众号服务器测试工具")
    print("=" * 60)
    print()
    
    # 获取配置
    server_url = os.getenv('WECHAT_SERVER_URL', 'http://localhost:8000')
    token = os.getenv('WECHAT_TOKEN', '')
    
    if not token:
        print("❌ 错误: 未配置 WECHAT_TOKEN")
        print("   请在 .env 文件中设置 WECHAT_TOKEN")
        return
    
    print(f"服务器地址: {server_url}")
    print(f"Token: {token}")
    print()
    
    # 运行测试
    results = []
    
    # 1. 健康检查
    results.append(("健康检查", test_health_check(server_url)))
    
    # 2. 验证接口（正确签名）
    results.append(("服务器验证", test_verification(server_url, token)))
    
    # 3. 验证接口（错误签名）
    results.append(("错误签名测试", test_wrong_signature(server_url)))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print()
    if all_passed:
        print("🎉 所有测试通过！")
        print()
        print("下一步:")
        print(f"1. 确保服务器正在运行: {server_url}")
        print("2. 在微信公众平台配置服务器 URL:")
        print(f"   - URL: {server_url}/wechat")
        print(f"   - Token: {token}")
        print("3. 点击'提交'进行验证")
    else:
        print("⚠️  部分测试失败，请检查配置和服务器状态")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

