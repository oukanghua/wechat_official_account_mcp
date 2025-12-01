#!/usr/bin/env python3
"""
微信公众号 MCP 服务器入口文件 (FastMCP 2.0 版本)
支持多种传输模式：stdio、http、sse
"""
import logging
import os
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 添加项目根目录到 Python 路径
        script_dir = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        # 加载环境变量
        from dotenv import load_dotenv
        env_file = script_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"已加载环境变量文件: {env_file}")
        else:
            logger.warning(f"未找到环境变量文件: {env_file}")
        
        # 确保数据目录存在
        data_dir = script_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # 设置日志目录
        logs_dir = script_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # 配置日志到文件
        log_file = logs_dir / 'mcp_server.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)
        
        logger.info("微信公众号 MCP 服务器启动中...")
        
        # 直接导入并运行 MCP 服务器
        logger.info("启动 MCP 服务器...")
        import mcp_server
        mcp_server.main()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"MCP 服务器启动异常: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

