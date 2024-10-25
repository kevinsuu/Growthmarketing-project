# 使用官方 Python 執行環境作為基礎鏡像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安裝系統依賴
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        python3-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露埠號
EXPOSE 8000

# 執行命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]