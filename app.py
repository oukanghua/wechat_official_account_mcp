import time
from flask import Flask, request, jsonify
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 导入配置
from .config import Config
config = Config()

# 导入路由
from .api.routes import api_bp
app.register_blueprint(api_bp)

@app.route('/')
def index():
    """根路径"""
    return jsonify({
        'message': 'WeChat Complete Plugin API',
        'version': '1.0.0',
        'status': 'running'
    })

@app.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time())
    })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f'Internal Server Error: {str(error)}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred'
    }), 500

def main():
    """主函数"""
    port = int(os.getenv('API_PORT', 5000))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    logger.info(f'Starting WeChat Plugin API on {host}:{port}')
    
    try:
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f'Failed to start server: {str(e)}')
        raise

if __name__ == '__main__':
    main()