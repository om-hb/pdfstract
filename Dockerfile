FROM node:20-bullseye AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim-bullseye
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgl1 \
      poppler-utils \
      tesseract-ocr \
      build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip uv
COPY scripts /app/scripts

COPY pyproject.toml uv.lock* /app/
RUN uv sync
# RUN bash scripts/setup-mineru.sh

COPY services /app/services
COPY main.py /app/
COPY templates /app/templates

# Copy built frontend from builder stage (vite outputs to ../static relative to /app/frontend)
COPY --from=frontend-builder /app/static /app/static

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 