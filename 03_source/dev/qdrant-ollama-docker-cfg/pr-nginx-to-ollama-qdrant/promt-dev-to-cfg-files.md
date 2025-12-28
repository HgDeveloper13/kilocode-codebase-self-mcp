ollama docker compose:
docker run -d `
  -v ollama:/root/.ollama `
  -p 11434:11434 `
  --name ollama `
  -e OLLAMA_HOST=0.0.0.0 `
  -e OLLAMA_NUM_PARALLEL=1 `
  -e OLLAMA_MAX_LOADED_MODELS=1 `
  -e OLLAMA_GPU_LAYERS=0 `
  -e OLLAMA_NUM_THREADS=4 `
  -e OLLAMA_MAX_QUEUE=1024 `
  -e OLLAMA_KEEP_ALIVE="30m" `
  -e OLLAMA_DEBUG=false `
  ollama/ollama

qdrant docker compose:
services:
  qdrant:
    image: qdrant:v1.16.2
    restart: always
    container_name: qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      # Используем bind mount для удобного доступа к данным
      - ./qdrant_storage:/qdrant/storage
      # Монтируем наши файлы конфигурации
      - ./config.yaml:/qdrant/config/production.yaml
    # Указываем путь к главному конфигу
    command: ./qdrant --config-path /qdrant/config/production.yaml

    environment:
      - QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage
      # Эти переменные переопределят/дополнят настройки из YAML-файлов
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__ENABLE_CORS=true
      # Путь к данным и снэпшотам задается здесь, это надежный способ
      - QDRANT__STORAGE__SNAPSHOTS_PATH=/qdrant/snapshots

      - QDRANT__TELEMETRY_DISABLED=true

volumes:
  qdrant_storage:

Какой Nginx теперь будет?

Цель:
localhost:11434 → nginx → ollama (внутри контейнера)
localhost:6333 → nginx → qdrant (внутри контейнера)
Все три сервиса — в одном docker-compose.yml,
ollama и qdrant не публикуют порты напрямую (ports: только у nginx),
клиенты ничего не замечают — работают как раньше.

локальный Docker Desktop (Windows 11 + WSL2),
→ в одном docker-compose.yml поднимаются:
✅ Ollama
✅ Qdrant
✅ nginx
→ nginx работает как reverse-proxy,
→ но внешние клиенты по-прежнему используют стандартные адреса:
 • http://localhost:11434 — Ollama
 • http://localhost:6333 — Qdrant

То есть:
🔹 nginx внутри контейнера,
🔹 проксирует на уровне HTTP (не TCP),
🔹 сохраняя оригинальные порты снаружи,
🔹 и не требуя переделки чужих клиентов.

прошлая, версия без улучшений, как пример:
docker-compose.yml (локальный, Docker Desktop, Windows + WSL2)

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    # ❗ ports НЕ указываем — только внутри сети
    volumes:
      - ollama_/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - internal
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:v1.16.1  # твоя версия — сохраняем
    container_name: qdrant
    # ❗ ports НЕ указываем — только внутри сети
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - internal
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "11434:11434"   # ← внешний порт = внутренний (как у Ollama)
      - "6333:6333"     # ← внешний порт = внутренний (как у Qdrant)
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - ollama
      - qdrant
    networks:
      - internal
    restart: unless-stopped

volumes:
  ollama_
  qdrant_storage:

networks:
  internal:
    driver: bridge

nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    # Запрещаем логи в локальной разработке (меньше шума)
    access_log off;
    error_log /dev/stderr warn;

    upstream ollama_backend {
        server ollama:11434;
    }

    upstream qdrant_backend {
        server qdrant:6333;
    }

    # === Ollama API (на :11434) ===
    server {
        listen 11434;
        server_name localhost;

        location / {
            proxy_pass http://ollama_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Обязательно для streaming (api/generate, api/chat)
            proxy_http_version 1.1;
            proxy_set_header Connection '';
            proxy_cache_bypass $http_upgrade;
            proxy_buffering off;
            proxy_request_buffering off;
        }
    }

    # === Qdrant API (на :6333) ===
    server {
        listen 6333;
        server_name localhost;

        location / {
            proxy_pass http://qdrant_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Qdrant работает поверх HTTP/JSON — буферинг можно оставить
            proxy_buffering on;
        }

        # Qdrant Dashboard (если нужен)
        location /dashboard/ {
            proxy_pass http://qdrant_backend/dashboard/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}

✅ Проверка после запуска:
cd ~/qdrant-ollama-nginx
docker compose up -d

Тест:
# Проверяем Ollama
curl http://localhost:11434
# → "Ollama is running"

curl http://localhost:11434/api/tags
# → список моделей (должен быть пуст, пока не загрузишь)

# Проверяем Qdrant
curl http://localhost:6333
# → {"title":"qdrant - vector search engine","version":"1.16.1",...}

curl http://localhost:6333/dashboard
# → перенаправит в UI (если браузер)