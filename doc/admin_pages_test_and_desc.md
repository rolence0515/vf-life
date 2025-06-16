# 管理後台 admin 頁面測試文件（簡明版）

## 1. admin_user.html
### 測試項目
- [ ] 搜尋功能可依 Email/姓名/管理員篩選
- [ ] 管理員切換（設為/取消管理員）
- [ ] 重設密碼按鈕功能
- [ ] 進入「瀏覽影片」連結正確
- [ ] 分頁功能正常

## 2. admin_series.html
### 測試項目
- [ ] 新增系列（modal 彈窗）
- [ ] 編輯系列（modal 彈窗）
- [ ] 刪除系列
- [ ] 系列列表顯示正確

## 3. admin_videos.html
### 測試項目
- [ ] 新增影片（modal 彈窗）
- [ ] 編輯影片（modal 彈窗）
- [ ] 刪除影片
- [ ] 影片列表顯示正確
- [ ] 系列下拉選單正確

## 4. admin_user_videos.html
### 測試項目
- [ ] 新增影片給使用者（modal 彈窗）
- [ ] 移除使用者影片
- [ ] 影片列表顯示正確
- [ ] 系列與影片下拉選單正確

## 5. admin_bulk_create_accounts.html
### 測試項目
- [ ] 備份確認 checkbox
- [ ] 上傳 CSV 驗證（dry run）
- [ ] 上傳 CSV 執行批量開帳號
- [ ] 結果下載連結

## 6. admin_batch_account_log.html
### 測試項目
- [ ] 批量開帳號記錄列表顯示
- [ ] 下載結果檔案連結

---

# 管理後台 admin 頁面功能說明

## 1. admin_user.html
- 顯示所有使用者列表，可搜尋、分頁
- 可切換管理員身份、重設密碼
- 可進入該使用者的影片管理頁

## 2. admin_series.html
- 管理影片系列（新增、編輯、刪除）
- 以表格方式顯示所有系列

## 3. admin_videos.html
- 管理所有影片（新增、編輯、刪除）
- 影片需指定所屬系列
- 可設定上架/下架日、影片網址

## 4. admin_user_videos.html
- 管理單一使用者的影片權限
- 可新增/移除該用戶可觀看的影片

## 5. admin_bulk_create_accounts.html
- 批量建立帳號（上傳 CSV）
- 支援檔案驗證（dry run）與正式執行
- 顯示結果下載連結

## 6. admin_batch_account_log.html
- 顯示批量開帳號操作記錄
- 可下載每次操作的結果檔案
