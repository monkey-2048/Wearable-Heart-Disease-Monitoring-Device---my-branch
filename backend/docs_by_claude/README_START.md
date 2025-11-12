# 🎯 在 backend 目錄啟動 Docker

## ✅ 已修復

所有 PowerShell 腳本已經移到 `backend` 目錄並修復編碼問題！

## 📁 文件位置

```
backend/
├── start-docker.ps1     ← 啟動腳本
├── stop-docker.ps1      ← 停止腳本
├── docker-compose.yml   ← Docker 配置
├── Dockerfile           ← 容器配置
├── start.sh             ← 容器啟動腳本
└── testing_backend.py   ← Flask 應用
```

## 🚀 啟動步驟

### 1️⃣ 啟動 Docker Desktop

**重要：** 必須先啟動 Docker Desktop！

在 Windows 開始菜單中找到並啟動 `Docker Desktop`，等待它完全啟動（工作列圖示不再旋轉）。

### 2️⃣ 切換到 backend 目錄

```powershell
cd C:\diskD\大學專題\Home_Wearable_Heart_Disease_Monitoring_Device\backend
```

### 3️⃣ 執行啟動腳本

```powershell
.\start-docker.ps1
```

或使用完整路徑：

```powershell
& "C:\diskD\大學專題\Home_Wearable_Heart_Disease_Monitoring_Device\backend\start-docker.ps1"
```

## 📋 腳本會執行的步驟

```
[1/5] 檢查 Docker 是否安裝
[2/5] 檢查 Docker 服務是否運行
[3/5] 確認在 backend 目錄
[4/5] 建立並啟動 Docker 容器
[5/5] 取得 Cloudflare Tunnel URL
```

## 🌐 獲取 URL

腳本執行完成後，會顯示：

```
========================================
SUCCESS!
========================================

Cloudflare URL:
  https://xxxxx-xxx-xxx.trycloudflare.com

OK URL copied to clipboard!

Local URL:
  http://localhost:5001
```

URL 會自動複製到剪貼簿！

## 🔧 下一步

1. 複製顯示的 Cloudflare URL
2. 打開 `frontend/script.js`
3. 找到第 22 行的 `API_BASE_URL`
4. 將它改為：
   ```javascript
   const API_BASE_URL = 'https://your-cloudflare-url.trycloudflare.com';
   ```

## 🛑 停止服務

```powershell
cd backend
.\stop-docker.ps1
```

## ❌ 如果遇到錯誤

### 錯誤：Docker 服務未運行

```
ERROR Docker service is not running!
Please start Docker Desktop
```

**解決方法：** 啟動 Docker Desktop

### 錯誤：無法執行腳本

```
無法辨識 '.\start-docker.ps1' 詞彙...
```

**解決方法：** 使用完整路徑和 `&` 運算符：

```powershell
& "C:\diskD\大學專題\Home_Wearable_Heart_Disease_Monitoring_Device\backend\start-docker.ps1"
```

### 錯誤：無法取得 Cloudflare URL

**解決方法：** 手動查看日誌：

```powershell
docker logs heart-monitor-backend | Select-String trycloudflare
```

## 📊 查看即時日誌

```powershell
docker-compose logs -f
```

按 `Ctrl+C` 退出日誌查看。

## 🔄 重新啟動

```powershell
docker-compose restart
```

## 🧹 完全清理

停止容器並刪除映像：

```powershell
.\stop-docker.ps1
# 當詢問時輸入 'y' 刪除映像
```

## ✨ 優點

- ✅ 所有文件在同一個 `backend` 目錄
- ✅ 一個命令啟動完整系統
- ✅ 自動獲取 Cloudflare URL
- ✅ URL 自動複製到剪貼簿
- ✅ 不需要手動安裝 Python 或依賴
- ✅ 容器化環境，乾淨隔離

---

**注意：** 確保 Docker Desktop 正在運行是最重要的前提條件！
