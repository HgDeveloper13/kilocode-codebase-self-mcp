# RAG Workflows — Memory Notes AI

[CONTEXT]

Проект RAG использует стек: .NET 8 Gateway + Redis + Nginx + Ollama + Qdrant. В процессе работы реализованы механизмы кэширования и ожидания кэша для оптимизации повторных запросов.

[INSTRUCTION]

При работе над проектом RAG использовать данные workflows для быстрой верной разработки, быстрой диагностики и исправления.

---

## 🔧 Tech Detail

### Основные компоненты

| Компонент | Порт | Описание |
|-----------|------|----------|
| Nginx | 11434 | Единая точка входа, проксирует на Gateway и Ollama |
| Gateway | 11435 | .NET 8 ASP.NET, кэширует в Redis |
| Ollama | 11434 (внутри) | Генерирует embeddings |
| Redis | 6379 | Кэш с TTL 7 дней |
| Qdrant | 6333 | Векторная БД |

### Ключевые endpoints

- `POST /api/embed` — нативный Ollama API
- `POST /v1/embeddings` — OpenAI-совместимый API
- `GET /health` — health check Gateway

### Механизм кэширования

| Параметр | Значение |
|----------|----------|
| Тип | SHA256 хеш от model + input/prompt |
| Формат ключа | `emb:{hash}` |
| TTL | 7 дней (604800 секунд) |
| Хранилище | Redis |

### Механизм ожидания кэша (Cache Wait)

| Параметр | Значение |
|----------|----------|
| In-progress ключ | `in-progress:emb:{hash}` |
| In-progress TTL | 5 минут (300 сек) |
| Poll interval | 2 секунды |
| Max wait time | 5 минут (300 сек) |
| Таймаут клиента | Код 499 (Client closed) |
| Таймаут ожидания | Код 504 (Gateway Timeout) |

---

## 🎯 FAQ

### Как проверить что Gateway работает?

```bash
curl -X GET http://localhost:11435/health
```

### Как проверить Ollama напрямую?

```bash
# Отключить Gateway в nginx.conf
# Перенаправить /api/embed на Ollama напрямую
curl -X POST http://localhost:11434/api/embed -d '{"model": "qwen3-embedding:0.6b-q8_0", "input": "test"}'
```

### Как проверить Gateway с поддержкой OpenAI API?

```bash
curl -X POST http://localhost:11434/v1/embeddings -d '{"model": "qwen3-embedding:0.6b-q8_0", "input": "test"}'
```

### Как посмотреть логи контейнеров?

```bash
docker logs embedding-gateway --tail 30
docker logs ollama --tail 30
docker logs redis-cache --tail 30
docker logs nginx-proxy --tail 30
```

### Как пересобрать Gateway после изменений?

```bash
cd qdrant-ollama-docker-cfg/pr-core-train-to-ollama-qdrant
docker compose build gateway
docker compose up -d --force-recreate nginx gateway
```

### Как работает кэширование в Gateway?
Кэш формируется из SHA256 хеша всего тела запроса (модель + input/prompt). Ключ имеет формат `emb:{hex_hash}`. При повторном запросе с тем же телом - возвращается кэшированный результат без обращения к Ollama.

### Как работает механизм ожидания кэша?
1. При запросе: проверить Redis кэш по (model + hash prompt)
2. Если есть в кэше → вернуть сразу
3. Если нет в кэше:
   - Проверить in-progress flag (`in-progress:emb:{hash}`)
   - Если flag установлен → ждать (poll до 5 минут) пока кэш заполнится
   - Если flag не установлен → отправить запрос в Ollama и записать в кэш

### Как проверить in-progress ключи в Redis?

```bash
docker exec -it redis-cache redis-cli
> KEYS in-progress:*
> TTL <key>
```

### Что происходит при отмене клиентом запроса?
При отмене запроса (клиент закрыл соединение) Gateway:
- Проверяет `context.RequestAborted.IsCancellationRequested`
- Возвращает статус 499 (Client closed request)
- Не удаляет in-progress flag (его TTL сам очистит через 5 минут)

### Как проверить кэш Redis?

```bash
docker exec -it redis-cache redis-cli
> KEYS emb:*
> TTL <key>
```

---

## 🧠 Workflow Examples

### Workflow: Диагностика Gateway при ошибках эмбедингов

| Шаг | Действие | Команда/Проверка |
|-----|----------|------------------|
| 1 | Проверить статус контейнеров | `docker ps -a` |
| 2 | Проверить логи Gateway | `docker logs embedding-gateway --tail 50` |
| 3 | Проверить логи Ollama | `docker logs ollama --tail 30` |
| 4 | Определить тип ошибки | Искать "Invalid request URI" — проблема в IHttpClientFactory |
| 5 | Проверить формат запроса | Если клиент использует `/v1/embeddings` — нужна конвертация |

### Workflow: Исправление IHttpClientFactory в .NET 8 Gateway

| Шаг | Действие | Изменение |
|-----|----------|-----------|
| 1 | Изменить регистрацию HttpClient | `builder.Services.AddHttpClient()` вместо `AddHttpClient("Ollama")` |
| 2 | Изменить внедрение в endpoint | `IHttpClientFactory httpClientFactory` вместо `HttpClient ollamaClient` |
| 3 | Создать HttpClient в endpoint | `var ollamaClient = httpClientFactory.CreateClient()` |
| 4 | Установить BaseAddress | `ollamaClient.BaseAddress = new Uri(ollamaUrl)` |
| 5 | Пересобрать контейнер | `docker compose build gateway` |

### Workflow: Добавление поддержки OpenAI-совместимого API

| Шаг | Действие | Код |
|-----|----------|-----|
| 1 | Добавить новый endpoint | `app.MapPost("/v1/embeddings", ...)` |
| 2 | Конвертировать запрос | Из `{"input": "..."}` в `{"input": "..."}` для Ollama |
| 3 | Конвертировать ответ | Из нативного формата в OpenAI формат |
| 4 | Сохранить в кэш | Redis с SHA256 ключом, TTL 7 дней |
| 5 | Пересобрать и протестировать | curl с замером времени |

### Workflow: Обновление nginx.conf для проксирования /v1/embeddings

| Шаг | Действие | Конфиг |
|-----|----------|--------|
| 1 | Добавить location | `location /v1/embeddings { proxy_pass http://gateway_backend; ... }` |
| 2 | Добавить заголовки | Host, X-Real-IP, X-Forwarded-For |
| 3 | Установить таймауты | proxy_read_timeout 300s |
| 4 | Перезапустить nginx | `docker compose up -d nginx` |

### Workflow: Тестирование Gateway после исправлений

| Шаг | Действие | Ожидаемый результат |
|-----|----------|---------------------|
| 1 | Первый запрос (cold start) | ~8 сек, статус 200 |
| 2 | Второй запрос (кэш) | ~0.04 сек, статус 200 |
| 3 | Проверить формат ответа | `{"object":"embedding","data":[...]}` |
| 4 | Проверить логи | Нет ошибок "Invalid request URI" |

### Workflow: Анализ логов контейнеров после индексации

| Контейнер | Проверить | Команда |
|-----------|-----------|---------|
| Ollama | Все POST /api/embed вернули 200 | `docker logs ollama --tail 30` |
| Redis | Ключи созданы, TTL установлен | `docker exec redis-cache redis-cli KEYS emb:*` |
| Gateway | Время отклика, статус 200 | `docker logs embedding-gateway --tail 30` |
| Nginx | Проксирование работает | `docker logs nginx-proxy --tail 30` |
| Qdrant | Данные сохранены | `docker logs qdrant --tail 30` |

### Workflow: Проверка кэша Redis

| Шаг | Действие | Команда/Проверка |
|-----|----------|------------------|
| 1 | Подключиться к Redis | `docker exec -it redis-cache redis-cli` |
| 2 | Посмотреть все ключи | `KEYS emb:*` |
| 3 | Проверить TTL ключа | `TTL <key>` |
| 4 | Получить значение ключа | `GET <key>` |

### Workflow: Реализация механизма ожидания кэша для повторных запросов

| Шаг | Действие | Код/Проверка |
|-----|----------|--------------|
| 1 | Добавить in-progress flag | `await db.StringSetAsync($"in-progress:{cacheKey}", "1", TimeSpan.FromSeconds(300))` |
| 2 | Проверить in-progress при cache miss | `var inProgress = await db.StringGetAsync($"in-progress:{cacheKey}")` |
| 3 | Реализовать poll логику | `await Task.Delay(2000)` в цикле до 5 минут |
| 4 | Добавить проверку отмены клиента | `if (context.RequestAborted.IsCancellationRequested)` |
| 5 | Обработать таймаут | Вернуть 504 при истечении 5 минут |
| 6 | Удалить in-progress flag | `await db.KeyDeleteAsync($"in-progress:{cacheKey}")` в finally блоке |
| 7 | Тестировать | Два параллельных запроса: первый - в Ollama, второй - ждёт кэш |

---

## 📚 How to add new example

Добавить новый workflow:

1. Добавить секцию `### Workflow: Название` в блок 🧠 Workflow Examples
2. Создать таблицу с колонками: Шаг, Действие, Команда/Проверка
3. Пронумеровать шаги последовательно
4. В блоке 🔧 Tech Detail добавить технические детали если требуется
5. В блоке 🎯 FAQ добавить часто задаваемые вопросы если требуется