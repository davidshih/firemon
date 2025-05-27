import os
import json
import logging
import time
from typing import Dict, Optional, Tuple, Any
from functools import wraps
import pandas as pd
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FireMonAPIError(Exception):
    """FireMon API 相關的自訂例外類別"""
    pass


class FireMonAuthError(FireMonAPIError):
    """認證相關的例外類別"""
    pass


class FireMonRequestError(FireMonAPIError):
    """請求相關的例外類別"""
    pass


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重試裝飾器，用於處理暫時性的 API 失敗"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"嘗試 {attempt + 1}/{max_attempts} 失敗: {e}. 等待 {delay} 秒後重試...")
                        time.sleep(delay)
                    else:
                        logger.error(f"所有 {max_attempts} 次嘗試都失敗了")
            raise last_exception
        return wrapper
    return decorator


class FireMonClient:
    """FireMon API 客戶端類別"""
    
    def __init__(self, base_url: str, user_id: str, password: str, domain_id: str):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.password = password
        self.domain_id = domain_id
        self._token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "Content-Type": "application/json; charset=utf-8"
        })
    
    @property
    def token(self) -> str:
        """獲取或刷新認證 Token"""
        if not self._token:
            self._authenticate()
        return self._token
    
    @retry_on_failure(max_attempts=3, delay=2.0)
    def _authenticate(self) -> None:
        """執行 FireMon API 認證"""
        url = f"{self.base_url}/securitymanager/api/authentication/login"
        payload = {"username": self.user_id, "password": self.password}
        
        logger.info("正在進行 FireMon API 認證...")
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            auth_data = response.json()
            token = auth_data.get("token")
            
            if not token:
                raise FireMonAuthError(f"認證回應中未包含 token: {auth_data}")
            
            self._token = token
            self.session.headers.update({"X-FM-Auth-Token": token})
            logger.info("FireMon API 認證成功！")
            
        except requests.exceptions.HTTPError as e:
            raise FireMonAuthError(f"認證失敗 (HTTP {e.response.status_code}): {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FireMonAuthError(f"認證請求失敗: {e}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """通用的 API 請求方法"""
        if self._token:
            self.session.headers.update({"X-FM-Auth-Token": self.token})
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning("Token 可能已過期，嘗試重新認證...")
                self._token = None
                self._authenticate()
                return self._make_request(method, url, **kwargs)
            raise FireMonRequestError(f"API 請求失敗 (HTTP {e.response.status_code}): {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FireMonRequestError(f"API 請求失敗: {e}")
    
    @retry_on_failure(max_attempts=3, delay=1.0)
    def update_ticket_variables(self, ticket_id: str, workflow_id: str, 
                               packet_task_id: str, variables: Dict[str, Any]) -> bool:
        """更新票證變數"""
        url = (f"{self.base_url}/policysoptimizer/api/v2/workflow/"
               f"{workflow_id}@{self.domain_id}/packet/{packet_task_id}/task/{ticket_id}")
        
        payload = {"variables": variables}
        logger.info(f"更新 Ticket ID: {ticket_id} 的變數...")
        
        try:
            self._make_request("PUT", url, json=payload)
            logger.info(f"Ticket ID: {ticket_id} 變數更新成功")
            return True
        except FireMonRequestError as e:
            logger.error(f"更新 Ticket ID: {ticket_id} 失敗: {e}")
            return False
    
    @retry_on_failure(max_attempts=3, delay=1.0)
    def assign_ticket(self, ticket_id: str, workflow_id: str, 
                     packet_task_id: str, assigned_user_id: str) -> bool:
        """指派票證給使用者"""
        url = (f"{self.base_url}/policysoptimizer/api/v2/workflow/"
               f"{workflow_id}@{self.domain_id}/packet/{packet_task_id}/task/{ticket_id}/assign")
        
        payload = {"assignedTo": assigned_user_id}
        logger.info(f"指派 Ticket ID: {ticket_id} 給使用者: {assigned_user_id}...")
        
        try:
            self._make_request("PUT", url, json=payload)
            logger.info(f"Ticket ID: {ticket_id} 指派成功")
            return True
        except FireMonRequestError as e:
            logger.error(f"指派 Ticket ID: {ticket_id} 失敗: {e}")
            return False
    
    @retry_on_failure(max_attempts=3, delay=1.0)
    def update_ticket_status(self, ticket_id: str, workflow_id: str, 
                            packet_task_id: str, new_status: str) -> bool:
        """更新票證狀態"""
        return self.update_ticket_variables(
            ticket_id, workflow_id, packet_task_id, 
            {"status": new_status}
        )


class TicketProcessor:
    """票證批次處理器"""
    
    def __init__(self, client: FireMonClient):
        self.client = client
        self.processed_count = 0
        self.failed_count = 0
    
    def process_csv(self, csv_path: str) -> None:
        """處理 CSV 檔案中的票證"""
        logger.info(f"讀取 CSV 檔案: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到 CSV 檔案: {csv_path}")
        except Exception as e:
            raise Exception(f"讀取 CSV 檔案失敗: {e}")
        
        for index, row in df.iterrows():
            self._process_single_ticket(row, index + 2)
        
        logger.info(
            f"批次處理完成！成功: {self.processed_count} 筆, "
            f"失敗: {self.failed_count} 筆"
        )
    
    def _process_single_ticket(self, row: pd.Series, row_number: int) -> None:
        """處理單一票證"""
        ticket_info = self._validate_ticket_info(row, row_number)
        if not ticket_info:
            return
        
        action_type = ticket_info['action_type']
        success = False
        
        action_handlers = {
            'update_vars': self._handle_update_vars,
            'assign_ticket': self._handle_assign_ticket,
            'complete_ticket': self._handle_complete_ticket,
        }
        
        handler = action_handlers.get(action_type)
        if handler:
            success = handler(ticket_info, row)
        else:
            logger.warning(
                f"不支援的 action_type: '{action_type}' "
                f"(Ticket ID: {ticket_info['ticket_id']})"
            )
            self.failed_count += 1
            return
        
        if success:
            self.processed_count += 1
        else:
            self.failed_count += 1
    
    def _validate_ticket_info(self, row: pd.Series, row_number: int) -> Optional[Dict[str, str]]:
        """驗證票證資訊的完整性"""
        required_fields = ['ticket_id', 'action_type', 'workflow_id', 'packet_task_id']
        ticket_info = {}
        
        for field in required_fields:
            value = row.get(field)
            if pd.isna(value):
                logger.warning(f"第 {row_number} 行缺少必要欄位: {field}")
                self.failed_count += 1
                return None
            ticket_info[field] = str(value)
        
        return ticket_info
    
    def _handle_update_vars(self, ticket_info: Dict[str, str], row: pd.Series) -> bool:
        """處理更新變數的動作"""
        variables_to_update = {}
        excluded_fields = ['ticket_id', 'action_type', 'workflow_id', 'packet_task_id']
        
        for col_name, value in row.items():
            if col_name not in excluded_fields and pd.notna(value):
                variables_to_update[col_name] = value
        
        if not variables_to_update:
            logger.warning(f"Ticket ID: {ticket_info['ticket_id']} 沒有要更新的變數")
            return False
        
        return self.client.update_ticket_variables(
            ticket_info['ticket_id'],
            ticket_info['workflow_id'],
            ticket_info['packet_task_id'],
            variables_to_update
        )
    
    def _handle_assign_ticket(self, ticket_info: Dict[str, str], row: pd.Series) -> bool:
        """處理指派票證的動作"""
        assigned_to = row.get('assigned_to')
        if pd.isna(assigned_to):
            logger.warning(
                f"Ticket ID: {ticket_info['ticket_id']} 的 'assign_ticket' "
                f"動作缺少 'assigned_to' 欄位"
            )
            return False
        
        return self.client.assign_ticket(
            ticket_info['ticket_id'],
            ticket_info['workflow_id'],
            ticket_info['packet_task_id'],
            str(assigned_to)
        )
    
    def _handle_complete_ticket(self, ticket_info: Dict[str, str], row: pd.Series) -> bool:
        """處理完成票證的動作"""
        new_status = row.get('new_status')
        if pd.isna(new_status):
            logger.warning(
                f"Ticket ID: {ticket_info['ticket_id']} 的 'complete_ticket' "
                f"動作缺少 'new_status' 欄位"
            )
            return False
        
        return self.client.update_ticket_status(
            ticket_info['ticket_id'],
            ticket_info['workflow_id'],
            ticket_info['packet_task_id'],
            str(new_status)
        )


def load_config() -> Tuple[str, str, str, str]:
    """載入環境變數設定"""
    load_dotenv()
    
    config = {
        'base_url': os.getenv("FIREMON_BASE_URL"),
        'user_id': os.getenv("FIREMON_USER_ID"),
        'password': os.getenv("FIREMON_PASSWORD"),
        'domain_id': os.getenv("FIREMON_DOMAIN_ID")
    }
    
    missing_vars = [k for k, v in config.items() if not v]
    if missing_vars:
        raise ValueError(
            f"缺少必要的環境變數: {', '.join(missing_vars)}. "
            f"請檢查 .env 檔案"
        )
    
    return (config['base_url'], config['user_id'], 
            config['password'], config['domain_id'])


def main():
    """主程式進入點"""
    try:
        base_url, user_id, password, domain_id = load_config()
        
        client = FireMonClient(base_url, user_id, password, domain_id)
        
        processor = TicketProcessor(client)
        processor.process_csv('bulk_updates.csv')
        
    except FileNotFoundError as e:
        logger.error(f"檔案錯誤: {e}")
        return 1
    except FireMonAuthError as e:
        logger.critical(f"認證錯誤: {e}")
        return 2
    except FireMonAPIError as e:
        logger.error(f"API 錯誤: {e}")
        return 3
    except Exception as e:
        logger.critical(f"未預期的錯誤: {e}")
        return 4
    
    return 0


if __name__ == "__main__":
    exit(main())