#!/bin/bash

# ===== 變數設定區 =====
UAT_INSTANCE="vf-life-uat-db"
UAT_DB="postgres"
UAT_USER="postgres"
UAT_PROJECT="rolence-project"

PROD_INSTANCE="vf-life-prod-db"
PROD_DB="postgres"
PROD_USER="postgres"
PROD_PROJECT="rolence-project"

# ===== 參數判斷 =====
if [[ "$1" == "uat" ]]; then
  ENV="uat"
  INSTANCE="$UAT_INSTANCE"
  DB="$UAT_DB"
  USER="$UAT_USER"
  PROJECT="$UAT_PROJECT"
elif [[ "$1" == "prod" ]]; then
  ENV="prod"
  INSTANCE="$PROD_INSTANCE"
  DB="$PROD_DB"
  USER="$PROD_USER"
  PROJECT="$PROD_PROJECT"
else
  echo "請以參數指定環境：uat 或 prod"
  echo "用法：$0 uat|prod"
  exit 1
fi

# ===== 操作選擇 =====
echo "請選擇操作："
select ACTION in "備份" "還原"; do
  case $ACTION in
    "備份") OP="backup"; break;;
    "還原") OP="restore"; break;;
    *) echo "請輸入 1 或 2";;
  esac
done

# ===== 顯示資訊並確認 =====
echo "-----------------------------"
echo "GCP Project: $PROJECT"
echo "環境：$ENV"
echo "Cloud SQL 實例：$INSTANCE"
echo "資料庫名稱：$DB"
echo "操作：$ACTION"
echo "-----------------------------"
read -p "請確認以上資訊正確，繼續請輸入 y：" confirm
if [[ "$confirm" != "y" ]]; then
  echo "已取消"
  exit 1
fi

# ===== 執行備份或還原 =====
if [[ "$OP" == "backup" ]]; then
  echo "開始備份..."
  gcloud sql backups create --instance="$INSTANCE" --project="$PROJECT"
  if [[ $? -eq 0 ]]; then
    echo "✅ 備份成功！"
  else
    echo "❌ 備份失敗，請檢查錯誤訊息"
    exit 1
  fi
elif [[ "$OP" == "restore" ]]; then
  echo "查詢可用備份..."
  gcloud sql backups list --instance="$INSTANCE" --project="$PROJECT"
  read -p "請輸入要還原的 BACKUP_ID：" BACKUP_ID
  echo "開始還原..."
  gcloud sql backups restore "$BACKUP_ID" --restore-instance="$INSTANCE" --project="$PROJECT"
  if [[ $? -eq 0 ]]; then
    echo "✅ 還原成功！"
  else
    echo "❌ 還原失敗，請檢查錯誤訊息"
    exit 1
  fi
fi
