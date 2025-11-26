# 🔍 verify_google_token 函數詳解

## 📋 函數定義

```python
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
```

## 🎯 函數用途

`verify_google_token` 是用來**驗證 Google 登入後的 ID Token** 的核心函數。

### 它做了什麼？

1. **驗證 Token 真實性**：確保 Token 是由 Google 簽發的，不是偽造的
2. **提取用戶信息**：從 Token 中安全地獲取用戶的 Google ID、email、姓名等
3. **確認用戶身份**：提供一個可信任的唯一用戶標識符

## 🔐 安全機制

### JWT (JSON Web Token) 原理

Google ID Token 是一個 **JWT**，包含三部分：
```
header.payload.signature
```

- **Header**：指定 token 類型和加密算法
- **Payload**：包含用戶信息（Google ID、email、姓名等）
- **Signature**：Google 的數位簽章，確保 token 未被篡改

### 驗證過程

```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

idinfo = id_token.verify_oauth2_token(
    token,                    # 前端傳來的 Google ID Token
    google_requests.Request(), # HTTP 請求對象
    YOUR_GOOGLE_CLIENT_ID     # 您的 Google OAuth 客戶端 ID
)
```

這個函數會：
1. ✅ 驗證 token 的簽章
2. ✅ 檢查 token 是否過期
3. ✅ 確認 token 是為您的應用程式簽發的
4. ✅ 解碼 payload 獲取用戶信息

## 📊 Token 內容示例

驗證成功後，`idinfo` 包含：

```json
{
  "iss": "https://accounts.google.com",        // 發行者
  "sub": "123456789012345678901",              // Google 用戶 ID (唯一)
  "aud": "your-google-client-id.apps.googleusercontent.com",  // 受眾
  "exp": 1638360000,                          // 過期時間
  "iat": 1638356400,                          // 發行時間
  "email": "user@gmail.com",                   // 用戶郵箱
  "email_verified": true,                      // 郵箱是否驗證
  "name": "張小明",                            // 用戶姓名
  "picture": "https://lh3.googleusercontent.com/...",  // 頭像
  "locale": "zh-TW"                            // 地區設定
}
```

## 🏗️ 在您的專題中的使用

### 1. 前端獲取 Token

```javascript
// frontend/script.js
function handleCredentialResponse(response) {
    const googleToken = response.credential;  // 這就是 ID Token
    
    // 發送到後端驗證
    fetch(`${API_BASE_URL}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_token: googleToken })
    });
}
```

### 2. 後端驗證 Token

```python
# backend/testing_backend.py
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

def verify_google_token(token):
    """驗證 Google ID Token"""
    try:
        # 您的 Google Client ID
        CLIENT_ID = "your-google-client-id.apps.googleusercontent.com"
        
        # 驗證 token
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            CLIENT_ID
        )
        
        return {
            'google_id': idinfo['sub'],      # Google 唯一用戶 ID
            'email': idinfo['email'],        # 郵箱（用於顯示，不存儲）
            'name': idinfo['name'],          # 姓名（用於顯示）
            'verified': True
        }
    except ValueError as e:
        print(f"Token verification failed: {e}")
        return None

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    data = request.json
    google_token = data.get('google_token')
    
    if not google_token:
        abort(400, 'Missing google_token')
    
    # 🔍 這裡就是 verify_google_token 的使用
    user_info = verify_google_token(google_token)
    if not user_info:
        abort(401, 'Invalid Google token')
    
    # 使用 Google ID 作為用戶標識符
    google_user_id = user_info['google_id']
    
    # ... 後續處理
```

## ⚙️ 設置步驟

### 1. 安裝依賴

```bash
pip install google-auth
```

### 2. 獲取 Google Client ID

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建/選擇項目
3. 啟用 Google+ API
4. 創建 OAuth 2.0 憑證
5. 設置授權重定向 URI（用於 Web 應用）

### 3. 配置環境變量

```python
# 在您的應用中設置
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
```

## 🔍 常見問題

### Q: 為什麼需要這個函數？
**A:** 因為前端傳來的 Google Token 可能是偽造的。這個函數確保 token 是真的，並安全地提取用戶信息。

### Q: `sub` 字段是什麼？
**A:** `sub` 是 "Subject" 的縮寫，是 Google 為每個用戶分配的唯一標識符。它在同一個 Google 應用中永不改變。

### Q: Token 會過期嗎？
**A:** 是的，Google ID Token 通常在 1 小時後過期。前端會自動處理重新獲取。

### Q: 如果驗證失敗怎麼辦？
**A:** 函數返回 `None`，後端應該拒絕登入請求。

## 📚 相關資源

- [Google OAuth 2.0 文檔](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/sign-in/web/sign-in)
- [JWT 解釋](https://jwt.io/introduction/)

## 🎯 在您的專題中的實務應用

```python
# 建議的實現方式
def verify_google_token(token):
    """安全驗證 Google ID Token"""
    try:
        CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            CLIENT_ID
        )
        
        # 基本驗證
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
            
        if idinfo['aud'] != CLIENT_ID:
            return None
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo.get('email'),
            'name': idinfo.get('name'),
            'verified': idinfo.get('email_verified', False)
        }
        
    except Exception as e:
        print(f"Google token verification error: {e}")
        return None
```

這個函數是實現安全 Google 認證的關鍵組件，確保您的應用只接受有效的 Google 用戶登入。 🚀