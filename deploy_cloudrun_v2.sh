#!/bin/bash

# ====================
# CPU 和記憶體配置
# ====================
CPU=2
MEMORY="1024Mi"

# ====================
# 變數區 (請根據需求修改)
# ====================
ENV_FILE_PREFIX=".env"
PROJECT_ID="ardent-strength-459016-s3"
REGION="asia-east2"
ARTIFACT_REGION="asia-east1"  # Artifact Registry 區域
ARTIFACT_REPO="web-deploy"    # Artifact Registry 倉庫名稱

UAT_SERVICE_NAME="vf-life-uat"
UAT_MAX_INSTANCES=4
PROD_SERVICE_NAME="vf-life-prod"
PROD_MAX_INSTANCES=10

CLOUDSQL_INSTANCE="ardent-strength-459016-s3:asia-east2:vf-life-uat-db"
echo "🔍 CLOUDSQL_INSTANCE = $CLOUDSQL_INSTANCE"

if [ -z "$1" ]; then
    echo "❌ 請提供環境參數：uat 或 prod"
    exit 1
fi

ENVIRONMENT=$1
ENV_FILE="$ENV_FILE_PREFIX.$ENVIRONMENT"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 找不到環境變數文件: $ENV_FILE"
    exit 1
fi

set -o allexport
source $ENV_FILE
set +o allexport

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

# 允許自訂映像名稱與 tag
IMAGE_NAME=${2:-$SERVICE_NAME}
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE_TAG=${3:-$GIT_HASH}

IMAGE_URI="$ARTIFACT_REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$IMAGE_NAME:$IMAGE_TAG"
echo "🔍 IMAGE_URI = $IMAGE_URI"

echo "🚀 開始建置 Docker 映像..."
docker build -t $IMAGE_URI .
if [ $? -ne 0 ]; then
    echo "❌ Docker build 失敗，請檢查錯誤訊息。"
    exit 1
fi

echo "🚀 登入 Artifact Registry..."
gcloud auth configure-docker $ARTIFACT_REGION-docker.pkg.dev
if [ $? -ne 0 ]; then
    echo "❌ Artifact Registry 登入失敗。"
    exit 1
fi

echo "🚀 推送映像到 Artifact Registry..."
docker push $IMAGE_URI
if [ $? -ne 0 ]; then
    echo "❌ Docker push 失敗，請檢查錯誤訊息。"
    exit 1
fi

echo "🚀 開始部署到 Cloud Run..."
ENV_VARS=$(awk -F= '!/^\s*#/ && NF==2 {printf "%s=%s,", $1, $2}' "$ENV_FILE" | sed 's/,$//')

gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_URI \
    --add-cloudsql-instances=$CLOUDSQL_INSTANCE \
    --region=$REGION \
    --max-instances=$MAX_INSTANCES \
    --cpu=$CPU \
    --memory=$MEMORY \
    --allow-unauthenticated \
    --set-env-vars=$ENV_VARS

if [ $? -ne 0 ]; then
    echo "❌ Cloud Run 部署失敗，請檢查錯誤訊息。"
    exit 1
fi

echo "✅ 部署完成！"
