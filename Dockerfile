# 使用 Python 3.9 作為基礎鏡像
FROM python:3.9

# 設置工作目錄
WORKDIR /app

# 設置環境變量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \  # 添加 netcat 用於檢查數據庫連接
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案文件
COPY . .

# 複製並設置啟動腳本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 設置啟動命令
ENTRYPOINT ["/app/entrypoint.sh"]