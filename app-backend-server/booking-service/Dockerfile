FROM python:3.10-slim

WORKDIR /usr/src/app

COPY booking-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared

COPY booking-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]