# Sử dụng Python 3.11 slim
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /usr/src/app

COPY email-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8086

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8086", "--reload"]
