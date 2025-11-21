# API Keys Configuration Guide

## 🔑 如何獲取免費 API Keys

### 1. Finnhub API Key (推薦)

**免費額度**: 60 calls/minute

**註冊步驟**:
1. 前往 https://finnhub.io/register
2. 使用 Email 註冊（免費）
3. 登入後，在 Dashboard 找到您的 API Key
4. 複製 API Key

**功能**:
- 公司新聞
- 市場情緒分析
- 分析師建議
- 同業列表（自動獲取）
- 財報日期

---

### 2. Alpha Vantage API Key (可選)

**免費額度**: 25 calls/day

**註冊步驟**:
1. 前往 https://www.alphavantage.co/support/#api-key
2. 填寫表單（免費）
3. 立即收到 API Key（發送到 Email）

**功能**:
- 技術指標（RSI, MACD, SMA, EMA）
- 更詳細的歷史數據

---

## 🔧 如何配置 API Keys

### 方法 1: 使用 Streamlit Secrets (推薦，用於部署)

1. 在 Streamlit Cloud 上：
   - 進入您的 app 設置
   - 點擊 "Secrets"
   - 添加以下內容：

```toml
FINNHUB_API_KEY = "your_finnhub_key_here"
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key_here"
```

2. 本地測試時：
   - 在項目根目錄創建 `.streamlit/secrets.toml`
   - 添加相同內容

---

### 方法 2: 使用環境變量（本地開發）

**Mac/Linux**:
```bash
export FINNHUB_API_KEY="your_key_here"
export ALPHA_VANTAGE_API_KEY="your_key_here"
```

**Windows**:
```cmd
set FINNHUB_API_KEY=your_key_here
set ALPHA_VANTAGE_API_KEY=your_key_here
```

---

## ⚠️ 重要提示

1. **不要將 API Keys 提交到 Git**
   - `.streamlit/secrets.toml` 已在 `.gitignore` 中
   - 永遠不要在代碼中硬編碼 API Keys

2. **免費額度限制**
   - Finnhub: 60 calls/minute（足夠使用）
   - Alpha Vantage: 25 calls/day（謹慎使用）

3. **可選配置**
   - 即使沒有 API Keys，app 仍可正常運行
   - 只是會缺少新聞、情緒分析等額外功能

---

## ✅ 驗證配置

運行 app 後，在側邊欄會顯示 API 狀態：
- ✅ 綠色 = API 已配置
- ❌ 紅色 = API 未配置

---

## 🎯 推薦配置

**最低配置**（免費）:
- ✅ Finnhub API Key

**完整配置**（免費）:
- ✅ Finnhub API Key
- ✅ Alpha Vantage API Key

這樣您就可以使用所有功能了！
