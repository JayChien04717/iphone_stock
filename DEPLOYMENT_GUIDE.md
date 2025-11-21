# 🚀 部署到 Streamlit Cloud 教學

## 📋 前置準備

### 1. 創建 GitHub 帳號
- 前往 [github.com](https://github.com)
- 點擊 "Sign up" 註冊（完全免費）

### 2. 創建 Streamlit Cloud 帳號
- 前往 [share.streamlit.io](https://share.streamlit.io)
- 使用 GitHub 帳號登入（完全免費）

---

## 📤 步驟 1: 上傳代碼到 GitHub

### 方法 A: 使用 GitHub Desktop（推薦，最簡單）

1. **下載 GitHub Desktop**
   - 前往 [desktop.github.com](https://desktop.github.com)
   - 下載並安裝

2. **創建 Repository**
   - 打開 GitHub Desktop
   - File → New Repository
   - Name: `stock-valuation-pro`
   - Local Path: `/Users/jay/Documents/python/stock`
   - 點擊 "Create Repository"

3. **發布到 GitHub**
   - 點擊 "Publish repository"
   - 取消勾選 "Keep this code private"（或保持私密）
   - 點擊 "Publish repository"

### 方法 B: 使用命令行

```bash
cd /Users/jay/Documents/python/stock

# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Stock Valuation Pro"

# 在 GitHub 上創建 repository 後，連接並推送
git remote add origin https://github.com/YOUR_USERNAME/stock-valuation-pro.git
git branch -M main
git push -u origin main
```

---

## 🚀 步驟 2: 部署到 Streamlit Cloud

1. **登入 Streamlit Cloud**
   - 前往 [share.streamlit.io](https://share.streamlit.io)
   - 使用 GitHub 帳號登入

2. **創建新 App**
   - 點擊 "New app"
   - Repository: 選擇 `stock-valuation-pro`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: 選擇一個名稱（例如：`my-stock-analyzer`）

3. **部署**
   - 點擊 "Deploy!"
   - 等待 2-3 分鐘部署完成

4. **完成！**
   - 您的 app 現在可以在以下網址訪問：
   - `https://YOUR-APP-NAME.streamlit.app`

---

## 📱 步驟 3: 在 iPhone 上使用

1. **打開 Safari**
   - 在 iPhone 上打開 Safari 瀏覽器
   - 訪問您的 app URL

2. **添加到主屏幕**
   - 點擊底部的「分享」按鈕（方框加箭頭）
   - 向下滾動，選擇「加入主畫面」
   - 自定義名稱（例如：Stock Pro）
   - 點擊「加入」

3. **使用**
   - 現在您的主屏幕上有一個 app 圖標
   - 點擊它就像使用原生 app 一樣！

---

## 🔄 更新 App

當您修改代碼後：

### 使用 GitHub Desktop:
1. 打開 GitHub Desktop
2. 查看更改
3. 填寫 commit message
4. 點擊 "Commit to main"
5. 點擊 "Push origin"
6. Streamlit Cloud 會自動重新部署（約 1-2 分鐘）

### 使用命令行:
```bash
git add .
git commit -m "Update: description of changes"
git push
```

---

## ⚠️ 注意事項

1. **Watchlist 數據**
   - 默認情況下，watchlist.json 不會同步到 GitHub
   - 如果想要跨設備同步 watchlist，從 `.gitignore` 中移除 `watchlist.json`

2. **免費限制**
   - Streamlit Cloud 免費版有以下限制：
     - 1 個私有 app
     - 無限個公開 app
     - 1 GB RAM
     - 1 CPU
   - 對於這個 app 完全足夠！

3. **隱私**
   - 如果不想公開您的代碼，可以設置 repository 為 private
   - App 仍然可以正常運行

---

## 🆘 常見問題

**Q: 部署失敗怎麼辦？**
A: 檢查 Streamlit Cloud 的錯誤日誌，通常是缺少依賴或文件路徑問題。

**Q: App 很慢怎麼辦？**
A: 免費版資源有限，可以考慮：
- 優化代碼
- 減少數據請求
- 升級到付費版（$20/月）

**Q: 可以自定義域名嗎？**
A: 付費版可以使用自定義域名。

**Q: 數據安全嗎？**
A: 所有連接都是 HTTPS 加密的，但免費版不保證數據持久化。

---

## 📞 需要幫助？

如果遇到問題，可以：
1. 查看 [Streamlit 文檔](https://docs.streamlit.io)
2. 訪問 [Streamlit 社區論壇](https://discuss.streamlit.io)
3. 查看 GitHub Issues

---

**恭喜！您現在有一個免費的股票分析 app，可以在任何設備上使用！** 🎉
