#!/usr/bin/env python3
"""
微信公众号消息服务器入口文件
用于启动消息接收服务器
"""
import sys
import os

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 导入并运行服务器
if __name__ == "__main__":
    from server.wechat_server import main
    main()

