# 使用 Python 3.11 作為基底映像
FROM python:3.11

# Cloud SQL socket 是被 mount 到 /cloudsql 路徑的，但這個資料夾要 你自己在 Dockerfile 裡建出來
RUN mkdir -p /cloudsql

# 安裝必要的工具
RUN apt-get update && apt-get install -y \
    openvpn \
    net-tools && \
    apt-get clean

# 設定工作目錄
WORKDIR /app

# 複製應用程式
COPY . /app

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 啟動應用
CMD gunicorn -b 0.0.0.0:8080 app:app --workers=2 --threads=5 --timeout=120 --worker-class=gthread