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

# 測試用的範例資料 - 修正版本
sample_log = '''Members changed from [N-23.67.78.0:local,N-104.103.70.0:local,N-23.77.200.0:local,N-95.101.237.0:local] to [N-23.67.78.0:local,N-104.103.70.0:local,N-23.205.103.0:local,N-23.212.111.0:local,N-23.77.200.0:local,N-95.101.237.0:local]'''

# 或者如果要處理完整的 JSON 格式
def parse_json_log(json_text):
    """
    處理 JSON 格式的 log 記錄
    """
    try:
        import json
        # 清理字串，移除多餘的引號和格式
        cleaned = json_text.strip().replace("'", '"')
        log_data = json.loads(cleaned)
        return log_data.get('summary', '')
    except:
        # 如果不是標準 JSON，直接當作字串處理
        return json_text

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