# Xiaomi Coupon Bot

這個專案提供一個使用 [Playwright](https://playwright.dev/python/) 自動搶小米優惠券的範例程式。

## 安裝環境

1. 建議使用 Python 3.10 以上版本。
2. 安裝依賴：

   ```bash
   pip install playwright
   playwright install chromium
   ```

## 使用方式

1. 先到小米商城登入並取得已登入的 cookies，將其匯出成 JSON 格式存成 `cookies.json`（或任意檔名）。
2. 依照活動內容設定一份設定檔，可以複製 `config.example.json` 後修改：

   ```json
   {
     "url": "https://m.mi.com/page/some-coupon-event",
     "click_selectors": ["text=立即领取", "css=.coupon-btn"],
     "success_selectors": ["text=领取成功", "css=.coupon-success"],
     "start_time": "2024-05-01T16:00:00+08:00",
     "max_attempts": 300,
     "pause_between_attempts": 0.03,
     "wait_selector": "css=.coupon-container",
     "cookies_path": "cookies.json",
     "headless": false,
     "timeout": 15000
   }
   ```

   * `url`：優惠券活動頁面。
   * `click_selectors`：會依序嘗試點擊的按鈕選擇器，可以是 Playwright 支援的 `css=`、`text=`…等語法。
   * `success_selectors`：代表成功領券的提示元素，只要其中之一出現就視為成功。
   * `start_time`：活動開始時間（ISO 8601 格式），程式會在時間到時才開始連續點擊。
   * `max_attempts` / `pause_between_attempts`：最多嘗試次數與每次嘗試間隔秒數。
   * `wait_selector`：進入頁面後會等待出現的元素，避免頁面尚未載入完成。
   * `cookies_path`：cookies 檔案路徑。
   * `headless`：是否使用 headless 模式。
   * `timeout`：頁面載入與操作等待的逾時毫秒數。

3. 執行程式：

   ```bash
   python xiaomi_coupon_bot.py my-config.json --log-level DEBUG
   ```

   程式會在達到 `start_time` 後連續點擊 `click_selectors` 中的按鈕，偵測到任一 `success_selectors` 即停止。

> ⚠️ **注意**：請遵守小米商城的使用條款與各項活動規則，過度頻繁的請求可能導致帳號被限制。
