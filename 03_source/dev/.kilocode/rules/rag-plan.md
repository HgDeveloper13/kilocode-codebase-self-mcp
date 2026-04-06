# План разработки: Gateway Local Self - RAG-стека

- .NET 8, ASP.NET 8
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
- У нас получается nginx единственная точка входа. Nginx прямо на qdrant отправляет запросы, пользователь обращается по стандартной схеме к qdrant localhost:6333. gateway > redis. gateway > ollama. nginx > gateway.
- Ollama работает без GPU, все вычисления на CPU
- Ollama: CPU-режим (OLLAMA_GPU_LAYERS=0)
- Ollama: OLLAMA_NUM_PARALLEL=1
- Redis: --maxmemory 256mb
- Qdrant: Используется кастомный config.yaml + env переменные

## docker image ls

REPOSITORY                               TAG              IMAGE ID       CREATED          SIZE
redis                                    8.6.2-alpine     81b6f81d6a6c   12 days ago      134MB
mcr.microsoft.com/dotnet/sdk             8.0              a9330090b730   2 weeks ago      1.2GB
mcr.microsoft.com/dotnet/aspnet          8.0              d4d80bf500f4   2 weeks ago      320MB
nginx                                    1.28.1-alpine    35d0527c0661   3 months ago     81.1MB
ollama/ollama                            0.13.5           2c9595c555fd   3 months ago     6.14GB
qdrant/qdrant                            v1.16.2          dab6de32f7b2   4 months ago     272MB
alpine                                   latest           4b7ce07002c6   5 months ago     12.8MB

## Ollama Models

| NAME                                | ID              | SIZE      | MODIFIED         | **VECTOR SIZE** | RU	    |
|-------------------------------------|-----------------|-----------|------------------|-----------------|----------|
| qwen3-embedding:0.6b-fp16           | 67a7592a8852    | 1.2 GB    | 8 minutes ago    | **1024**        |          |
| qwen3-embedding:0.6b-q8_0           | ac6da0dfba84    | 639 MB    | 10 minutes ago   | **1024**        |          | 
| bge-m3:567m-fp16                    | 790764642607    | 1.2 GB    | 30 minutes ago   | **1024**        |          |

| nomic-embed-text:137m-v1.5-fp16     | 0a109f422b47    | 274 MB    | 30 minutes ago   | **768**         |          | 

* qllama/multilingual-e5-small:f16    | 3c8dead9831d    | 241 MB    | 27 hours ago     | **384**         |          |
| all-minilm:l6-v2                    | 1b226e2802db    | 45 MB     | 2 days ago       | **384**         |          |
> all-minilm:22m-l6-v2-fp16           | 1b226e2802db    | 45 MB     | 29 minutes ago   | **384**         |          |

## Notes

- План разработки еще пока в стадии разработки активной
- Ollama Models, необходимо с поддержкой русского языка
- Ollama Models, необходима с размерностью больше или равно 768, так как codebase kilo.ai, отправляет большие куски кода
- Ollama Models, с маленькими размерностями **384** оставляем для других codebase.
- Не выдумуываем, если, чего не знаем, спрашиваем у пользователя
- Используем активно при разработки знания/документацию через use context7. К примеру нужна "информация по ollama asp.net use context7", тогда будет получена актуальная документация по данной теме!
- 2026.04 начало разработки данного плана RAG
