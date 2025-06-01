import requests
from datetime import datetime, timedelta
import time
import json
import os
from urllib.parse import urlparse, unquote

def download_file(url, save_path, headers=None):
    """
    下載檔案的輔助函數
    """
    try:
        print(f"📥 開始下載: {url}")
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # 寫入檔案
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(save_path)
        print(f"✅ 下載完成！檔案大小: {file_size:,} bytes")
        return True
        
    except Exception as e:
        print(f"❌ 下載失敗: {str(e)}")
        return False

def trigger_api_for_date_range(start_date, end_date, api_endpoint, headers=None, download_dir="downloads"):
    """
    觸發 API 端點，從 start_date 到 end_date 一天一次，並下載檔案
    
    Args:
        start_date: 開始日期 (格式: "2025-05-20")
        end_date: 結束日期 (格式: "2025-05-20")
        api_endpoint: API 端點 URL
        headers: 額外的 headers (可選)
        download_dir: 下載目錄 (預設: "downloads")
    """
    
    # 建立下載目錄
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"📁 建立下載目錄: {download_dir}")
    
    # 輸入驗證
    try:
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"❌ 日期格式錯誤！請使用 YYYY-MM-DD 格式")
        print(f"錯誤訊息: {e}")
        return []
    
    if current > end:
        print("❌ 開始日期不能晚於結束日期！")
        return []
    
    results = []
    
    while current <= end:
        # 格式化日期
        date_str = current.strftime("%Y-%m-%d")
        # 修正：加上正確的時區格式（注意有兩個 :00）
        start_date_with_time = current.strftime("%Y-%m-%dT00:00:00:00-0400")
        
        # 準備 payload
        payload = {
            "name": f"change report cisco {date_str}",
            "startDate": start_date_with_time
        }
        
        print(f"\n{'='*60}")
        print(f"🗓️  正在處理日期: {date_str}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # 發送 POST 請求
            print(f"🔄 發送請求到 API...")
            response = requests.post(
                api_endpoint,
                json=payload,
                headers=headers,
                allow_redirects=False
            )
            
            # 檢查回應
            if response.status_code in [200, 201, 202, 302, 303]:
                location = response.headers.get('Location') or response.headers.get('location')
                if location:
                    print(f"✅ API 回應成功！")
                    print(f"📍 Location: {location}")
                    
                    # 等待檔案生成
                    print(f"⏳ 等待 10 秒讓檔案生成...")
                    for i in range(10, 0, -1):
                        print(f"   還剩 {i} 秒...", end='\r')
                        time.sleep(1)
                    print("   檔案應該準備好了！")
                    
                    # 下載檔案
                    # 從 URL 產生檔名
                    parsed_url = urlparse(location)
                    filename = os.path.basename(unquote(parsed_url.path))
                    if not filename:
                        filename = f"cisco_report_{date_str}.pdf"  # 預設檔名
                    else:
                        # 確保檔名包含日期以便識別
                        name, ext = os.path.splitext(filename)
                        filename = f"{name}_{date_str}{ext}"
                    
                    save_path = os.path.join(download_dir, filename)
                    
                    # 執行下載
                    download_success = download_file(location, save_path, headers)
                    
                    results.append({
                        'date': date_str,
                        'status': 'success' if download_success else 'download_failed',
                        'location': location,
                        'filename': filename if download_success else None,
                        'status_code': response.status_code
                    })
                else:
                    print("⚠️  成功但沒有 location header")
                    results.append({
                        'date': date_str,
                        'status': 'success_no_location',
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'response': response.text[:500]
                    })
            else:
                print(f"❌ API 錯誤！狀態碼: {response.status_code}")
                print(f"回應內容: {response.text[:200]}...")
                results.append({
                    'date': date_str,
                    'status': 'error',
                    'status_code': response.status_code,
                    'error': response.text[:500]
                })
                
        except requests.exceptions.RequestException as e:
            print(f"💥 網路錯誤: {type(e).__name__}: {str(e)}")
            results.append({
                'date': date_str,
                'status': 'network_error',
                'error': str(e)
            })
        except Exception as e:
            print(f"💥 未預期的錯誤: {type(e).__name__}: {str(e)}")
            results.append({
                'date': date_str,
                'status': 'exception',
                'error': str(e)
            })
        
        # 移到下一天
        current += timedelta(days=1)
        
        # 避免太快打爆人家的 API（如果還有下一天的話）
        if current <= end:
            print("\n💤 休息 2 秒再處理下一天...")
            time.sleep(2)
    
    return results

# 使用範例
if __name__ == "__main__":
    # API 設定
    API_ENDPOINT = "https://your-api-endpoint.com/api/reports"  # 請替換成實際的 API 端點
    
    # 如果需要認證的話，可以加上 headers
    HEADERS = {
        "Authorization": "Bearer YOUR_TOKEN_HERE",  # 如果需要的話
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 輸入日期範圍
    print("🚀 Cisco Report 下載工具")
    print("-" * 40)
    start_date = input("請輸入開始日期 (格式: YYYY-MM-DD): ").strip()
    end_date = input("請輸入結束日期 (格式: YYYY-MM-DD): ").strip()
    
    # 詢問下載目錄
    download_dir = input("請輸入下載目錄 (預設: downloads): ").strip()
    if not download_dir:
        download_dir = "downloads"
    
    # 執行
    results = trigger_api_for_date_range(
        start_date=start_date,
        end_date=end_date,
        api_endpoint=API_ENDPOINT,
        headers=HEADERS,
        download_dir=download_dir
    )
    
    # 顯示總結
    print("\n" + "=" * 60)
    print("📊 執行總結：")
    success_count = sum(1 for r in results if r['status'] == 'success')
    download_failed = sum(1 for r in results if r['status'] == 'download_failed')
    error_count = sum(1 for r in results if r['status'] in ['error', 'exception', 'network_error'])
    
    print(f"✅ 成功下載: {success_count} 個檔案")
    if download_failed > 0:
        print(f"⚠️  下載失敗: {download_failed} 個檔案")
    print(f"❌ API 錯誤: {error_count} 筆")
    
    # 列出下載的檔案
    if success_count > 0:
        print(f"\n📁 下載的檔案在 '{download_dir}' 目錄：")
        for r in results:
            if r['status'] == 'success' and r.get('filename'):
                print(f"   - {r['filename']}")
    
    # 儲存執行記錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'download_log_{timestamp}.json'
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📝 執行記錄已儲存到 {log_filename}")
    
    print("\n✨ 完成！")