#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FireMon 專案配置文件
"""

import os
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent

# 應用程式設定
APP_CONFIG = {
    "name": "FireMon",
    "version": "1.0.0",
    "description": "FireMon 監控系統",
    "author": "開發團隊",
}

# 日誌設定
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": PROJECT_ROOT / "logs" / "app.log",
}

# 資料庫設定
DATABASE_CONFIG = {
    "type": "sqlite",
    "path": PROJECT_ROOT / "data" / "firemon.db",
}

# 網路設定
NETWORK_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "debug": True,
}

# 環境變數設定
def get_env_var(key: str, default=None):
    """取得環境變數值"""
    return os.getenv(key, default)

# 開發/生產環境設定
ENVIRONMENT = get_env_var("FIREMON_ENV", "development")

if ENVIRONMENT == "production":
    NETWORK_CONFIG["debug"] = False
    LOGGING_CONFIG["level"] = "WARNING"
