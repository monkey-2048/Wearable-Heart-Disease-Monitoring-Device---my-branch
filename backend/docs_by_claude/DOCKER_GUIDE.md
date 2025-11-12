# 🐳 Docker 部署指南

## 📋 目錄
- [快速開始](#快速開始)
- [詳細說明](#詳細說明)
- [使用方式](#使用方式)
- [常見問題](#常見問題)
- [進階設定](#進階設定)

## 🚀 快速開始

### 前置需求
- 安裝 Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- 確保 Docker 正在運行

### 一鍵啟動

```powershell
# 切換到後端目錄
cd backend

# 使用 Docker Compose 啟動（推薦）
docker-compose up --build

# 或直接使用 Docker 命令
docker build -t heart-monitor-backend .
docker run -p 5001:5001 heart-monitor-backend
```

### 查看 Cloudflare Tunnel URL

容器啟動後，會在終端顯示 Cloudflare Tunnel URL，格式如下：

```
========================================
✓ 所有服務已成功啟動！
========================================

📡 Cloudflare Tunnel URL:
   https://xxxxx-xxx-xxx.trycloudflare.com

🔧 本地 URL:
   http://localhost:5001

========================================
```

### 更新前端配置

複製顯示的 Cloudflare URL，然後更新 `frontend/script.js`：

```javascript
// 修改這一行
const API_BASE_URL = "https://your-tunnel-url.trycloudflare.com";
```

## 📖 詳細說明

### Docker 容器內容

這個 Docker 容器包含：

1. **Python 3.11** - 執行後端服務
2. **Flask 應用** - 心臟監測系統 API
3. **Cloudflared** - 建立安全的 Tunnel 連接
4. **自動啟動腳本** - 同時啟動後端和 Tunnel

### 容器架構

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Flask Backend (Port 5001)        │ │
│  │  testing_backend.py               │ │
│  └───────────┬───────────────────────┘ │
│              │                          │
│  ┌───────────▼───────────────────────┐ │
│  │  Cloudflare Tunnel                │ │
│  │  cloudflared                      │ │
│  └───────────┬───────────────────────┘ │
│              │                          │
└──────────────┼──────────────────────────┘
               │
               ▼
        Internet (HTTPS)
               │
               ▼
         Frontend 應用
```

## 🎯 使用方式

### 方式 1: Docker Compose（推薦）

```powershell
# 啟動服務
cd backend
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down

# 重新啟動
docker-compose restart
```

### 方式 2: 直接使用 Docker

```powershell
# 建立映像
docker build -t heart-monitor-backend ./backend

# 啟動容器
docker run -d \
  --name heart-monitor \
  -p 5001:5001 \
  heart-monitor-backend

# 查看日誌
docker logs -f heart-monitor

# 停止容器
docker stop heart-monitor

# 刪除容器
docker rm heart-monitor
```

### 查看服務狀態

```powershell
# 查看運行中的容器
docker ps

# 查看容器詳細資訊
docker inspect heart-monitor-backend

# 進入容器內部（除錯用）
docker exec -it heart-monitor-backend /bin/bash
```

## 🔍 查看 Tunnel URL 的方法

### 方法 1: 查看容器日誌

```powershell
docker logs heart-monitor-backend | grep "trycloudflare.com"
```

### 方法 2: 即時監控日誌

```powershell
docker logs -f heart-monitor-backend
```

### 方法 3: 進入容器查看

```powershell
docker exec -it heart-monitor-backend cat /tmp/cloudflared.log | grep "trycloudflare"
```

## ❓ 常見問題

### 1. Docker 無法啟動

**問題**: `Cannot connect to the Docker daemon`

**解決方式**:
```powershell
# 確認 Docker Desktop 是否在運行
# Windows: 檢查系統托盤是否有 Docker 圖示

# 啟動 Docker Desktop
# 或重新啟動 Docker 服務
```

### 2. 端口被占用

**問題**: `Bind for 0.0.0.0:5001 failed: port is already allocated`

**解決方式**:
```powershell
# 方式 1: 關閉占用端口的程式
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# 方式 2: 使用不同的端口
docker run -p 5002:5001 heart-monitor-backend
```

### 3. 找不到 Cloudflare URL

**問題**: 日誌中沒有顯示 Tunnel URL

**解決方式**:
```powershell
# 等待更長時間（Tunnel 需要時間啟動）
sleep 10
docker logs heart-monitor-backend

# 手動查看完整日誌
docker exec -it heart-monitor-backend cat /tmp/cloudflared.log
```

### 4. Tunnel 連接失敗

**問題**: Cloudflare Tunnel 無法建立連接

**解決方式**:
- 檢查網路連接
- 確認防火牆設定
- 重新啟動容器：`docker restart heart-monitor-backend`

### 5. 前端無法連接後端

**問題**: 前端顯示 CORS 錯誤或連接失敗

**解決方式**:
1. 確認已更新 `frontend/script.js` 中的 `API_BASE_URL`
2. 確認使用的是 HTTPS 的 Cloudflare URL
3. 清除瀏覽器快取並重新載入

## ⚙️ 進階設定

### 自訂環境變數

建立 `.env` 文件：

```env
# .env
FLASK_ENV=production
API_TOKEN=your_custom_token
PORT=5001
```

更新 `docker-compose.yml`：

```yaml
services:
  backend:
    build: .
    env_file:
      - .env
```

### 持久化資料

如果需要保存用戶資料：

```yaml
services:
  backend:
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

### 使用固定的 Cloudflare Tunnel

如果不想每次都更改 URL，可以註冊 Cloudflare Tunnel：

1. 註冊 Cloudflare 帳號
2. 安裝並驗證 cloudflared
3. 建立永久 Tunnel
4. 更新 Dockerfile 使用固定的 Tunnel

### 多容器部署

如果需要部署多個服務：

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5001:5001"
  
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
  
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: heart_monitor
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

## 🛠️ 除錯技巧

### 查看容器資源使用

```powershell
docker stats heart-monitor-backend
```

### 檢查容器健康狀態

```powershell
docker inspect --format='{{.State.Health.Status}}' heart-monitor-backend
```

### 匯出容器日誌

```powershell
docker logs heart-monitor-backend > backend-logs.txt
```

### 重建映像（清除快取）

```powershell
docker-compose build --no-cache
docker-compose up --force-recreate
```

## 📊 效能優化

### 減少映像大小

使用多階段建置：

```dockerfile
# 建置階段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 執行階段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["./start.sh"]
```

### 使用 Docker 快取

確保 requirements.txt 在其他文件之前複製，以利用 Docker 層快取。

## 🔒 安全建議

1. **不要在映像中包含敏感資料**
   - 使用環境變數
   - 使用 Docker secrets

2. **定期更新基礎映像**
   ```powershell
   docker pull python:3.11-slim
   docker-compose build --no-cache
   ```

3. **限制容器權限**
   ```yaml
   services:
     backend:
       security_opt:
         - no-new-privileges:true
       read_only: true
   ```

## 📝 部署檢查清單

- [ ] Docker 已安裝並運行
- [ ] 成功建立 Docker 映像
- [ ] 容器啟動無錯誤
- [ ] 後端服務可訪問 (localhost:5001)
- [ ] Cloudflare Tunnel URL 已顯示
- [ ] 前端已更新 API_BASE_URL
- [ ] CORS 設定正確
- [ ] WebSocket 連接正常
- [ ] 所有 API 端點可訪問

## 🎓 學習資源

- [Docker 官方文檔](https://docs.docker.com/)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [Cloudflare Tunnel 文檔](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

## 🆘 獲取幫助

如果遇到問題：

1. 查看容器日誌：`docker logs heart-monitor-backend`
2. 檢查 Docker 狀態：`docker ps -a`
3. 查看本文檔的常見問題部分
4. 搜尋 Docker 官方論壇
5. 檢查防火牆和網路設定

---

**祝你部署順利！** 🚀
