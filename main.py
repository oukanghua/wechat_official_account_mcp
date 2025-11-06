from dify_plugin import Plugin, DifyPluginEnv
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 设置特定模块的日志级别
logging.getLogger('dify_plugin').setLevel(logging.WARNING)
logging.getLogger('dify_plugin.core.server.tcp.request_reader').setLevel(logging.WARNING)

# 创建插件实例
# 设置较长的超时时间以支持复杂的微信API操作
plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))

# 加载环境变量
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# 确保必要的目录存在
required_dirs = ['tools', 'handlers', 'api', 'utils', 'config']
for dir_name in required_dirs:
    Path(dir_name).mkdir(exist_ok=True)

if __name__ == '__main__':
    logging.info("微信公众号完整插件启动中...")
    plugin.run()