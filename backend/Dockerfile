FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-gcp.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-gcp.txt
COPY app ./app
ENV DATA_DIR=/app/data
ENV DISCOVERY_MODE=live
ENV AI_PROVIDER=gemini
ENV STORAGE_BACKEND=local
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]