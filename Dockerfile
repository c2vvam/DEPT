FROM python:3.11-slim-bookworm

# 파이썬 출력을 버퍼링 없이 즉시 출력하도록 설정
ENV PYTHONUNBUFFERED=1
# pyc 파일 생성 방지
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 종속성 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . /app/

# entrypoint.sh 스크립트 실행 권한 부여
RUN chmod +x /app/entrypoint.sh

# non-root 사용자 생성 및 소유권 변경
RUN useradd -u 8888 django_user && chown -R django_user:django_user /app

# non-root 사용자로 실행
USER django_user

ENTRYPOINT ["/app/entrypoint.sh"]



