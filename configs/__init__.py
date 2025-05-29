#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块
管理数据库和应用程序配置
"""

from .database_config import (
    DB_CONFIG,
    APP_CONFIG,
    get_database_config,
    get_app_config,
    validate_config,
    print_config_info
)

__all__ = [
    'DB_CONFIG',
    'APP_CONFIG', 
    'get_database_config',
    'get_app_config',
    'validate_config',
    'print_config_info'
] 