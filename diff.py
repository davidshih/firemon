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

def add_change_columns_to_df(df, changelog_column='changeLog', inplace=True):
    """
    直接在原 DataFrame 上新增變更分析欄位
    新增三個欄位：changes, removed, added
    就像直接在你的資料上加工一樣！📊
    
    參數:
    - df: 你的 DataFrame
    - changelog_column: changeLog 欄位名稱 (預設 'changeLog')
    - inplace: True=直接修改原 df, False=回傳新的 df
    """
    
    # 決定要操作哪個 DataFrame
    if inplace:
        target_df = df
        print("🔧 直接在原 DataFrame 上新增欄位...")
    else:
        target_df = df.copy()
        print("📋 建立新的 DataFrame 副本...")
    
    # 初始化新欄位
    target_df['changes'] = ''
    target_df['removed'] = ''
    target_df['added'] = ''
    
    print(f"🔥 開始處理 {len(target_df)} 筆 {changelog_column} 記錄...")
    
    processed_count = 0
    changes_found = 0
    
    for idx, row in target_df.iterrows():
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
            target_df.at[idx, 'changes'] = change_summary
            target_df.at[idx, 'removed'] = removed_text
            target_df.at[idx, 'added'] = added_text
        
        processed_count += 1
        
        # 顯示進度 (每處理100筆顯示一次)
        if processed_count % 100 == 0:
            print(f"   已處理 {processed_count}/{len(target_df)} 筆...")
    
    print(f"✅ 處理完成！")
    print(f"   總共處理: {processed_count} 筆記錄")
    print(f"   找到變更: {changes_found} 筆")
    print(f"   無變更:   {processed_count - changes_found} 筆")
    
    if inplace:
        print("📊 新欄位已直接加到你的原始 DataFrame！")
        return None  # inplace 模式不回傳任何東西
    else:
        print("📊 回傳新的 DataFrame，原始資料保持不變")
        return target_df

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

# 🎯 超簡單使用方式
print("🎯 如何使用 - 直接在你的 DataFrame 上新增欄位：")
print("="*60)
print("""
# 方法1: 直接修改原 DataFrame (推薦！)
add_change_columns_to_df(df)                    # 使用預設欄位名 'changeLog'
add_change_columns_to_df(df, 'your_column')     # 如果你的欄位名不同

# 方法2: 建立新的 DataFrame (保留原始資料)
new_df = add_change_columns_to_df(df, inplace=False)

# 處理完後，你的 df 就會有新欄位：
# df['changes'] - 變更摘要
# df['removed'] - 移除的項目
# df['added']   - 新增的項目
""")

print("\n🧪 實際測試...")
print("="*60)

# 真實使用示範
print("1️⃣ 建立測試 DataFrame")
df = pd.DataFrame(test_data)
print("原始 df 欄位:", list(df.columns))

print("\n2️⃣ 直接在 df 上新增變更分析欄位")
add_change_columns_to_df(df)  # 直接修改原始 df

print("\n3️⃣ 查看結果 - df 現在有新欄位了！")
print("新的 df 欄位:", list(df.columns))
print("\n前3筆資料的變更分析：")
print(df[['id', 'changes', 'removed', 'added']].head(3))

print("\n4️⃣ 檢查某筆詳細的新增項目 (formatted with line breaks):")
if len(df[df['added'] != '']) > 0:
    sample_row = df[df['added'] != ''].iloc[0]
    print(f"ID {sample_row['id']} 的新增項目：")
    print(sample_row['added'])

print("\n🎉 完成！你的原始 df 現在有 changes, removed, added 三個新欄位了！")

print("\n💡 使用提示：")
demo_usage()

print("\n🎉 批量處理完成！現在你可以用同樣方式處理你的真實資料了 😄")