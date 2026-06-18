FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /frontend

COPY vue/package*.json ./
RUN npm install

COPY vue/ ./
RUN npm run build


FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

COPY backend/requirements_utf8.txt /app/backend/requirements_utf8.txt
RUN pip install --no-cache-dir -r /app/backend/requirements_utf8.txt

COPY backend/ /app/backend/
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /app/backend/logs /var/log/supervisor

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
