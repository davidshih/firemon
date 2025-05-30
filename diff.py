import pandas as pd
import re
import json

def parse_firewall_changes(log_text):
    """
    解析防火牆變更記錄，提取變更前後的差異
    就像在找出網管到底改了什麼設定一樣 🔍
    """
    
    # 使用正則表達式提取變更資訊
    # 找出 "Members changed from [舊設定] to [新設定]" 的部分
    pattern = r"Members changed from \[(.*?)\] to \[(.*?)\]"
    match = re.search(pattern, log_text)
    
    if not match:
        print("找不到變更記錄，是不是網管偷懶沒寫清楚？ 🤔")
        return None
    
    old_members = match.group(1)
    new_members = match.group(2)
    
    # 解析成員清單 (用逗號分隔)
    old_list = [member.strip() for member in old_members.split(',') if member.strip()]
    new_list = [member.strip() for member in new_members.split(',') if member.strip()]
    
    # 轉換成集合來比較差異
    old_set = set(old_list)
    new_set = set(new_list)
    
    # 計算差異
    removed_from_old = old_set - new_set  # 從舊的移除的項目
    added_to_new = new_set - old_set      # 新增的項目
    
    # 建立結果 DataFrame
    results = []
    
    # 處理移除的項目
    for item in removed_from_old:
        results.append({
            'change_type': 'removed',
            'member': item,
            'removed_from_old': item,
            'added_to_new': ''
        })
    
    # 處理新增的項目
    for item in added_to_new:
        results.append({
            'change_type': 'added',
            'member': item,
            'removed_from_old': '',
            'added_to_new': item
        })
    
    # 處理沒有變更的項目 (保持不變)
    unchanged = old_set & new_set
    for item in unchanged:
        results.append({
            'change_type': 'unchanged',
            'member': item,
            'removed_from_old': '',
            'added_to_new': ''
        })
    
    df = pd.DataFrame(results)
    
    # 顯示統計資訊
    print(f"📊 變更統計：")
    print(f"   移除項目：{len(removed_from_old)} 個")
    print(f"   新增項目：{len(added_to_new)} 個")
    print(f"   不變項目：{len(unchanged)} 個")
    print(f"   總共處理：{len(results)} 筆記錄")
    
    return df, removed_from_old, added_to_new

def create_summary_df(removed_items, added_items):
    """
    建立摘要 DataFrame，專門顯示差異
    適合給老闆看的那種簡潔版本 📋
    """
    summary_data = []
    
    # 計算最大長度，確保兩個欄位對齊
    max_len = max(len(removed_items), len(added_items))
    
    removed_list = list(removed_items) + [''] * (max_len - len(removed_items))
    added_list = list(added_items) + [''] * (max_len - len(added_items))
    
    for i in range(max_len):
        summary_data.append({
            'removed_from_old': removed_list[i],
            'added_to_new': added_list[i]
        })
    
    return pd.DataFrame(summary_data)

# 測試用的範例資料 (基於圖片中的內容)
sample_log = """
{'id': 2234893, 'action': 'MODIFY', 'objectType': 'NETWORK_OBJECT', 'objectMatchId': 'bd6b79b9-440f-43aa-9bbe-0d06050043f',
'objectName': 'Akamai-lb-subnets:local', 'summary': 'Members changed from [N-23.67.78.0:local,N-104.103.70.0:local,N-
104.120.208.0:local,N-2.19.98.0:local,N-2.20.137.0:local,N-23.14.129.0:local,N-23.192.127.0:local,N-23.198.13.0:local,N-
23.200.82.0:local,N-23.201.31.0:local,N-23.206.187.0:local,N-23.212.48.0:local,N-23.213.19.0:local,N-23.218.233.0:local,N-
23.219.171.0:local,N-23.220.104.0:local,N-23.36.66.0:local,N-23.40.189.0:local,N-23.41.246.0:local,N-23.44.98.0:local,N-
23.45.180.0:local,N-23.45.44.0:local,N-23.47.205.0:local,N-23.47.58.0:local,N-23.48.200.0:local,N-23.52.98.0:local,N-
23.53.123.0:local,N-23.55.63.0:local,N-23.58.89.0:local,N-23.62.22.0:local,N-23.62.36.0:local,N-23.63.30.0:local,N-
23.77.200.0:local,N-95.101.237.0:local] to [N-23.67.78.0:local,N-104.103.70.0:local,N-104.120.208.0:local,N-2.19.98.0:local,N-
2.20.137.0:local,N-23.14.129.0:local,N-23.192.127.0:local,N-23.198.13.0:local,N-23.200.82.0:local,N-23.201.31.0:local,N-
23.205.103.0:local,N-23.206.187.0:local,N-23.212.111.0:local,N-23.212.48.0:local,N-23.213.19.0:local,N-23.218.233.0:local,N-
23.219.171.0:local,N-23.219.80.0:local,N-23.220.104.0:local,N-23.36.66.0:local,N-23.40.189.0:local,N-23.41.246.0:local,N-
23.44.202.0:local,N-23.44.98.0:local,N-23.45.180.0:local,N-23.45.44.0:local,N-23.47.205.0:local,N-23.47.58.0:local,N-
23.47.59.0:local,N-23.48.200.0:local,N-23.52.98.0:local,N-23.53.10.0:local,N-23.53.123.0:local,N-23.55.63.0:local,N-
23.58.89.0:local,N-23.62.22.0:local,N-23.62.36.0:local,N-23.63.30.0:local,N-23.77.200.0:local,N-95.101.237.0:local]'}
"""

# 執行解析
print("🔥 開始解析防火牆變更記錄...")
print("=" * 50)

result_df, removed, added = parse_firewall_changes(sample_log)

if result_df is not None:
    print("\n📋 完整變更記錄：")
    print(result_df.to_string(index=False))
    
    print("\n🎯 差異摘要表格：")
    summary_df = create_summary_df(removed, added)
    print(summary_df.to_string(index=False))
    
    print("\n🔍 詳細變更內容：")
    print("移除的項目 (removed_from_old)：")
    for item in sorted(removed):
        print(f"  - {item}")
    
    print("\n新增的項目 (added_to_new)：")
    for item in sorted(added):
        print(f"  + {item}")
    
    # 如果你想要儲存結果
    print("\n💾 想要儲存結果嗎？取消註解下面的程式碼：")
    print("# result_df.to_csv('firewall_changes_detail.csv', index=False)")
    print("# summary_df.to_csv('firewall_changes_summary.csv', index=False)")

print("\n🎉 解析完成！現在你知道網管到底改了什麼了 😄")