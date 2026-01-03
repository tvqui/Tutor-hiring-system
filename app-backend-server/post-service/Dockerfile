FROM python:3.10-slim

WORKDIR /usr/src/app

COPY post-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared

COPY post-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8083"]