FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các gói phụ trợ cơ bản
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn dự án vào container
COPY . /app/

# Mở cổng cho các dịch vụ SOA
EXPOSE 8001 8002 8003

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]

