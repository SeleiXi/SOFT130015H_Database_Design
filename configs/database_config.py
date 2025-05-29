#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Dict, Any

def get_database_config() -> Dict[str, Any]:
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root'),
        'database': os.getenv('DB_NAME', 'db_design_pj'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
        'autocommit': os.getenv('DB_AUTOCOMMIT', 'True').lower() == 'true',
        # 连接池配置
        'pool_name': os.getenv('DB_POOL_NAME', 'llm_eval_pool'),
        'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
        'pool_reset_session': os.getenv('DB_POOL_RESET_SESSION', 'True').lower() == 'true',
    }

def get_app_config() -> Dict[str, Any]:
    """
    获取应用配置
    """
    return {
        'debug': os.getenv('APP_DEBUG', 'False').lower() == 'true',
        'log_level': os.getenv('APP_LOG_LEVEL', 'INFO'),
        'streamlit_port': int(os.getenv('STREAMLIT_PORT', '8501')),
        'streamlit_host': os.getenv('STREAMLIT_HOST', 'localhost'),
    }

# 导出配置
DB_CONFIG = get_database_config()
APP_CONFIG = get_app_config()

# 验证配置的函数
def validate_config() -> bool:
    """验证配置是否有效"""
    required_fields = ['host', 'user', 'password', 'database']
    
    for field in required_fields:
        if not DB_CONFIG.get(field):
            print(f"❌ 配置错误: {field} 不能为空")
            return False
    
    if DB_CONFIG['port'] <= 0 or DB_CONFIG['port'] > 65535:
        print(f"❌ 配置错误: 端口号 {DB_CONFIG['port']} 无效")
        return False
    
    return True

def print_config_info():
    """打印配置信息（隐藏敏感信息）"""
    safe_config = DB_CONFIG.copy()
    safe_config['password'] = '*' * len(safe_config['password']) if safe_config['password'] else 'None'
    
    print("📋 数据库配置信息:")
    for key, value in safe_config.items():
        print(f"   {key}: {value}") 