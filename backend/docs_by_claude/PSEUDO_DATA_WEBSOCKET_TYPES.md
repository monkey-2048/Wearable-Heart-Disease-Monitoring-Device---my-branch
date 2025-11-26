# 🔍 Pseudo Data & WebSocket 類型分析

## 📋 問題回答

### 1️⃣ `pseudo_data.py` 需要套用 Eventlet Monkey Patch 嗎？

**答案：不需要特別處理，因為已經被間接影響了**

### 🔄 影響鏈

```
backend_main.py (有 monkey patch)
    ↓
import pseudo_data  ← 已經被 patch 影響
    ↓
pseudo_data.py 中的所有操作都使用非阻塞版本
```

### ✅ 為什麼不需要擔心？

1. **自動生效**：Monkey patch 在 `backend_main.py` 最前面執行
2. **模塊級別**：影響整個 Python 進程的所有模塊
3. **間接導入**：`pseudo_data.py` 被 `backend_main.py` 導入，所以自動生效

### 📊 實際影響

```python
# pseudo_data.py 中的 time.sleep()
time.sleep(0.16)  # 實際是 eventlet.sleep(0.16)，非阻塞！

# 在 WebSocket 函數中使用
def send_ecg_data(ws):
    while True:
        # 這個 sleep 不會阻塞其他用戶的連接
        time.sleep(0.16)  # 非阻塞的！
        ws.send(ecg_data)
```

---

## 2️⃣ WebSocket (`ws`) 的類型是什麼？

### 🎯 **類型：Flask-Sock WebSocket 對象**

```python
from flask_sock import Sock

@sock.route('/ws/ecg/stream')
def ecg_stream(ws):  # ws 的類型是 flask_sock.WebSocket
    # ws 是一個 WebSocket 連接對象
    pass
```

### 📋 WebSocket 對象的方法

```python
# 發送數據
ws.send(message)  # 發送字符串或 JSON

# 接收數據
data = ws.receive()  # 接收客戶端發來的數據

# 關閉連接
ws.close()  # 關閉 WebSocket 連接

# 檢查連接狀態
# (Flask-Sock 自動處理連接管理)
```

### 🔧 在您的專題中的使用

```python
@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
    """
    ws 參數類型: flask_sock.WebSocket
    
    這是一個雙向通信的 WebSocket 連接對象，
    支持實時發送和接收數據
    """
    
    # 發送 ECG 數據
    ws.send(json.dumps({"points": [1.0, 2.0, 3.0]}))
    
    # 可以接收客戶端消息（如果需要的話）
    # message = ws.receive()
    
    # 連接會自動關閉（客戶端斷開或錯誤）
```

### 🌐 WebSocket 通信協議

**WebSocket 是 HTML5 的雙向通信協議：**

```
Client (Browser) ↔ WebSocket Server ↔ Flask App
       ↑               ↑               ↑
    JavaScript    TCP Connection    Python Object
```

### 📊 數據格式

```javascript
// 前端發送 (如果需要)
ws.send(JSON.stringify({
    type: "start_stream",
    user_id: "123"
}));

// 後端發送
ws.send(JSON.stringify({
    points: [1.0, 2.0, 3.0, 4.0],
    timestamp: "2025-11-26T10:30:00Z"
}));
```

### ⚡ Eventlet 的影響

**沒有 Eventlet：**
```python
@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
    while True:
        time.sleep(1)  # ❌ 阻塞！其他用戶無法連接
        ws.send(data)
```

**有 Eventlet：**
```python
@sock.route('/ws/ecg/stream') 
def ecg_stream(ws):
    while True:
        time.sleep(1)  # ✅ 非阻塞！多用戶同時連接
        ws.send(data)
```

---

## 🏗️ 架構總覽

### 數據流

```
前端 JavaScript → WebSocket 連接 → Flask-Sock → Eventlet 協程 → pseudo_data.py
                                      ↓
                               ws.send() 方法發送數據
```

### 類型層次

```
flask_sock.WebSocket (具體類型)
    ↑
flask_sock.Connection (基類)
    ↑  
WebSocket 協議標準
```

### 🔒 安全特性

- **自動驗證**：WebSocket 路由可以檢查 token
- **連接隔離**：每個用戶的 WebSocket 是獨立的
- **自動清理**：連接斷開時自動清理資源

---

## 🎯 實務建議

### 對於 pseudo_data.py

```python
# pseudo_data.py - 不需要特別修改
def send_ecg_data(ws):  # ws: flask_sock.WebSocket
    """WebSocket 發送 ECG 數據"""
    while True:
        # 自動使用 eventlet.sleep()，非阻塞
        time.sleep(0.16)
        
        # 發送數據到前端
        data = generate_ecg_points()
        ws.send(json.dumps({"points": data}))
```

### 對於 WebSocket 處理

```python
# backend_main.py
@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
    """處理 ECG 實時數據流"""
    
    # 驗證 token
    token = request.args.get('token')
    if not token or not validate_token(token):
        ws.close()
        return
    
    # 啟動數據發送線程
    thread = threading.Thread(
        target=pseudo_data.send_ecg_data, 
        args=(ws,)
    )
    thread.daemon = True
    thread.start()
    
    # 等待線程完成（通常不會，因為是無限循環）
    thread.join()
```

### 📈 性能優化

1. **協程友好**：Eventlet 讓多個 WebSocket 連接高效運行
2. **內存效率**：協程比線程輕量很多
3. **實時性**：低延遲的數據傳輸

---

## ✅ 總結

- **pseudo_data.py** ✅ 自動受到 monkey patch 影響，無需修改
- **WebSocket 類型** 🎯 `flask_sock.WebSocket` 對象
- **通信協議** 🌐 HTML5 WebSocket 雙向實時通信
- **異步處理** ⚡ Eventlet 提供非阻塞協程支持

您的架構已經正確設置，可以支持多個用戶同時接收實時 ECG 數據！ 🫀📊