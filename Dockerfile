# ---------- 阶段 1：构建前端 ----------
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 阶段 2：运行时 ----------
FROM python:3.11-slim
WORKDIR /app

# 时区（可选，让"今天"按本地时间计算）
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /build/dist ./static/

RUN mkdir -p /data

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
