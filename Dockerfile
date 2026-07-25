FROM node:22-alpine AS web-builder

WORKDIR /build
RUN corepack enable && corepack prepare pnpm@11.0.8 --activate
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./
RUN pnpm build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AICOWORK_HOST=0.0.0.0 \
    AICOWORK_PORT=8787 \
    AICOWORK_WEB_DIST=/app/apps/web/dist

WORKDIR /app

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/ ./apps/
COPY workflows/ ./workflows/
COPY configs/ ./configs/
COPY data/ ./data/
COPY --from=web-builder /build/dist ./apps/web/dist/

EXPOSE 8787

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8787"]
