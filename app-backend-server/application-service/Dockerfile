FROM python:3.10-slim

WORKDIR /usr/src/app

COPY application-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared

COPY application-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]