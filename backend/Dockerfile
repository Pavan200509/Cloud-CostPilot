
# Stage 1: Build React frontend
FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# Stage 2: Build FastAPI backend
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements-gcp.txt ./

RUN pip install --no-cache-dir -r requirements.txt -r requirements-gcp.txt

COPY backend/app ./app

# Replace old static UI with the production React build
RUN rm -rf /app/app/static

COPY --from=frontend-build /frontend/dist ./app/static

ENV DATA_DIR=/app/data
ENV DISCOVERY_MODE=live
ENV AI_PROVIDER=gemini
ENV STORAGE_BACKEND=local

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
