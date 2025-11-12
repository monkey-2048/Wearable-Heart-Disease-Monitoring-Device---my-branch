# 新功能說明文件

## 📋 更新內容

### 1. 新用戶註冊流程

當用戶首次使用 Google 登入時，系統會自動檢測並引導用戶填寫基本資料表單。

#### 註冊表單欄位：
- **生理性別**: 男性 (M) / 女性 (F)
- **年齡**: 1-120 歲
- **胸痛類別**:
  - TA: 典型心絞痛 (Typical Angina)
  - ATA: 非典型心絞痛 (Atypical Angina)
  - NAP: 非心絞痛性疼痛 (Non-Anginal Pain)
  - ASY: 無症狀 (Asymptomatic)
- **是否有運動心絞痛**: 是 (Y) / 否 (N)

### 2. 健康數據頁面

新增「健康數據」分頁，允許用戶定期更新健康指標。

#### 健康數據欄位：
- **靜息血壓** (Resting Blood Pressure): 70-200 mmHg
  - 正常範圍: 90-140 mmHg
- **血清膽固醇** (Serum Cholesterol): 100-600 mm/dl
  - 正常範圍: < 200 mm/dl
- **空腹血糖** (Fasting Blood Sugar): 50-400 mg/dl
  - 正常範圍: 70-100 mg/dl

## 🔌 新增 API 端點

### 1. Google 登入 (更新)
```
POST /api/auth/google
```
**Request Body:**
```json
{
  "google_token": "string"
}
```
**Response:**
```json
{
  "api_token": "string",
  "is_new_user": boolean,
  "user": {
    "name": "string",
    "email": "string"
  }
}
```

### 2. 獲取當前用戶資訊 (更新)
```
GET /api/auth/me
Authorization: Bearer {token}
```
**Response:**
```json
{
  "is_new_user": boolean,
  "user": {
    "name": "string",
    "email": "string"
  }
}
```

### 3. 創建用戶資料 (新增)
```
POST /api/v1/user/profile
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "sex": "M" | "F",
  "age": number,
  "chest_pain_type": "TA" | "ATA" | "NAP" | "ASY",
  "exercise_angina": "Y" | "N"
}
```
**Response:**
```json
{
  "message": "Profile created successfully",
  "profile": {
    "sex": "string",
    "age": number,
    "chest_pain_type": "string",
    "exercise_angina": "string",
    "created_at": "ISO datetime"
  }
}
```

### 4. 提交健康數據 (新增)
```
POST /api/v1/user/health-data
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "resting_bp": number,
  "cholesterol": number,
  "fasting_bs": number
}
```
**Response:**
```json
{
  "message": "Health data submitted successfully",
  "data": {
    "resting_bp": number,
    "cholesterol": number,
    "fasting_bs": number,
    "timestamp": "ISO datetime"
  }
}
```

### 5. 獲取健康數據歷史 (新增)
```
GET /api/v1/user/health-data
Authorization: Bearer {token}
```
**Response:**
```json
{
  "health_data": [
    {
      "resting_bp": number,
      "cholesterol": number,
      "fasting_bs": number,
      "timestamp": "ISO datetime"
    }
  ]
}
```

## 🧪 測試方式

### 啟動後端服務
```powershell
cd backend
python testing_backend.py
```

### 測試 API（可選）
```powershell
cd backend
pip install requests
python test_api.py
```

### 開啟前端
在瀏覽器中打開 `frontend/index.html`

## 📝 用戶流程

1. **首次登入**:
   - 用戶使用 Google 登入
   - 系統檢測到是新用戶
   - 顯示註冊表單
   - 用戶填寫基本資料並提交
   - 進入主儀表板

2. **再次登入**:
   - 用戶使用 Google 登入
   - 系統檢測到用戶已完成註冊
   - 直接進入主儀表板

3. **更新健康數據**:
   - 點擊「健康數據」分頁
   - 填寫最新的健康指標
   - 提交數據
   - 系統顯示成功訊息
   - 自動刷新健康摘要

## 📂 修改的文件

### Frontend
- `frontend/index.html` - 新增註冊表單和健康數據頁面
- `frontend/script.js` - 新增表單處理邏輯和 API 調用
- `frontend/style.css` - 無需修改（表單使用 Tailwind CSS）

### Backend
- `backend/testing_backend.py` - 新增用戶資料庫和 API 端點

### 新增文件
- `backend/test_api.py` - API 測試腳本

## 🔒 注意事項

1. 目前後端使用記憶體存儲用戶資料，重啟後資料會消失
2. 實際應用中應該使用資料庫（如 PostgreSQL, MongoDB）
3. Google 登入的 token 驗證目前是模擬的，實際應用需要真實驗證
4. API token 應該有過期時間和刷新機制
5. 健康數據應該加入更多的驗證和異常檢測

## 🚀 未來改進建議

- [ ] 實作真實的資料庫存儲
- [ ] 添加資料編輯功能
- [ ] 實作健康數據的圖表顯示
- [ ] 添加資料匯出功能（CSV/PDF）
- [ ] 實作多語言支持
- [ ] 添加資料刪除和隱私控制功能
