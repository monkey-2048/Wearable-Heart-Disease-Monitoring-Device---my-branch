# 🔐 Google 認證最佳實務建議

## 📊 當前實現分析

### 現有方式：存儲 Gmail 地址
```python
# 當前實現（不推薦）
user_email = "test.user@google.com"  # 從 Google token 提取
user_database[user_email] = {...}    # 以 email 為鍵存儲
```

### 推薦方式：使用 Google ID Token
```python
# 推薦實現
google_user_id = decode_google_token(google_token)['sub']  # Google 的唯一用戶 ID
user_database[google_user_id] = {...}  # 以 Google ID 為鍵
```

## ⚖️ 兩種方法的比較

### ❌ 方法1：存儲 Gmail 地址

**優點：**
- 簡單直觀
- 容易理解和調試
- 可以直接查看用戶身份

**缺點：**
- 🔴 **隱私風險**：存儲個人郵箱地址
- 🔴 **GDPR 合規問題**：可能違反隱私法規
- 🔴 **維護困難**：用戶改郵箱會導致數據丟失
- 🔴 **安全風險**：郵箱地址可能被濫用
- 🔴 **依賴外部服務**：Google 可能改變郵箱政策

### ✅ 方法2：使用 Google ID Token（推薦）

**優點：**
- 🟢 **隱私保護**：不存儲個人信息
- 🟢 **合規性好**：符合 GDPR 等隱私法規
- 🟢 **維護簡單**：Google ID 永不改變
- 🟢 **安全性高**：使用業界標準的 JWT
- 🟢 **可擴展性**：容易整合其他 OAuth 提供商

**缺點：**
- 🟡 **實現複雜度稍高**：需要 JWT 解析
- 🟡 **調試困難**：無法直接從數據庫看出是哪個用戶
- 🟡 **依賴 Google 服務**：需要線上驗證

## 🏗️ 推薦的實務架構

### 1. 使用 Google ID 作為主鍵

```python
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

def verify_google_token(token):
    """驗證 Google ID Token"""
    try:
        # 驗證 token 並獲取用戶信息
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            YOUR_GOOGLE_CLIENT_ID
        )

        # 提取 Google 分配的唯一用戶 ID
        google_user_id = idinfo['sub']  # 這是 Google 的唯一標識符
        email = idinfo['email']          # 可選：用於顯示，不存儲
        name = idinfo['name']            # 可選：用於顯示

        return {
            'google_id': google_user_id,
            'email': email,
            'name': name,
            'verified': True
        }
    except ValueError:
        return None

# 在認證端點中使用
@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    data = request.json
    google_token = data.get('google_token')

    if not google_token:
        abort(400, 'Missing google_token')

    # 驗證 Google token
    user_info = verify_google_token(google_token)
    if not user_info:
        abort(401, 'Invalid Google token')

    google_user_id = user_info['google_id']

    # 使用 Google ID 作為數據庫鍵
    is_new_user = google_user_id not in user_database

    if is_new_user:
        user_database[google_user_id] = {
            "google_id": google_user_id,
            "name": user_info['name'],
            "email_verified": user_info.get('email_verified', False),
            "profile_completed": False,
            "profile_data": None,
            "health_data": [],
            "created_at": datetime.now().isoformat()
        }

    # 生成應用內部的 session token
    session_token = generate_session_token(google_user_id)

    return jsonify({
        "api_token": session_token,
        "is_new_user": is_new_user,
        "user": {
            "name": user_info['name'],
            "google_id": google_user_id  # 前端不需要知道具體 ID
        }
    })
```

### 2. Session Token 管理

```python
import secrets
import hashlib

# 存儲活躍的 session
active_sessions = {}

def generate_session_token(google_user_id):
    """生成安全的 session token"""
    # 創建隨機 token
    raw_token = secrets.token_urlsafe(32)

    # 創建 token hash 用於數據庫查找
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # 存儲 session 信息
    active_sessions[token_hash] = {
        'google_user_id': google_user_id,
        'created_at': datetime.now(),
        'expires_at': datetime.now() + timedelta(hours=24)  # 24小時過期
    }

    return raw_token  # 返回原始 token 給用戶

def validate_session_token(token):
    """驗證 session token"""
    if not token:
        return None

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = active_sessions.get(token_hash)

    if not session:
        return None

    # 檢查是否過期
    if datetime.now() > session['expires_at']:
        del active_sessions[token_hash]
        return None

    return session['google_user_id']
```

### 3. 認證中間件更新

```python
def check_auth(request):
    """檢查請求中是否有有效的 Authorization 標頭"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, 'Missing Authorization Header')

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            abort(401, 'Invalid Authorization Header')

        # 驗證 session token
        google_user_id = validate_session_token(token)
        if not google_user_id:
            abort(401, 'Invalid or expired token')

        # 將用戶 ID 存儲在 request 對象中供後續使用
        request.google_user_id = google_user_id

    except ValueError:
        abort(401, 'Invalid Authorization Header')
```

### 4. API 端點更新

```python
@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    check_auth(request)
    google_user_id = request.google_user_id

    if google_user_id not in user_database:
        abort(404, 'User not found')

    user_data = user_database[google_user_id]

    return jsonify({
        "is_new_user": not user_data["profile_completed"],
        "user": {
            "name": user_data["name"],
            # 不返回 email 或其他敏感信息
        }
    })

@app.route('/api/v1/user/profile', methods=['POST'])
def create_user_profile():
    check_auth(request)
    google_user_id = request.google_user_id
    data = request.json

    # ... 驗證邏輯 ...

    if google_user_id not in user_database:
        abort(404, 'User not found')

    # 更新用戶資料
    user_database[google_user_id]["profile_data"] = {
        "sex": data["sex"],
        "age": data["age"],
        "chest_pain_type": data["chest_pain_type"],
        "exercise_angina": data["exercise_angina"],
        "created_at": datetime.now().isoformat()
    }
    user_database[google_user_id]["profile_completed"] = True

    return jsonify({
        "message": "Profile created successfully",
        "profile": user_database[google_user_id]["profile_data"]
    })
```

## 🔒 安全優勢

### 隱私保護
- ✅ 不存儲個人郵箱地址
- ✅ 符合 GDPR 要求
- ✅ 減少數據洩露風險

### 安全性
- ✅ 使用 JWT 標準驗證
- ✅ Session token 有過期機制
- ✅ 雙重驗證（Google + 應用內 token）

### 可維護性
- ✅ Google ID 永不改變
- ✅ 容易處理用戶信息更新
- ✅ 支持多個 OAuth 提供商

## 📋 實施檢查清單

### 後端修改
- [ ] 安裝 `google-auth` 套件
- [ ] 實現 `verify_google_token()` 函數
- [ ] 修改用戶數據庫結構（使用 Google ID 作為鍵）
- [ ] 實現 session token 管理
- [ ] 更新所有認證相關的 API 端點
- [ ] 添加 token 過期處理

### 前端修改
- [ ] 更新登入邏輯以處理新的 token 格式
- [ ] 修改 API_BASE_URL 配置
- [ ] 測試認證流程

### 測試項目
- [ ] 新用戶註冊流程
- [ ] 現有用戶登入
- [ ] Token 過期處理
- [ ] 無效 token 拒絕
- [ ] 隱私信息不洩露

## 🚀 遷移策略

### 對於現有數據
如果已經有用戶數據，需要遷移：

```python
# 遷移腳本示例
def migrate_existing_users():
    """將現有 email 鍵轉換為 Google ID"""
    migrated_db = {}

    for email, user_data in user_database.items():
        # 模擬：從 email 生成 Google ID（實際需要用戶重新登入）
        # 在生產環境中，這需要用戶重新認證
        google_id = f"google_{hash(email)}"  # 臨時解決方案

        migrated_db[google_id] = user_data
        migrated_db[google_id]['google_id'] = google_id
        migrated_db[google_id]['migrated_from_email'] = email

    return migrated_db
```

## 📚 推薦資源

- [Google OAuth 2.0 文檔](https://developers.google.com/identity/protocols/oauth2)
- [JWT 最佳實務](https://tools.ietf.org/html/rfc8725)
- [GDPR 隱私指南](https://gdpr-info.eu/)

---

## 🎯 結論

**強烈推薦使用 Google ID Token 方法**，因為：

1. **隱私合規**：避免存儲個人信息
2. **安全性**：使用業界標準的認證機制
3. **可維護性**：Google ID 永不改變
4. **擴展性**：容易整合其他認證提供商

雖然實現複雜度稍高，但對於生產環境來說是必要的投資。
