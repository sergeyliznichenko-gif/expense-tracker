FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DB_PATH=/data/data.db
EXPOSE 8000
CMD ["waitress-serve", "--listen=0.0.0.0:8000", "app:app"]
