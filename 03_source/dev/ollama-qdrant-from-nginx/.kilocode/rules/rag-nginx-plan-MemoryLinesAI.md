# Настройка Nginx Reverse Proxy для Ollama и Qdrant (Docker Compose)

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

# Список моделей LLM
Адресс ollama:
    http://localhost:11434/

Пример запроса к ollam в docker через терминал:
    docker exec ollama ollama list

Используемая модель:
    qwen3-embedding:0.6b-q8_0           ac6da0dfba84    639 MB

Список моделей для тестирования:
    NAME                                ID              SIZE      MODIFIED
        qwen3-embedding:0.6b-fp16           67a7592a8852    1.2 GB    3 weeks ago
        qwen3-embedding:0.6b-q8_0           ac6da0dfba84    639 MB    3 weeks ago
        all-minilm:22m-l6-v2-fp16           1b226e2802db    45 MB     3 weeks ago
        bge-m3:567m-fp16                    790764642607    1.2 GB    3 weeks ago
        nomic-embed-text:137m-v1.5-fp16     0a109f422b47    274 MB    3 weeks ago
        qllama/multilingual-e5-small:f16    3c8dead9831d    241 MB    3 weeks ago
        all-minilm:l6-v2                    1b226e2802db    45 MB     4 weeks ago
