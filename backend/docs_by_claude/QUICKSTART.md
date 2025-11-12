# 快速啟動指南

## 🚀 啟動步驟

### 1. 啟動後端服務

打開 PowerShell，執行以下命令：

```powershell
# 切換到後端目錄
cd c:\diskD\大學專題\Home_Wearable_Heart_Disease_Monitoring_Device\backend

# 安裝依賴（首次運行時需要）
pip install -r requirements.txt

# 啟動服務
python testing_backend.py
```

後端服務會在 `http://localhost:5001` 啟動。

### 2. 開啟前端頁面

有兩種方式：

#### 方式 A: 使用 VS Code Live Server（推薦）
1. 在 VS Code 中打開 `frontend/index.html`
2. 右鍵點擊編輯器，選擇 "Open with Live Server"
3. 瀏覽器會自動打開頁面

#### 方式 B: 直接打開 HTML 文件
1. 使用瀏覽器打開 `frontend/index.html`
2. **注意**: 某些功能可能因為 CORS 限制而無法正常運作

### 3. 更新 API URL

如果你要部署到雲端，需要修改 `frontend/script.js` 中的 `API_BASE_URL`：

```javascript
// 本地測試
const API_BASE_URL = "http://localhost:5001";

// 雲端部署（例如 Cloudflare Tunnel）
const API_BASE_URL = "https://your-domain.trycloudflare.com";
```

## 🧪 測試流程

### 1. 首次登入測試

1. 點擊「使用 Google 帳戶登入」按鈕
2. 完成 Google 登入流程
3. 系統會自動顯示「完善個人資料」表單
4. 填寫以下資料：
   - 生理性別: 選擇男性或女性
   - 年齡: 輸入年齡（例如: 45）
   - 胸痛類別: 選擇一個選項
   - 運動心絞痛: 選擇是或否
5. 點擊「提交資料」
6. 成功後會進入主儀表板

### 2. 健康數據提交測試

1. 在主儀表板中，點擊「健康數據」分頁
2. 填寫以下資料：
   - 靜息血壓: 輸入數值（例如: 120）
   - 血清膽固醇: 輸入數值（例如: 200）
   - 空腹血糖: 輸入數值（例如: 95）
3. 點擊「提交數據」
4. 系統會顯示成功訊息
5. 健康摘要會自動更新

### 3. 再次登入測試

1. 點擊右上角的「登出」按鈕
2. 再次使用相同的 Google 帳戶登入
3. 這次應該直接進入主儀表板（不會再要求填寫資料）

## 🛠️ 測試 API（可選）

如果你想直接測試後端 API：

```powershell
# 安裝 requests 庫
pip install requests

# 執行測試腳本
cd backend
python test_api.py
```

測試腳本會自動執行所有 API 並顯示結果。

## ⚠️ 常見問題

### 1. 後端服務無法啟動
- 確認已安裝所有依賴套件
- 檢查 5001 端口是否被占用
- 查看終端機中的錯誤訊息

### 2. 前端無法連接後端
- 確認後端服務正在運行
- 檢查 `script.js` 中的 `API_BASE_URL` 是否正確
- 打開瀏覽器開發者工具 (F12) 查看 Console 中的錯誤

### 3. Google 登入失敗
- 確認網路連接正常
- 檢查 Google Client ID 是否有效
- 查看瀏覽器 Console 中的錯誤訊息

### 4. WebSocket 連接失敗
- 確認後端支援 WebSocket
- 檢查防火牆設定
- 確認 API token 有效

## 📊 監控後端日誌

後端會在終端機中顯示詳細的日誌，包括：
- 接收到的請求
- 用戶資料變更
- WebSocket 連接狀態
- 錯誤訊息

監控這些日誌可以幫助你理解系統運作和排查問題。

## 🔄 資料持久化注意事項

**重要**: 目前後端使用記憶體存儲資料，重啟服務後所有資料會消失。

如果需要資料持久化，建議：
1. 使用資料庫（SQLite, PostgreSQL, MongoDB 等）
2. 實作資料匯出/匯入功能
3. 定期備份資料

## 📝 開發建議

### 前端開發
- 使用瀏覽器開發者工具 (F12) 查看 Console 和 Network
- 修改 JavaScript 後記得重新整理頁面
- 使用 Live Server 可以自動重新整理

### 後端開發
- 修改 Python 程式碼後需要重新啟動服務
- 使用 `print()` 輸出除錯訊息
- 建議使用 Flask 的 debug 模式（但不要在正式環境使用）

## 🎯 下一步

完成基本測試後，你可以：
1. 自訂健康評估邏輯
2. 整合真實的 ML 模型
3. 添加更多健康指標
4. 實作通知功能
5. 部署到雲端平台

祝你開發順利！🎉
