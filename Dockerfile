# --- Stage 1: Build Resident Frontend ---
FROM node:20-alpine AS builder-resident
WORKDIR /frontend-resident
COPY frontend-resident/package*.json ./
RUN npm install
COPY frontend-resident/ ./
RUN npm run build

# --- Stage 2: Build Official Frontend ---
FROM node:20-alpine AS builder-official
WORKDIR /frontend-official
COPY frontend-official/package*.json ./
RUN npm install
COPY frontend-official/ ./
RUN npm run build

# --- Stage 3: Serve Backend + Static Assets ---
FROM python:3.12-slim
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app code
COPY backend/app ./backend/app

# Copy mock credentials for simple verification
COPY backend/floodguard-sa-key.json ./backend/floodguard-sa-key.json
COPY backend/.env ./backend/.env

# Copy built frontend assets matching main.py resolution paths
COPY --from=builder-resident /frontend-resident/dist ./frontend-resident/dist
COPY --from=builder-official /frontend-official/dist ./frontend-official/dist

# Set production environment configurations
ENV PORT=8080
ENV PYTHONPATH=/workspace/backend
ENV GOOGLE_APPLICATION_CREDENTIALS=/workspace/backend/floodguard-sa-key.json

WORKDIR /workspace/backend
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
