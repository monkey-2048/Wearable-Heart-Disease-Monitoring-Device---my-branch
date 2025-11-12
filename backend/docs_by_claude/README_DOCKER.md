# 🐳 Docker 快速啟動指南

## 一鍵啟動命令

### Windows (PowerShell)

```powershell
# 切換到 backend 目錄
cd c:\diskD\大學專題\Home_Wearable_Heart_Disease_Monitoring_Device\backend

# 使用 Docker Compose 啟動
docker-compose up --build
```

### 查看 Cloudflare URL

啟動後，終端會顯示：

```
========================================
✓ 所有服務已成功啟動！
========================================

📡 Cloudflare Tunnel URL:
   https://xxxxx-xxx-xxx.trycloudflare.com
```

## 停止服務

```powershell
# 停止容器（保留資料）
docker-compose stop

# 停止並刪除容器
docker-compose down
```

## 查看日誌

```powershell
# 即時查看日誌
docker-compose logs -f

# 查看最後 100 行
docker-compose logs --tail=100
```

## 重新啟動

```powershell
# 重新啟動服務
docker-compose restart

# 完全重建並啟動
docker-compose up --build --force-recreate
```

## 更新前端配置

1. 複製終端顯示的 Cloudflare URL
2. 打開 `frontend/script.js`
3. 修改第 22 行：

```javascript
const API_BASE_URL = "https://your-tunnel-url.trycloudflare.com";
```

## 故障排除

### 端口被占用
```powershell
# 查看端口使用情況
netstat -ano | findstr :5001

# 終止占用端口的程式
taskkill /PID <PID> /F
```

### 無法啟動 Docker
```powershell
# 確認 Docker Desktop 是否運行
# 檢查系統托盤的 Docker 圖示
```

### 找不到 Cloudflare URL
```powershell
# 等待 30 秒後查看日誌
docker logs heart-monitor-backend | grep "trycloudflare"
```

## 詳細文檔

完整的部署指南請參考：`DOCKER_GUIDE.md`

---

**注意**：Cloudflare Tunnel URL 每次重啟都會改變，需要更新前端配置。
