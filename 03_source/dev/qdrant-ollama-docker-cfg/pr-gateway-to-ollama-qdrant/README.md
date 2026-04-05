# ASP.NET Core Gateway + Ollama + Qdrant Stack

## Описание проекта

Данный проект представляет собой интегрированный стек сервисов для работы с LLM (Large Language Models) и векторными базами данных. В качестве основного entry point используется ASP.NET Core Gateway, который проксирует запросы к Ollama (LLM inference) и Qdrant (Vector Database).

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Network                          │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Client    │    │   Client    │    │      Client         │  │
│  │  (Gateway)  │    │  (Ollama)   │    │     (Qdrant)        │  │
│  │  :8080      │    │  :11434     │    │  :6333 / :6334      │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                       │             │
└─────────┼──────────────────┼───────────────────────┼─────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Network: internal                     │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   ASP.NET Core   │    │     Nginx        │                   │
│  │    Gateway       │    │     Proxy        │                   │
│  │  (aspnet-gateway)│    │  (nginx-proxy)   │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                             │
│           ├───────────────────────┤                             │
│           │                       │                             │
│  ┌────────▼─────────┐    ┌────────▼─────────┐                   │
│  │     Ollama       │    │     Qdrant       │                   │
│  │  (LLM Inference) │    │ (Vector DB)      │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Компоненты

| Сервис | Контейнер | Порт | Описание |
|--------|-----------|------|----------|
| **Gateway** | `aspnet-gateway` | 8080 | ASP.NET Core Gateway - единая точка входа |
| **Nginx** | `nginx-proxy` | 11434, 6333, 6334 | Reverse proxy для прямого доступа к Ollama и Qdrant |
| **Ollama** | `ollama` | internal | LLM inference engine |
| **Qdrant** | `qdrant` | internal | Vector database |

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose v2+
- Минимум 8GB RAM (рекомендуется 16GB+)
- Свободное место на диске: ~10GB

### Запуск стека

```bash
# Клонировать репозиторий (если еще не клонирован)
cd qdrant-ollama-docker-cfg/pr-gateway-to-ollama-qdrant

# Скопировать .env.example в .env и настроить переменные
cp .env.example .env

# Запустить все сервисы
docker compose up -d

# Проверить статус
docker compose ps

# Посмотреть логи
docker compose logs -f gateway
```

### Остановка стека

```bash
# Остановить все сервисы
docker compose down

# Остановить и удалить volumes (данные будут удалены!)
docker compose down -v
```

## Конфигурация

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте под свои нужды:

```bash
cp .env.example .env
```

#### Gateway

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `GATEWAY_PORT` | `8080` | Внешний порт для ASP.NET Core Gateway |
| `ASPNETCORE_ENVIRONMENT` | `Production` | Среда выполнения (.NET) |

#### Ollama

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `OLLAMA_PORT` | `11434` | Внешний порт для Ollama API |
| `OLLAMA_NUM_PARALLEL` | `1` | Количество параллельных запросов |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Максимальное количество загруженных моделей |
| `OLLAMA_GPU_LAYERS` | `0` | Количество слоев для GPU (0 = CPU only) |
| `OLLAMA_NUM_THREADS` | `4` | Количество потоков CPU |
| `OLLAMA_MAX_QUEUE` | `1024` | Максимальный размер очереди запросов |
| `OLLAMA_KEEP_ALIVE` | `2h` | Время жизни модели в памяти |
| `OLLAMA_DEBUG` | `false` | Включить debug логи |

#### Qdrant

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `QDRANT_HTTP_PORT` | `6333` | Внешний порт для Qdrant HTTP API |
| `QDRANT_GRPC_PORT` | `6334` | Внешний порт для Qdrant gRPC API |
| `QDRANT_TELEMETRY_DISABLED` | `true` | Отключить телеметрию |

## API Endpoints

### ASP.NET Core Gateway

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/health` | Проверка здоровья сервиса |
| `POST` | `/api/ollama/api/embed` | Получить embedding через Ollama |
| `POST` | `/api/ollama/api/generate` | Генерация текста через Ollama |
| `POST` | `/api/ollama/api/chat` | Чат через Ollama |
| `GET` | `/api/ollama/api/tags` | Список доступных моделей Ollama |
| `GET` | `/api/qdrant/collections` | Получить список коллекций Qdrant |
| `POST` | `/api/qdrant/collections` | Создать коллекцию в Qdrant |
| `POST` | `/api/qdrant/collections/{name}/points` | Добавить точки в коллекцию |
| `POST` | `/api/qdrant/collections/{name}/search` | Поиск похожих точек |

### Ollama (через Nginx)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `http://localhost:11434/api/embed` | Получить embedding |
| `POST` | `http://localhost:11434/api/generate` | Генерация текста |
| `POST` | `http://localhost:11434/api/chat` | Чат |
| `GET` | `http://localhost:11434/api/tags` | Список доступных моделей |

### Qdrant (через Nginx)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `http://localhost:6333/collections` | Список коллекций |
| `POST` | `http://localhost:6333/collections/{name}` | Создать коллекцию |
| `POST` | `http://localhost:6333/collections/{name}/points` | Добавить точки |
| `POST` | `http://localhost:6333/collections/{name}/search` | Поиск |

## Интеграция с существующим стеком

Этот проект является расширением базового стека `pr-core-train-to-ollama-qdrant`. Основные отличия:

1. **ASP.NET Core Gateway** - добавлен как единая точка входа для всех запросов
2. **Упрощенная конфигурация** - все сервисы запускаются через один docker-compose.yml
3. **Гибкие порты** - все внешние порты настраиваются через `.env` файл

### Миграция с pr-core-train-to-ollama-qdrant

Если у вас уже есть запущенный стек из `pr-core-train-to-ollama-qdrant`:

1. Остановите старый стек:
   ```bash
   cd ../pr-core-train-to-ollama-qdrant
   docker compose down
   ```

2. Запустите новый стек:
   ```bash
   cd ../pr-gateway-to-ollama-qdrant
   docker compose up -d
   ```

3. Данные Ollama и Qdrant сохранятся, т.к. используются именованные volumes.

## Структура проекта

```
pr-gateway-to-ollama-qdrant/
├── docker-compose.yml          # Основная конфигурация Docker
├── Dockerfile                  # Dockerfile для ASP.NET Core Gateway
├── .dockerignore               # Исключения для Docker build
├── .env.example                # Шаблон переменных окружения
├── README.md                   # Эта документация
├── nginx/
│   └── nginx.conf              # Конфигурация Nginx
├── qdrant/
│   └── config.yaml             # Конфигурация Qdrant (опционально)
└── src/
    └── EmbeddingGateway/       # Исходный код ASP.NET Core Gateway
        ├── Program.cs
        ├── appsettings.json
        ├── Endpoints/
        ├── Services/
        └── Models/
```

## Troubleshooting

### Gateway не запускается

```bash
# Проверить логи
docker compose logs gateway

# Пересобрать образ
docker compose build --no-cache gateway
```

### Ollama не загружает модели

```bash
# Зайти в контейнер Ollama
docker exec -it ollama bash

# Загрузить модель
ollama pull llama3.2

# Проверить доступные модели
ollama list
```

### Qdrant недоступен

```bash
# Проверить статус
curl http://localhost:6333/

# Проверить логи
docker compose logs qdrant
```

### Очистка и перезапуск

```bash
# Полная очистка (ВНИМАНИЕ: данные будут удалены!)
docker compose down -v

# Перезапуск без удаления данных
docker compose down
docker compose up -d
```

## Лицензия

MIT
