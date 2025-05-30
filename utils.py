#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FireMon 專案工具函數
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from selenium.webdriver.common.by import By

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """設置日誌系統"""
    logger = logging.getLogger("firemon")
    logger.setLevel(getattr(logging, config["level"]))
    
    # 創建日誌目錄
    log_file = Path(config["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 文件處理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, config["level"]))
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(config["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def load_json_file(file_path: str) -> Optional[Dict]:
    """載入 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件不存在: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤: {e}")
        return None

def save_json_file(data: Dict, file_path: str) -> bool:
    """儲存資料到 JSON 文件"""
    try:
        # 創建目錄
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"儲存文件失敗: {e}")
        return False

def get_current_timestamp() -> str:
    """取得當前時間戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f}{size_names[i]}"

def validate_config(config: Dict, required_keys: List[str]) -> bool:
    """驗證配置文件"""
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        print(f"配置文件缺少必要的鍵: {missing_keys}")
        return False
    return True

class Timer:
    """計時器工具類"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """開始計時"""
        self.start_time = datetime.now()
        print(f"計時開始: {self.start_time.strftime('%H:%M:%S')}")
    
    def stop(self):
        """停止計時"""
        if self.start_time is None:
            print("請先開始計時")
            return None
        
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        print(f"計時結束: {self.end_time.strftime('%H:%M:%S')}")
        print(f"總耗時: {duration.total_seconds():.2f} 秒")
        return duration.total_seconds()

class WebDriverHelper:
    """WebDriver 輔助工具類"""
    
    @staticmethod
    def wait_for_element(driver, by, value, timeout=10):
        """等待元素出現"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    @staticmethod
    def safe_click(driver, element):
        """安全點擊元素"""
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            print(f"點擊失敗: {e}")
            return False
    
    @staticmethod
    def take_screenshot(driver, filename):
        """截圖"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.png"
            driver.save_screenshot(full_filename)
            return full_filename
        except Exception as e:
            print(f"截圖失敗: {e}")
            return None

class FireMonHelper:
    """FireMon 專用輔助工具"""
    
    @staticmethod
    def extract_rule_info(element):
        """從元素中提取規則資訊"""
        rule_info = {}
        
        try:
            # 嘗試不同的選擇器來提取規則名稱
            name_selectors = [".rule-name", ".name", "[class*='name']", "[data-rule-name]"]
            for selector in name_selectors:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, selector)
                    rule_info['name'] = name_element.text.strip()
                    break
                except:
                    continue
            
            # 嘗試提取其他屬性
            rule_info['id'] = element.get_attribute('id') or ''
            rule_info['class'] = element.get_attribute('class') or ''
            
        except Exception as e:
            print(f"提取規則資訊失敗: {e}")
            
        return rule_info
    
    @staticmethod
    def find_policy_optimizer_link(driver):
        """尋找 Policy Optimizer 連結"""
        selectors = [
            "//a[contains(text(), 'Policy Optimizer')]",
            "//a[contains(text(), 'policy optimizer')]",
            "//a[contains(text(), 'PO')]",
            "[href*='policy-optimizer']",
            "[href*='po']"
        ]
        
        from selenium.webdriver.common.by import By
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = driver.find_element(By.XPATH, selector)
                else:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except:
                continue
        
        return None
    
    @staticmethod
    def find_tickets(driver):
        """尋找 PO tickets"""
        ticket_selectors = [".po-ticket", ".ticket", ".policy-ticket", "[class*='ticket']"]
        
        from selenium.webdriver.common.by import By
        
        for selector in ticket_selectors:
            try:
                tickets = driver.find_elements(By.CSS_SELECTOR, selector)
                if tickets:
                    return tickets
            except:
                continue
        
        return []
