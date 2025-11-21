# 🔧 本地 API 配置快速指南

## 📍 當前狀態
您的應用顯示 "API not configured" 是正常的，因為還沒有設置 API Keys。

## ✅ 快速配置步驟

### 1️⃣ 獲取免費 API Keys

#### Finnhub API (推薦 - 用於新聞和分析師建議)
1. 訪問: https://finnhub.io/register
2. 使用 Email 註冊（完全免費）
3. 登入後在 Dashboard 複製您的 API Key
4. 免費額度: **60 calls/minute** ✅

#### Alpha Vantage API (可選 - 用於技術指標)
1. 訪問: https://www.alphavantage.co/support/#api-key
2. 填寫表單（完全免費）
3. API Key 會立即發送到您的 Email
4. 免費額度: **25 calls/day** ⚠️

---

### 2️⃣ 配置 API Keys

打開文件: `.streamlit/secrets.toml`

將以下內容中的 `your_xxx_api_key_here` 替換為您的實際 API Key：

```toml
FINNHUB_API_KEY = "paste_your_finnhub_key_here"
ALPHA_VANTAGE_API_KEY = "paste_your_alpha_vantage_key_here"
```

**示例:**
```toml
FINNHUB_API_KEY = "abc123def456ghi789"
ALPHA_VANTAGE_API_KEY = "XYZ789ABC123"
```

---

### 3️⃣ 重新啟動應用

```bash
streamlit run app.py
```

側邊欄會顯示：
- ✅ **Finnhub API: Active** (綠色)
- ✅ **Alpha Vantage API: Active** (綠色)

---

## 🎯 功能對照表

| 功能 | 需要的 API | 是否必需 |
|------|-----------|---------|
| 股票分析 | 無 | ✅ 核心功能 |
| 估值模型 | 無 | ✅ 核心功能 |
| 同業比較 | Finnhub (可選) | ⚠️ 有 API 更好 |
| 新聞與情緒 | Finnhub | ❌ 需要 API |
| 分析師建議趨勢 | Finnhub | ❌ 需要 API |
| 技術指標 | Alpha Vantage | ❌ 需要 API |

---

## 🚀 Streamlit Cloud 部署配置

部署到 Streamlit Cloud 時：

1. 進入您的 app 設置
2. 點擊 **"Secrets"**
3. 添加相同的內容：

```toml
FINNHUB_API_KEY = "your_actual_key"
ALPHA_VANTAGE_API_KEY = "your_actual_key"
```

4. 保存並重新部署

---

## ⚠️ 安全提醒

- ✅ `.streamlit/secrets.toml` 已在 `.gitignore` 中
- ✅ 不會被提交到 Git
- ❌ 永遠不要在代碼中硬編碼 API Keys
- ❌ 不要分享您的 API Keys

---

## 💡 提示

**沒有 API Keys 也能用！**
- 應用的核心功能（估值、圖表、財務數據）不需要 API
- API 只是提供額外的新聞和情緒分析功能
- 您可以先使用核心功能，之後再添加 API Keys

**推薦配置:**
- 最低: 只配置 Finnhub (免費且額度充足)
- 完整: Finnhub + Alpha Vantage (兩個都免費)
