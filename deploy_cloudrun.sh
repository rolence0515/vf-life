#!/bin/bash

# ====================
# CPU 和記憶體配置
# ====================
CPU=2
MEMORY="1024Mi"

# ====================
# 變數區 (請根據需求修改)
# ====================
# 環境變數檔案名稱 (根據環境設定 .env.uat 或 .env.prod)
ENV_FILE_PREFIX=".env"

# Google Cloud 專案 ID
PROJECT_ID="rolence-project"

# Cloud Run 部署區域
REGION="asia-east2"

# VPC 連接器名稱 (可選，預設為空)
VPC_CONNECTOR=""

# VPC Egress 設定 (可選，預設為空)
VPC_EGRESS=""

# UAT 和 PROD 環境的服務名稱與最大實例數
UAT_SERVICE_NAME="vf-life-uat"
UAT_MAX_INSTANCES=4
PROD_SERVICE_NAME="vf-life-prod"
PROD_MAX_INSTANCES=10

# ====================
# Cloud SQL 實例連線名稱（方便未來修改）
# ====================
CLOUDSQL_INSTANCE="rolence-project:asia-east2:vf-life-uat-db"
echo "🔍 CLOUDSQL_INSTANCE = $CLOUDSQL_INSTANCE"

# 檢查是否提供了環境參數
if [ -z "$1" ]; then
    echo "❌ 請提供環境參數：uat 或 prod"
    exit 1
fi

# 設定變數
ENVIRONMENT=$1
ENV_FILE="$ENV_FILE_PREFIX.$ENVIRONMENT"

# 檢查環境變數文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 找不到環境變數文件: $ENV_FILE"
    exit 1
fi

# 載入環境變數
set -o allexport
source $ENV_FILE
set +o allexport

# 設定 Cloud Run 服務名稱與最大實例數
if [ "$ENVIRONMENT" == "uat" ]; then
    SERVICE_NAME="$UAT_SERVICE_NAME"
    MAX_INSTANCES=$UAT_MAX_INSTANCES
elif [ "$ENVIRONMENT" == "prod" ]; then
    SERVICE_NAME="$PROD_SERVICE_NAME"
    MAX_INSTANCES=$PROD_MAX_INSTANCES
else
    echo "❌ 無效的環境參數：$ENVIRONMENT。請使用 uat 或 prod。"
    exit 1
fi

IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ====================
# 建置 Docker 映像
# ====================
echo "🚀 開始建置 Docker 映像並推送到 Container Registry..."
gcloud builds submit --tag $IMAGE

# 檢查 build 是否成功
if [ $? -ne 0 ]; then
    echo "❌ Cloud Build 失敗，請檢查錯誤訊息。"
    exit 1
fi

# 確認映像已推送到 GCR
echo "🔍 確認映像已推送到 Google Container Registry..."
gcloud container images list --project=$PROJECT_ID

# ====================
# 部署到 Cloud Run
# ====================
echo "🚀 開始部署到 Cloud Run..."

# 將 .env 文件轉換為 --set-env-vars 格式
ENV_VARS=$(awk -F= '!/^\s*#/ && NF==2 {printf "%s=%s,", $1, $2}' "$ENV_FILE" | sed 's/,$//')

DEPLOY_COMMAND="gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE \
    --add-cloudsql-instances=$CLOUDSQL_INSTANCE \
    --region=$REGION \
    --max-instances=$MAX_INSTANCES \
    --cpu=$CPU \
    --memory=$MEMORY \
    --allow-unauthenticated \
    --set-env-vars=$ENV_VARS"

# 如果 VPC_CONNECTOR 和 VPC_EGRESS 有設定，則加入指令
if [ -n "$VPC_CONNECTOR" ]; then
    DEPLOY_COMMAND+=" \\
    --vpc-connector=$VPC_CONNECTOR"
fi
if [ -n "$VPC_EGRESS" ]; then
    DEPLOY_COMMAND+=" \\
    --vpc-egress=$VPC_EGRESS"
fi

# 執行部署指令
eval $DEPLOY_COMMAND

# 檢查部署是否成功
if [ $? -ne 0 ]; then
    echo "❌ Cloud Run 部署失敗，請檢查錯誤訊息。"
    exit 1
fi