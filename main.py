#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FireMon 專案主程式 - CLI 介面
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from config import FIREMON_CONFIG, LOGGING_CONFIG
from utils import setup_logging
from firemon_automation import FireMonAutomation

def create_parser():
    """建立命令列參數解析器"""
    parser = argparse.ArgumentParser(
        description='FireMon Policy Optimizer 自動化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s --url https://firemon.example.com --username admin --password secret
  %(prog)s --headless  # 無頭模式執行
  %(prog)s --config    # 顯示當前配置
        """
    )
    
    # 基本參數
    parser.add_argument(
        '--url', 
        default=FIREMON_CONFIG['url'],
        help='FireMon 實例 URL'
    )
    parser.add_argument(
        '--username', 
        default=FIREMON_CONFIG['username'],
        help='登入用戶名'
    )
    parser.add_argument(
        '--password', 
        default=FIREMON_CONFIG['password'],
        help='登入密碼'
    )
    
    # 執行選項
    parser.add_argument(
        '--browser', 
        choices=['chrome', 'edge'], 
        default=FIREMON_CONFIG['browser'],
        help='使用的瀏覽器 (chrome 或 edge)'
    )
    parser.add_argument(
        '--headless', 
        action='store_true',
        default=FIREMON_CONFIG['headless'],
        help='無頭模式執行（不顯示瀏覽器）'
    )
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=FIREMON_CONFIG['timeout'],
        help='元素等待超時時間（秒）'
    )
    parser.add_argument(
        '--screenshot-dir', 
        default=str(FIREMON_CONFIG['screenshot_dir']),
        help='截圖保存目錄'
    )
    
    # 工具選項
    parser.add_argument(
        '--config', 
        action='store_true',
        help='顯示當前配置'
    )
    parser.add_argument(
        '--version', 
        action='version',
        version='FireMon Automation Tool 1.0.0'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細輸出'
    )
    
    return parser

def show_config():
    """顯示當前配置"""
    print("=== FireMon 配置資訊 ===")
    print(f"URL: {FIREMON_CONFIG['url']}")
    print(f"使用者名稱: {FIREMON_CONFIG['username'] or '未設定'}")
    print(f"密碼: {'已設定' if FIREMON_CONFIG['password'] else '未設定'}")
    print(f"瀏覽器類型: {FIREMON_CONFIG['browser']}")
    print(f"截圖目錄: {FIREMON_CONFIG['screenshot_dir']}")
    print(f"超時時間: {FIREMON_CONFIG['timeout']} 秒")
    print(f"無頭模式: {FIREMON_CONFIG['headless']}")
    print(f"重試次數: {FIREMON_CONFIG['retry_attempts']}")
    print()
    
    # 檢查 .env 檔案
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env 檔案存在")
    else:
        print("⚠ .env 檔案不存在，請複製 .env.example 並修改")
    
    # 檢查必要參數
    missing_params = []
    if not FIREMON_CONFIG['url'] or FIREMON_CONFIG['url'] == 'https://your-firemon-instance.com':
        missing_params.append('URL')
    if not FIREMON_CONFIG['username']:
        missing_params.append('使用者名稱')
    if not FIREMON_CONFIG['password']:
        missing_params.append('密碼')
    
    if missing_params:
        print(f"⚠ 缺少必要參數: {', '.join(missing_params)}")
        print("請設定環境變數或使用命令列參數")
    else:
        print("✓ 所有必要參數已設定")

def validate_args(args):
    """驗證命令列參數"""
    errors = []
    
    if not args.url or args.url == 'https://your-firemon-instance.com':
        errors.append("請提供有效的 FireMon URL")
    
    if not args.username:
        errors.append("請提供使用者名稱")
        
    if not args.password:
        errors.append("請提供密碼")
    
    if args.timeout <= 0:
        errors.append("超時時間必須大於 0")
    
    return errors

def main():
    """主函數"""
    # 載入環境變數
    load_dotenv()
    
    # 建立參數解析器
    parser = create_parser()
    args = parser.parse_args()
    
    # 設定日誌
    logger = setup_logging(LOGGING_CONFIG)
    
    # 顯示配置
    if args.config:
        show_config()
        return 0
    
    # 驗證參數
    errors = validate_args(args)
    if errors:
        print("參數錯誤:")
        for error in errors:
            print(f"  • {error}")
        print("\n使用 --help 查看使用說明")
        print("使用 --config 查看當前配置")
        return 1
    
    # 建立截圖目錄
    screenshot_dir = Path(args.screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # 執行自動化
    try:
        if args.verbose:
            print(f"開始執行 FireMon 自動化...")
            print(f"目標 URL: {args.url}")
            print(f"使用者: {args.username}")
            print(f"瀏覽器: {args.browser}")
            print(f"無頭模式: {args.headless}")
            print(f"截圖目錄: {args.screenshot_dir}")
            print("-" * 50)
        
        automation = FireMonAutomation(
            url=args.url,
            username=args.username,
            password=args.password,
            headless=args.headless,
            browser=args.browser
        )
        
        success = automation.run()
        
        if success:
            print("\n✓ 自動化執行成功！")
            return 0
        else:
            print("\n✗ 自動化執行失敗！")
            return 1
            
    except KeyboardInterrupt:
        print("\n用戶中斷執行")
        return 1
    except Exception as e:
        logger.error(f"執行失敗: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())