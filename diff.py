import pandas as pd
import re
import json

def parse_firewall_changes(log_text):
    """
    解析防火牆變更記錄，提取變更前後的差異
    修正版：處理多行格式和正確解析差異 🔍
    """
    
    # 移除換行符號和多餘空格，讓正則表達式更容易匹配
    cleaned_text = re.sub(r'\s+', ' ', log_text.replace('\n', ' ').replace('\r', ''))
    
    # 更強化的正則表達式，處理可能的格式變化
    pattern = r"Members changed from \[(.*?)\] to \[(.*?)\]"
    match = re.search(pattern, cleaned_text, re.DOTALL)
    
    if not match:
        print("找不到變更記錄，是不是網管偷懶沒寫清楚？ 🤔")
        print("原始文字前100字元:", log_text[:100])
        return None, None, None
    
    old_members = match.group(1)
    new_members = match.group(2)
    
    print(f"🔍 Debug - 找到的舊成員: {old_members[:100]}...")
    print(f"🔍 Debug - 找到的新成員: {new_members[:100]}...")
    
    # 更仔細地解析成員清單，處理可能的格式問題
    def parse_members(member_string):
        # 移除多餘空格，然後用逗號分割
        items = []
        for item in member_string.split(','):
            cleaned_item = item.strip()
            if cleaned_item:  # 只加入非空的項目
                items.append(cleaned_item)
        return items
    
    old_list = parse_members(old_members)
    new_list = parse_members(new_members)
    
    print(f"📊 解析結果 - 舊清單: {len(old_list)} 項目")
    print(f"📊 解析結果 - 新清單: {len(new_list)} 項目")
    
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

def format_changes_output(removed_set, added_set):
    """
    格式化變更輸出，removed 顯示為清單，added 用逗號分隔換行
    就像給老闆看的報告一樣整齊 📋
    """
    print("\n" + "="*60)
    print("🔥 防火牆變更詳細報告")
    print("="*60)
    
    print(f"\n❌ 移除的項目 (removed_from_old): {len(removed_set)} 個")
    if removed_set:
        for item in sorted(removed_set):
            print(f"  - {item}")
    else:
        print("  (沒有移除任何項目)")
    
    print(f"\n✅ 新增的項目 (added_to_new): {len(added_set)} 個")
    if added_set:
        # 按照你的要求：移除括號，用逗號換行
        sorted_added = sorted(added_set)
        for i, item in enumerate(sorted_added):
            if i == len(sorted_added) - 1:  # 最後一個不加逗號
                print(f"  {item}")
            else:
                print(f"  {item},")
    else:
        print("  (沒有新增任何項目)")

def create_formatted_df(removed_set, added_set):
    """
    建立格式化的 DataFrame，專門用於匯出
    """
    # 計算最大長度
    max_len = max(len(removed_set), len(added_set))
    
    # 準備資料
    removed_list = list(sorted(removed_set)) + [''] * (max_len - len(removed_set))
    added_list = list(sorted(added_set)) + [''] * (max_len - len(added_set))
    
    # 建立 DataFrame
    df = pd.DataFrame({
        'removed_from_old': removed_list,
        'added_to_new': added_list
    })
    
    return df

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
    print(result_df.head(10).to_string(index=False))  # 只顯示前10行避免太長
    
    # 使用新的格式化輸出
    format_changes_output(removed, added)
    
    print("\n📊 摘要 DataFrame (適合匯出)：")
    summary_df = create_formatted_df(removed, added)
    print(summary_df.head(10).to_string(index=False))
    
    # 如果你想要儲存結果
    print("\n💾 想要儲存結果嗎？取消註解下面的程式碼：")
    print("# result_df.to_csv('firewall_changes_detail.csv', index=False)")
    print("# summary_df.to_csv('firewall_changes_summary.csv', index=False)")
    
    # 特別檢查 removed 是否真的是空的
    if len(removed) == 0:
        print("\n⚠️  注意：removed_from_old 是空的！")
        print("    這可能表示：")
        print("    1. 真的沒有移除任何項目（只有新增）")
        print("    2. 正則表達式沒有正確解析到資料")
        print("    3. 資料格式跟預期不同")
        
else:
    print("❌ 解析失敗！請檢查輸入資料格式")

print("\n🎉 解析完成！")
print("如果 removed 還是顯示 set()，請提供完整的原始 log 文字，我們來除錯一下 🔧")