#!/bin/sh

# 等待數據庫準備就緒
echo "Waiting for postgres..."

while ! nc -z db 5432; do
    sleep 0.1
done

echo "PostgreSQL started"

# 執行遷移
python manage.py migrate

# 啟動服務器
exec "$@"