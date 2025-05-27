import os
import json
import logging
import requests
import urllib3
import pandas as pd
from dotenv import load_dotenv

# 設定日誌 (Log)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 資安警告：請在生產環境中移除此行並確保 SSL 憑證有效 ---
# 這行會關閉 urllib3 發出的不安全請求警告，因為 requests 在 verify=False 時會用到 urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# -----------------------------------------------------------

# 全域變數，用於快取 API Token
# TOKEN 應該在成功認證後被設定
API_TOKEN = None

def load_config():
    """
    載入環境變數中的 FireMon API 設定。
    這些設定應該放在 .env 檔案中，例如：
    FIREMON_BASE_URL="https://your-firemon-instance.com"
    FIREMON_USER_ID="your_username"
    FIREMON_PASSWORD="your_password"
    FIREMON_DOMAIN_ID="your_domain_id" # 假設有個DOMAIN_ID
    """
    load_dotenv()
    base_url = os.getenv("FIREMON_BASE_URL")
    user_id = os.getenv("FIREMON_USER_ID")
    password = os.getenv("FIREMON_PASSWORD")
    domain_id = os.getenv("FIREMON_DOMAIN_ID")

    if not all([base_url, user_id, password, domain_id]):
        logger.error("錯誤：FireMon API 設定（BASE_URL, USER_ID, PASSWORD, DOMAIN_ID）未在 .env 檔案中完整設定。")
        raise ValueError("缺少必要的環境變數。請檢查 .env 檔案。")
    
    return base_url, user_id, password, domain_id

def get_auth_token(base_url, user_id, password):
    """
    獲取 FireMon API 的認證 Token。
    首次呼叫會進行認證，之後會使用快取的 Token (如果有的話)。
    """
    global API_TOKEN # 宣告使用全域變數

    if API_TOKEN:
        logger.info("使用已快取的 API Token。")
        return API_TOKEN

    url = f"{base_url}/securitymanager/api/authentication/login"
    auth_headers = {"Content-Type": "application/json; charset=utf-8"}
    auth_payload = json.dumps({"username": user_id, "password": password}) # 使用 json.dumps 將字典轉為 JSON 字串

    logger.info("嘗試獲取 FireMon API 認證 Token...")
    try:
        response = requests.post(url, headers=auth_headers, data=auth_payload, verify=False) # 再次強調 verify=False
        response.raise_for_status()  # 如果狀態碼是 4xx/5xx，拋出 HTTPError
        
        auth_token_data = response.json() # 直接使用 .json() 解析回應
        token = auth_token_data.get("token")

        if token:
            API_TOKEN = token # 快取 Token
            logger.info("FireMon API 認證成功！")
            return token
        else:
            logger.error(f"認證失敗：無法從回應中獲取 Token。回應：{response.text}")
            return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"認證失敗：HTTP 錯誤：{e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"認證失敗：請求錯誤：{e}")
    except Exception as e:
        logger.error(f"認證失敗：未知錯誤：{e}")
    return None

def update_ticket_variables(base_url, domain_id, ticket_id, workflow_id, packet_task_id, variables_to_update, token):
    """
    通用函數：更新 FireMon 票證的變數。
    """
    url = f"{base_url}/policysoptimizer/api/v2/workflow/{workflow_id}@{domain_id}/packet/{packet_task_id}/task/{ticket_id}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-FM-Auth-Token": token
    }
    
    # 這裡假設 variables_to_update 是一個字典，直接包含要更新的 key-value 對
    # 並且 ticket_list 中的每個 data 項目已經包含了 ticket_id, workflow_id, packet_task_id
    # FireMon API 的 payload 可能需要包含所有 variables，而不僅僅是更新的部分
    # 因此，理想情況下，應該先 GET 取得現有的 variables，然後合併或修改
    # 為簡化範例，這裡假設直接傳送一個包含修改後變數的 payload
    
    # 根據 Part 2 的邏輯，payload 應該是 {"variables": {...}}
    # 所以我們需要把 variables_to_update 包裝進去
    payload = {"variables": variables_to_update}

    logger.info(f"正在更新 Ticket ID: {ticket_id} 的變數...")
    try:
        response = requests.put(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        logger.info(f"Ticket ID: {ticket_id} 變數更新成功。狀態碼: {response.status_code}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"更新 Ticket ID: {ticket_id} 失敗：HTTP 錯誤：{e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"更新 Ticket ID: {ticket_id} 失敗：請求錯誤：{e}")
    return False

def assign_ticket(base_url, domain_id, ticket_id, workflow_id, packet_task_id, assigned_user_id, token):
    """
    處理指派票證的專用 API 呼叫。
    """
    # 根據 Part 1 的 assign_ticket URL
    url = f"{base_url}/policysoptimizer/api/v2/workflow/{workflow_id}@{domain_id}/packet/{packet_task_id}/task/{ticket_id}/assign"
    headers = {
        "Content-Type": "application/json", # 這個可能要看 API 文件，是 text/plain 還是 json
        "X-FM-Auth-Token": token
    }
    # 指派的 payload 結構可能根據 FireMon API 而異，這裡假設需要 assignedTo 這個 key
    # 實際可能需要更複雜的結構，例如包含 User ID 或其他資訊
    payload = json.dumps({"assignedTo": assigned_user_id}) 

    logger.info(f"正在指派 Ticket ID: {ticket_id} 給使用者: {assigned_user_id}...")
    try:
        response = requests.put(url, headers=headers, data=payload, verify=False) # data=payload 因為是 json.dumps 過的
        response.raise_for_status()
        logger.info(f"Ticket ID: {ticket_id} 指派成功。狀態碼: {response.status_code}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"指派 Ticket ID: {ticket_id} 失敗：HTTP 錯誤：{e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"指派 Ticket ID: {ticket_id} 失敗：請求錯誤：{e}")
    return False

def complete_ticket(base_url, domain_id, ticket_id, workflow_id, packet_task_id, new_status, token):
    """
    處理完成票證 (或更新票證狀態) 的專用 API 呼叫。
    這裡假設更新狀態也是透過修改 variables 實現，但為了通用性，可以有專屬函數
    """
    # 假設完成票證也透過 update_ticket_variables 實現，只是變數為 new_status
    # 或者 FireMon 有專門的 /complete 或 /status API
    # 這裡以修改 ticket 的 status 變數為例，實際可能需要查詢 API 文件
    
    # 為了簡化，我們假設 FireMon API 允許你直接設定 ticket_status
    # 如果是通過 variables 更新，應該是 update_ticket_variables 的範疇
    # 這裡創建一個假設的專用完成 API
    url = f"{base_url}/policysoptimizer/api/v2/workflow/{workflow_id}@{domain_id}/packet/{packet_task_id}/task/{ticket_id}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-FM-Auth-Token": token
    }
    # 假設 API 接收 {"status": "NewStatus"} 或 {"variables": {"status": "NewStatus"}}
    # 這裡我們假設需要傳送所有變數，包含新的 status
    
    # 你需要先獲取當前票證的所有變數，然後修改 status
    # 為了避免在每次呼叫中都 GET，這裡直接構建一個包含 status 的 payload
    # 這可能需要更精確的 API 文件說明，或者先 GET 再 PUT
    payload = {
        "variables": {
            "status": new_status # 假設變數名稱是 "status"
            # 如果還有其他變數需要保留，你需要先 GET 獲取它們
        }
    }
    
    logger.info(f"正在將 Ticket ID: {ticket_id} 狀態更新為: {new_status}...")
    try:
        response = requests.put(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        logger.info(f"Ticket ID: {ticket_id} 狀態更新成功為 {new_status}。狀態碼: {response.status_code}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"更新 Ticket ID: {ticket_id} 狀態失敗：HTTP 錯誤：{e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"更新 Ticket ID: {ticket_id} 狀態失敗：請求錯誤：{e}")
    return False

def bulk_process_tickets(csv_path, base_url, domain_id, token):
    """
    處理批次更新票證的核心函數，根據 CSV 中的 'action_type' 執行不同操作。
    """
    logger.info(f"正在讀取 CSV 檔案：{csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logger.error(f"錯誤：找不到 CSV 檔案：{csv_path}")
        return
    except Exception as e:
        logger.error(f"讀取 CSV 檔案時發生錯誤：{e}")
        return

    # 過濾掉沒有 ticket_id 的行，或者根據其他條件篩選
    # 沿用 Part 2 的篩選邏輯，如果需要可以修改
    # filtered_rows = df[(df['task'] == "Review") & (df['rule_disabled'] == True)]
    # 這裡我們假設 CSV 已經包含了所有要處理的票證，不再進行額外篩選
    
    processed_count = 0
    failed_count = 0

    for index, row in df.iterrows():
        ticket_id = row.get('ticket_id')
        action_type = row.get('action_type')
        workflow_id = row.get('workflow_id') # 假設 CSV 中有 workflow_id
        packet_task_id = row.get('packet_task_id') # 假設 CSV 中有 packet_task_id

        if not all([ticket_id, action_type, workflow_id, packet_task_id]):
            logger.warning(f"跳過第 {index+2} 行：缺少必要的 'ticket_id', 'action_type', 'workflow_id' 或 'packet_task_id'。")
            failed_count += 1
            continue
        
        # 轉換 ticket_id, workflow_id, packet_task_id 為字串，以防萬一
        ticket_id = str(int(ticket_id)) # 確保是整數再轉字串
        workflow_id = str(workflow_id)
        packet_task_id = str(packet_task_id)


        logger.info(f"處理 Ticket ID: {ticket_id}, 動作類型: {action_type}...")

        success = False
        if action_type == 'update_vars': # 更新通用變數
            variables_to_update = {}
            # 遍歷 CSV 行中除了核心 ID 和 action_type 以外的欄位，作為要更新的變數
            for col_name, value in row.items():
                if col_name not in ['ticket_id', 'action_type', 'workflow_id', 'packet_task_id'] and pd.notna(value):
                    variables_to_update[col_name] = value
            
            # 這裡需要一個方法先 GET 該 ticket_id 的所有變數，然後再更新
            # 因為 FireMon API 的 PUT 可能需要傳送所有變數，而不是只傳送要更新的
            # 為簡化，如果你的 API 允許 partial update 或你知道所有變數，可以跳過 GET
            # 否則，你應該像這樣獲取現有變數：
            # current_ticket_data = get_ticket_details(base_url, domain_id, ticket_id, token)
            # if current_ticket_data and 'variables' in current_ticket_data:
            #     existing_vars = current_ticket_data['variables']
            #     existing_vars.update(variables_to_update)
            #     success = update_ticket_variables(base_url, domain_id, ticket_id, workflow_id, packet_task_id, existing_vars, token)
            # else:
            #     logger.error(f"無法獲取 Ticket ID: {ticket_id} 的現有變數。")
            #     failed_count += 1
            #     continue
            
            # 簡化版：直接傳送 CSV 中定義的變數，假設 API 會處理
            success = update_ticket_variables(base_url, domain_id, ticket_id, workflow_id, packet_task_id, variables_to_update, token)

        elif action_type == 'assign_ticket': # 指派票證
            assigned_user_id = row.get('assigned_to')
            if pd.notna(assigned_user_id):
                success = assign_ticket(base_url, domain_id, ticket_id, workflow_id, packet_task_id, str(assigned_user_id), token)
            else:
                logger.warning(f"Ticket ID: {ticket_id} 的 'assign_ticket' 動作缺少 'assigned_to' 欄位。")

        elif action_type == 'complete_ticket': # 完成票證 (或更新狀態)
            new_status = row.get('new_status')
            if pd.notna(new_status):
                success = complete_ticket(base_url, domain_id, ticket_id, workflow_id, packet_task_id, str(new_status), token)
            else:
                logger.warning(f"Ticket ID: {ticket_id} 的 'complete_ticket' 動作缺少 'new_status' 欄位。")
        
        # 你可以在這裡添加更多 'elif action_type == '其他類型':' 的判斷
        # 例如：'add_comment', 'change_priority' 等等，並呼叫對應的 API 函數

        else:
            logger.warning(f"Ticket ID: {ticket_id} 的 'action_type': '{action_type}' 不支援。")
            failed_count += 1
            continue

        if success:
            processed_count += 1
        else:
            failed_count += 1

    logger.info(f"批次更新完成！成功處理 {processed_count} 筆，失敗 {failed_count} 筆。")


if __name__ == "__main__":
    # --- 1. 載入設定 ---
    BASE_URL, USER_ID, PASSWORD, DOMAIN_ID = load_config()

    # --- 2. 獲取 API Token ---
    AUTH_TOKEN = get_auth_token(BASE_URL, USER_ID, PASSWORD)

    if AUTH_TOKEN:
        # --- 3. 執行批次更新 ---
        # 請確保你的 CSV 檔案名稱正確，且包含 'ticket_id', 'action_type' 等欄位
        # 範例 CSV 檔案名稱為 'bulk_updates.csv'
        bulk_process_tickets(
            csv_path='bulk_updates.csv',
            base_url=BASE_URL,
            domain_id=DOMAIN_ID,
            token=AUTH_TOKEN
        )
    else:
        logger.critical("無法獲取 API Token，腳本終止。")
