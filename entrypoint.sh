#!/bin/sh

# 데이터베이스 마이그레이션 적용
echo "Applying database migrations..."
python manage.py migrate --noinput

# 정적 파일 모으기
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 인자로 받은 명령어 실행 (예: daphne 서버)
echo "Executing CMD..."
exec "$@"
