# FireMon Policy Optimizer 自動化工具

這是一個專為 FireMon Policy Optimizer 設計的自動化工具，可以自動處理 PO tickets 並截取政策變更的截圖。

## 功能特色

- 🤖 **自動登入** FireMon 系統
- 📋 **自動處理** 前兩個 PO tickets
- 🔍 **智慧搜尋** 政策修訂變更
- 📸 **自動截圖** 匹配的規則變更
- 🎯 **多重選擇器** 支援不同版本的 FireMon 介面
- 📝 **詳細日誌** 記錄每個步驟
- 🛠️ **CLI 介面** 靈活的命令列操作

## 快速開始

### 1. 安裝依賴

```bash
# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt
```

### 2. 配置設定

複製範例配置檔案：
```bash
cp .env.example .env
```

編輯 `.env` 檔案，設定您的 FireMon 資訊：
```env
FIREMON_URL=https://your-firemon-instance.com
FIREMON_USERNAME=your_username
FIREMON_PASSWORD=your_password
```

### 3. 執行自動化

```bash
# 使用配置檔案
python main.py

# 或直接指定參數
python main.py --url https://firemon.example.com --username admin --password secret

# 無頭模式執行
python main.py --headless

# 查看當前配置
python main.py --config
```

## 使用方式

### 命令列參數

```bash
python main.py [選項]

選項:
  --url URL           FireMon 實例 URL
  --username USER     登入用戶名
  --password PASS     登入密碼
  --headless          無頭模式執行（不顯示瀏覽器）
  --timeout SECONDS   元素等待超時時間（預設: 20 秒）
  --screenshot-dir DIR 截圖保存目錄（預設: ./screenshots）
  --config            顯示當前配置
  --verbose, -v       詳細輸出
  --help              顯示幫助訊息
  --version           顯示版本資訊
```

### Jupyter Notebook

如果您偏好逐步執行和除錯，可以使用 `firemon_automation.ipynb`：

```bash
jupyter notebook firemon_automation.ipynb
```

### 直接使用 Python 腳本

```bash
python firemon_automation.py --url YOUR_URL --username YOUR_USER --password YOUR_PASS
```

## 專案結構

```
firemon/
├── main.py                    # CLI 主程式
├── firemon_automation.py      # 自動化核心邏輯
├── firemon_automation.ipynb   # Jupyter Notebook 版本
├── config.py                  # 配置設定
├── utils.py                   # 工具函數
├── requirements.txt           # 依賴套件
├── .env.example              # 配置範例
├── screenshots/              # 截圖目錄
├── logs/                     # 日誌目錄
└── README.md                 # 說明文件
```

## 自動化流程

1. **登入 FireMon** - 自動填寫帳號密碼並登入
2. **導航至 Policy Optimizer** - 找到並點擊 PO 連結
3. **取得 PO Tickets** - 獲取前兩個 PO tickets
4. **提取規則資訊** - 從每個 ticket 提取規則名稱
5. **開啟政策修訂** - 點擊政策修訂連結
6. **查看變更** - 點擊 "View Changes" 按鈕
7. **匹配規則** - 找到對應的規則變更行
8. **截取截圖** - 對匹配的規則進行截圖
9. **生成報告** - 列出所有截圖檔案

## 故障排除

### 常見問題

1. **登入失敗**
   - 檢查用戶名/密碼欄位選擇器是否正確
   - 確認帳號密碼正確
   - 檢查是否有驗證碼或雙因子認證

2. **找不到元素**
   - 使用瀏覽器開發者工具檢查元素
   - 更新對應的選擇器（ID、class name、XPath）
   - 增加等待時間

3. **截圖問題**
   - 確保截圖目錄有寫入權限
   - 檢查元素是否可見
   - 使用全頁面截圖作為備選

### 調試模式

```bash
# 詳細輸出模式
python main.py --verbose

# 查看日誌檔案
tail -f logs/app.log
```

### 選擇器自訂

如果 FireMon 介面更新，您可能需要修改以下選擇器：

- **登入**: `#username`, `#password`, `#login-button`
- **PO Tickets**: `.po-ticket`, `.rule-name`, `.policy-revision-link`
- **變更檢視**: `.view-changes-toggle`, `.rule-change-row`

## 環境需求

- Python 3.8+
- Chrome 瀏覽器
- ChromeDriver（自動下載）
- 網路連線至 FireMon 實例

## 授權

此專案僅供內部使用。

## 聯絡資訊

如有問題請聯絡開發團隊。