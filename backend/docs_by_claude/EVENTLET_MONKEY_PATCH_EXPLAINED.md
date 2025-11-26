# 🐒 Eventlet Monkey Patch 詳解

## 📋 這段代碼是什麼？

```python
# eventlet imports and monkey patching must be done before other imports
import eventlet
import eventlet.wsgi
eventlet.monkey_patch()
```

## 🎯 它解決了什麼問題？

### 🔄 傳統 Web 服務器的問題

在傳統的 Flask 應用中，每個請求都是**同步處理**的：

```python
@app.route('/api/slow')
def slow_endpoint():
    time.sleep(5)  # 這個請求會阻塞 5 秒
    return "Done"
```

**問題：**
- 一個慢請求會阻塞整個服務器
- 無法同時處理多個請求
- WebSocket 連接會中斷

### ⚡ Eventlet 的解決方案

Eventlet 使用 **協程 (coroutines)** 和 **綠色線程 (green threads)**：

```python
import eventlet
eventlet.monkey_patch()  # 🔑 關鍵：猴子補丁

@app.route('/api/slow')
def slow_endpoint():
    eventlet.sleep(5)  # 非阻塞的睡眠
    return "Done"
```

**優勢：**
- ✅ 單個進程可以處理數千個並發連接
- ✅ WebSocket 連接保持活躍
- ✅ 內存使用更高效

## 🐒 Monkey Patch 是什麼？

### 補丁的原理

**Monkey Patch** = **動態替換函數**

```python
# 原始代碼
import time
time.sleep(5)  # 阻塞整個線程

# Monkey Patch 後
import eventlet
eventlet.monkey_patch()

time.sleep(5)  # 實際調用 eventlet.sleep(5)，非阻塞
```

### 它替換了哪些函數？

```python
# 標準庫替換
import socket  # → eventlet.green.socket
import thread  # → eventlet.green.thread
import time    # → eventlet.green.time
import os      # → eventlet.green.os

# 第三方庫替換
import requests  # → 異步版本
```

## 🚀 在您的專題中的應用

### 1. WebSocket 支持

```python
# 沒有 eventlet：WebSocket 連接會斷開
@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
    while True:
        time.sleep(1)  # 阻塞！
        ws.send(data)

# 有 eventlet：WebSocket 保持活躍
@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
    while True:
        eventlet.sleep(1)  # 非阻塞！
        ws.send(data)
```

### 2. 並發處理

```python
# 可以同時處理多個用戶的實時 ECG 數據
# 每個用戶的 WebSocket 連接都是獨立的協程
# 不會互相阻塞
```

### 3. 資源效率

```
傳統方式: 1000 個用戶 = 1000 個線程 = 高內存使用
Eventlet:  1000 個用戶 = 1 個進程 + 1000 個協程 = 低內存使用
```

## ⚠️ 為什麼要放在最前面？

### 1. 導入順序問題

```python
# ❌ 錯誤順序
import flask
import eventlet
eventlet.monkey_patch()  # 太晚了！flask 已經導入了阻塞版本

# ✅ 正確順序
import eventlet
eventlet.monkey_patch()  # 先打補丁
import flask              # flask 會使用非阻塞版本
```

### 2. 模塊依賴

許多模塊在導入時就決定了使用哪個實現：

```python
# socket 模塊在導入時就鎖定了實現
import socket        # 使用標準 socket
eventlet.monkey_patch()  # 太晚了！

# 正確方式
eventlet.monkey_patch()  # 先替換
import socket        # 使用 eventlet.green.socket
```

## 🔧 技術細節

### 協程 vs 線程

| 特性 | 傳統線程 | Eventlet 協程 |
|------|----------|---------------|
| 創建成本 | 高 (1MB 內存) | 低 (2KB 內存) |
| 切換成本 | 高 (系統調用) | 低 (用戶空間) |
| 並發數量 | 有限 (~1000) | 高 (~10,000+) |
| 調試難度 | 中等 | 較難 |

### 工作原理

```python
# Eventlet 內部實現
def monkey_patch():
    # 替換標準庫
    import sys
    sys.modules['socket'] = eventlet.green.socket
    sys.modules['time'] = eventlet.green.time
    sys.modules['thread'] = eventlet.green.thread
    
    # 替換內建函數
    __builtins__['open'] = eventlet.green.open
```

## 📊 在您的專題中的實際效果

### 沒有 Eventlet
```
用戶 A 請求 ECG 數據 → 服務器處理 2 秒 → 用戶 B 等待
用戶 B 請求 ECG 數據 → 必須等用戶 A 完成
結果：用戶體驗差，WebSocket 經常斷線
```

### 有 Eventlet
```
用戶 A 請求 ECG 數據 → 協程 A 處理
用戶 B 請求 ECG 數據 → 協程 B 處理（同時）
用戶 C 請求 ECG 數據 → 協程 C 處理（同時）
結果：所有用戶都能實時獲取數據
```

## 🛠️ 常見問題

### Q: 為什麼需要這個？
**A:** 因為您的應用有 WebSocket 實時 ECG 數據傳輸，需要非阻塞的異步處理。

### Q: 會不會有性能問題？
**A:** 不會。Eventlet 專門為高並發設計，比傳統線程更高效。

### Q: 調試會不會很難？
**A:** 協程調試確實比較複雜，但對於您的用例（實時數據流）非常適合。

### Q: 可以移除嗎？
**A:** 不建議。WebSocket 功能依賴這個異步處理。

## 🎯 總結

這段代碼是 **Flask + WebSocket 應用的核心組件**：

1. **啟用異步處理** - 支持多個並發 WebSocket 連接
2. **優化資源使用** - 低內存，高並發
3. **保持連接活躍** - ECG 數據能實時傳輸
4. **提升用戶體驗** - 多用戶同時使用不會卡頓

**簡單來說：讓您的醫療監測系統能同時服務多個用戶，提供實時的心臟數據！** 🫀📊

---

**補充：** 如果您將來需要更高的性能，可以考慮 `gunicorn` + `gevent` 或 `uvicorn` + `fastapi` 的組合。