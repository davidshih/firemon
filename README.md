# FireMon 專案

這是一個 Python 專案，使用虛擬環境進行依賴管理。

## 專案設置

### 1. 啟動虛擬環境

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 3. 執行程式

```bash
python main.py
```

## 專案結構

```
firemon/
├── venv/                 # Python 虛擬環境
├── main.py              # 主程式文件
├── requirements.txt     # Python 依賴套件清單
├── README.md           # 專案說明文件
└── .gitignore          # Git 忽略文件清單
```

## 開發指南

1. 在 `main.py` 中添加您的主要程式邏輯
2. 在 `requirements.txt` 中添加需要的 Python 套件
3. 使用虛擬環境來隔離專案依賴

## 常用命令

```bash
# 啟動虛擬環境
source venv/bin/activate

# 安裝新套件
pip install package_name

# 更新 requirements.txt
pip freeze > requirements.txt

# 停用虛擬環境
deactivate
