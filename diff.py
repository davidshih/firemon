import pandas as pd
import re

def parse_single_changelog(changelog_text):
    """
    解析單一 changelog 記錄，回傳 (removed_list, added_list)
    專門處理 DataFrame 中的單筆記錄 🔍
    """
    if pd.isna(changelog_text) or not changelog_text:
        return [], []
    
    # 移除換行符號和多餘空格
    cleaned_text = re.sub(r'\s+', ' ', str(changelog_text).replace('\n', ' ').replace('\r', ''))
    
    # 正則表達式找出變更模式
    pattern = r"Members changed from \[(.*?)\] to \[(.*?)\]"
    match = re.search(pattern, cleaned_text, re.DOTALL)
    
    if not match:
        return [], []
    
    old_members = match.group(1)
    new_members = match.group(2)
    
    # 解析成員清單
    def parse_members(member_string):
        items = []
        for item in member_string.split(','):
            cleaned_item = item.strip()
            if cleaned_item:
                items.append(cleaned_item)
        return items
    
    old_list = parse_members(old_members)
    new_list = parse_members(new_members)
    
    # 計算差異
    old_set = set(old_list)
    new_set = set(new_list)
    
    removed_from_old = list(old_set - new_set)
    added_to_new = list(new_set - old_set)
    
    return removed_from_old, added_to_new

def process_dataframe_changelogs(df, changelog_column='changeLog'):
    """
    批量處理 DataFrame 中的 changeLog 欄位
    新增三個欄位：changes, removed, added
    就像批量處理網管報告一樣有效率 📊
    """
    # 建立新的 DataFrame 副本，避免修改原始資料
    result_df = df.copy()
    
    # 初始化新欄位
    result_df['changes'] = ''
    result_df['removed'] = ''
    result_df['added'] = ''
    
    print(f"🔥 開始處理 {len(df)} 筆 changeLog 記錄...")
    
    processed_count = 0
    changes_found = 0
    
    for idx, row in result_df.iterrows():
        changelog = row[changelog_column]
        
        # 解析變更記錄
        removed_list, added_list = parse_single_changelog(changelog)
        
        if removed_list or added_list:
            changes_found += 1
            
            # 格式化變更摘要
            change_summary = f"移除:{len(removed_list)}項, 新增:{len(added_list)}項"
            
            # 格式化移除項目 (用逗號分隔)
            removed_text = ', '.join(removed_list) if removed_list else ''
            
            # 格式化新增項目 (按你要求的格式：逗號換行)
            added_text = ',\n'.join(added_list) if added_list else ''
            
            # 更新 DataFrame
            result_df.at[idx, 'changes'] = change_summary
            result_df.at[idx, 'removed'] = removed_text
            result_df.at[idx, 'added'] = added_text
        
        processed_count += 1
        
        # 顯示進度 (每處理100筆顯示一次)
        if processed_count % 100 == 0:
            print(f"   已處理 {processed_count}/{len(df)} 筆...")
    
    print(f"✅ 處理完成！")
    print(f"   總共處理: {processed_count} 筆記錄")
    print(f"   找到變更: {changes_found} 筆")
    print(f"   無變更:   {processed_count - changes_found} 筆")
    
    return result_df

def get_change_statistics(df):
    """
    統計變更資料，產生報表
    給老闆看的數據總結 📈
    """
    stats = {
        'total_records': len(df),
        'records_with_changes': len(df[df['changes'] != '']),
        'total_removed_items': 0,
        'total_added_items': 0
    }
    
    # 計算總移除和新增項目數
    for idx, row in df.iterrows():
        if row['removed']:
            stats['total_removed_items'] += len(row['removed'].split(','))
        if row['added']:
            stats['total_added_items'] += len(row['added'].split(',\n'))
    
    print(f"\n📊 變更統計報告：")
    print(f"   總記錄數: {stats['total_records']}")
    print(f"   有變更的記錄: {stats['records_with_changes']}")
    print(f"   總移除項目: {stats['total_removed_items']}")
    print(f"   總新增項目: {stats['total_added_items']}")
    
    return stats

# 使用範例
def demo_usage():
    """
    示範如何使用這個批量處理器
    """
    print("🎯 使用範例：")
    print("""
    # 假設你有一個 DataFrame
    df = pd.read_csv('your_firewall_logs.csv')
    
    # 或者手動建立測試資料
    test_data = {
        'id': [1, 2, 3],
        'changeLog': [
            'Members changed from [A,B,C] to [A,B,D,E]',
            'Members changed from [X,Y] to [X]',
            'No changes detected'
        ]
    }
    df = pd.DataFrame(test_data)
    
    # 處理 changeLog 欄位
    result_df = process_dataframe_changelogs(df, 'changeLog')
    
    # 查看結果
    print(result_df[['id', 'changes', 'removed', 'added']])
    
    # 產生統計報告
    stats = get_change_statistics(result_df)
    
    # 儲存結果
    result_df.to_csv('processed_changes.csv', index=False)
    """)

# 測試用資料
print("🧪 建立測試資料...")
test_data = {
    'id': [1, 2, 3, 4],
    'objectName': ['test-subnet1', 'test-subnet2', 'test-subnet3', 'test-subnet4'],
    'changeLog': [
        'Members changed from [N-192.168.1.0:local,N-192.168.2.0:local,N-192.168.3.0:local] to [N-192.168.1.0:local,N-192.168.4.0:local,N-192.168.5.0:local]',
        'Members changed from [N-10.0.1.0:local,N-10.0.2.0:local] to [N-10.0.1.0:local]',
        'No network changes detected',
        'Members changed from [A,B] to [A,B,C,D,E]'
    ]
}

df = pd.DataFrame(test_data)
print("\n📋 原始資料：")
print(df)

print("\n🔥 開始批量處理...")
result_df = process_dataframe_changelogs(df, 'changeLog')

print("\n📊 處理結果：")
print(result_df[['id', 'objectName', 'changes', 'removed', 'added']])

print("\n📈 統計報告：")
stats = get_change_statistics(result_df)

print("\n💡 使用提示：")
demo_usage()

print("\n🎉 批量處理完成！現在你可以用同樣方式處理你的真實資料了 😄")