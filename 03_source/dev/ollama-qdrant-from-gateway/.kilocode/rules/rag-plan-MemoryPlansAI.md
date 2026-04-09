# План реализации: ASP.NET Core Gateway с Redis кэшем для Embeddings

- Используем активно при разработки знания/документацию через use context7. К примеру нужна "информация по ollama asp.net .net 8 docs use context7", тогда будет получена актуальная документация по данной теме!
- Основные элементы системы: Nginx, Gateway, Qdrant, Ollama, Redis, ASP.NET 8, .NET 8, Docker Container

## Расположение текущего проекта

> qdrant-ollama-docker-cfg\pr-core-train-to-ollama-qdrant

- Только в данной папке проводим изменения!

## Работаем на стеке

> C# (.NET 8, ASP.NET 8) + Redis (8.6.2-alpine) + Nginx (1.28.1-alpine) + Ollama (0.13.5) + Qdrant (v1.16.2)

## Место Docker, где распологаются контейнеры

> Работаем на локальной ПК! Ни каких VPS! Работаем на windows 11, Docker Desctop 4.47.0 (206054), Среда разработки VS, ИИ ассистент kilocode.ai

## Как работаем с нашим RAG

> ИИ ассистент (kilocode.ai/kilo.ai) с VS обращается по базовым адресам localhost:11434 и localhost:6333

## План разработки - Список задач

> Список задач которые нужно будет решить

- Добавить ASP.NET Core Gateway как кэш-слой для embedding запросов к Ollama. Gateway проверяет Redis кэш перед отправкой запроса в Ollama, что ускоряет повторные запросы.

## Контекст плана разработки

> Информация которую нужно помнить при разработки по данному плану

### Целевая архитектура

**Проверка:** Архитектура ВЕРНА!
- Nginx публикует порты 11434 (Ollama), 6333 (Qdrant REST), 6334 (Qdrant gRPC)
- Gateway работает на порту 11435 внутри сети
- Embedding endpoints (/api/embed, /api/embeddings, /v1/embeddings) → Gateway → Redis → Ollama
- Chat/Generate endpoints → Ollama напрямую (через Nginx)
- Qdrant → Nginx → Qdrant

```
Client → Nginx (:11434, :6333, :6334)
              ├── /api/embed, /api/embeddings, /v1/embeddings → Gateway (:11435) → Redis → Ollama
              ├── /api/chat, /api/generate → Ollama напрямую
              └── Qdrant REST/gRPC → Qdrant напрямую
```

### Стек технологий

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Nginx | 1.28.1-alpine | Reverse proxy, единственная точка входа |
| ASP.NET Core | 8.0 LTS | Gateway с кэш-логикой |
| Redis | 8.6.2-alpine | Кэш для embeddings (TTL 7 дней) |
| Ollama | 0.13.5 | Embedding генерация |
| Qdrant | v1.16.2 | Vector database (без изменений) |

### Структура проекта

```
<путь-до-проекта>/
├── docker-compose.yml          # Основной compose файл
├── gateway/                  # .NET 8 Gateway
│   ├── Dockerfile
│   └── src/EmbeddingGateway/
│       ├── Program.cs        # Реализация Gateway с Redis кэшем
│       └── EmbeddingGateway.csproj
├── nginx/
│   └── nginx.conf         # Nginx конфиг с роутингом
├── ollama/                 # (预留) для модельных файлов
└── qdrant/
    └── config.yaml   # Qdrant конфигурация
```

## Краткая документация по нашему стеку

### В документации Ollama есть два разных API для embeddings

- Нативный Ollama API: /api/embed (требует поля input, а не prompt)
- OpenAI-совместимый API: /v1/embeddings (требует поля input, а не prompt)

### API совместимость

Gateway полностью совместим с Ollama API для embedding endpoints:

#### Нативный Ollama API - Request format (/api/embed)

```json
{
  "model": "nomic-embed-text",
  "input": "Hello world"
}
```

#### Нативный Ollama API - Response format (/api/embed)

```json
{
  "model": "nomic-embed-text",
  "embeddings": [[0.123, -0.456, 0.789, ...]]
}
```

#### OpenAI-совместимый API - Request format (/v1/embeddings)

```json
{
  "model": "nomic-embed-text",
  "input": "Hello world"
}
```

#### OpenAI-совместимый API - Response format (/v1/embeddings)

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.123, -0.456, 0.789, ...],
      "index": 0
    }
  ],
  "model": "nomic-embed-text",
  "usage": {
    "prompt_tokens": 3,
    "total_tokens": 3
  }
}
```

Клиент не замечает разницы между прямым запросом к Ollama и запросом через Gateway.

### Проверка работы сервисов

Внешние клиенты используют стандартные адреса:
- http://localhost:11434 — Ollama
- http://localhost:6333 — Qdrant

#### Проверка Ollama

```bash
# Базовая проверка
curl http://localhost:11434
# → "Ollama is running"

# Список моделей
curl http://localhost:11434/api/tags
# → список моделей

# Проверка через docker exec
docker exec ollama ollama list
```

#### Проверка Qdrant

```bash
# Базовая проверка
curl http://localhost:6333
# → {"title":"qdrant - vector search engine","version":"1.16.1",...}

# Dashboard
curl http://localhost:6333/dashboard
# → перенаправит в UI (если браузер)
```

## Dirts Data

> Еще в файле task.md в блоке подзадачах, есть информация полезная, можно будет из нее инсайты взять для плана разработки данного

- Nginx единственная точка входа внешнего трафика. Другие контейнеры только внутри контейнера могут общаться.
- Gateway только получает трафик тяжелый от nginx (весь трафик на ollama), порт 11434 ollama заберает себе gateway!
- Ollama порт 11435
- Gateway порт 11434, заберает у Ollama
- Порты открыты, нет auth!
- Версии Docker images строго фиксированные, список images приложен ниже!
- Nginx проксирует прямо на qdrant!
- gateway у нас на стеке (.NET 8, ASP.NET 8)!
- gateway у нас смотрит кэш в Redis, если нету кэша, то отправляет его в ollama!
- gateway у нас смотрит по модели + хеш (promt) в кэш
- Gateway использует кэширование по модели + SHA256 хешу всего тела запроса
- Ключ кэша: `emb:{sha256_hex_hash}`
- Пример: `emb:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824`
- TTL: 7 дней
- Кэш хранится в Redis
- У нас получается nginx единственная точка входа. Nginx прямо на qdrant отправляет запросы, пользователь обращается по стандартной схеме к qdrant localhost:6333. gateway > redis. gateway > ollama. nginx > gateway.
- Ollama работает без GPU, все вычисления на CPU
- Ollama: CPU-режим (OLLAMA_GPU_LAYERS=0)
- Ollama: OLLAMA_NUM_PARALLEL=1
- Redis: --maxmemory 256mb
- Qdrant: Используется кастомный config.yaml + env переменные

## docker image ls, используем уже скаченные images

REPOSITORY                               TAG              IMAGE ID       CREATED          SIZE
redis                                    8.6.2-alpine     81b6f81d6a6c   12 days ago      134MB
mcr.microsoft.com/dotnet/sdk             8.0              a9330090b730   2 weeks ago      1.2GB
mcr.microsoft.com/dotnet/aspnet          8.0              d4d80bf500f4   2 weeks ago      320MB
nginx                                    1.28.1-alpine    35d0527c0661   3 months ago     81.1MB
ollama/ollama                            0.13.5           2c9595c555fd   3 months ago     6.14GB
qdrant/qdrant                            v1.16.2          dab6de32f7b2   4 months ago     272MB
alpine                                   latest           4b7ce07002c6   5 months ago     12.8MB

## Ollama Models, доступные модели embeddings

| NAME                                | ID              | SIZE      | MODIFIED         | **VECTOR SIZE** | RU	    |
|-------------------------------------|-----------------|-----------|------------------|-----------------|----------|
| qwen3-embedding:0.6b-fp16           | 67a7592a8852    | 1.2 GB    | 8 minutes ago    | **1024**        |          |
| qwen3-embedding:0.6b-q8_0           | ac6da0dfba84    | 639 MB    | 10 minutes ago   | **1024**        |          | 
| bge-m3:567m-fp16                    | 790764642607    | 1.2 GB    | 30 minutes ago   | **1024**        |          |

| nomic-embed-text:137m-v1.5-fp16     | 0a109f422b47    | 274 MB    | 30 minutes ago   | **768**         |          | 

| qllama/multilingual-e5-small:f16    | 3c8dead9831d    | 241 MB    | 27 hours ago     | **384**         |          |
| all-minilm:l6-v2                    | 1b226e2802db    | 45 MB     | 2 days ago       | **384**         |          |
| all-minilm:22m-l6-v2-fp16           | 1b226e2802db    | 45 MB     | 29 minutes ago   | **384**         |          |

## Notes

- План разработки еще пока в стадии разработки активной
- Ollama Models, необходимо с поддержкой русского языка
- Ollama Models, необходима с размерностью больше или равно 768, так как codebase kilo.ai, отправляет большие куски кода
- Ollama Models, с маленькими размерностями **384** оставляем для других codebase.
- Не выдумуываем, если, чего не знаем, спрашиваем у пользователя
- Используем активно при разработки знания/документацию через use context7. К примеру нужна "информация по ollama asp.net use context7", тогда будет получена актуальная документация по данной теме!
- 2026.04 начало разработки данного плана RAG
- Стабильная версия готова RAG с кэшем, а так с учетом возможных повторных запросов к ollama
