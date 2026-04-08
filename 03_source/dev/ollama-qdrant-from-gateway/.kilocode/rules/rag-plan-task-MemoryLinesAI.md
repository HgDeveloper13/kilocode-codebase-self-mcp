# Текущей контекст проекта RAG

## Расположение текущего проекта

> qdrant-ollama-docker-cfg\pr-core-train-to-ollama-qdrant

- Только в данной папке проводим изменения!

## Расположение плана разработки, по которому был собран данный проект

> .kilocode\rules\rag-plan.md

- Обновляем в таком же стиле, как план разработки написан! Вносим критичные данные, в него! Спрашиваем у пользователя, вносить ли данные в план разработки и какие именно варианты предложи ему!
- К примеру не было учтено, что в документации Ollama есть два разных API для embeddings, в процессе было выявлено, это необходимо предложить пользователю обновить план разработки с учетом этого!
- К примеру было выявлено в процессе тестирования\разработки\диагностики, Ошибка - Модель Ollama не способна к вложению: qwen3-embedding:0.6b-q8_0, оказалось, что gateway не был верно написан, и что нужно было исправить его, после успешного исправления и проведенных тестов, было подтверждено пользователем, что исправлено все, и индексация работает успешно, необходимо в таких случаях проверь план разработки и предложить разумные и минимальные внесенния в данный план разработки, чтобы не было в будущем таких ошибок!

## Текущий статус проекта

- ✅ Сборка успешно завершена, проект контейнер успешно запущен
- ✅ Ollama успешно смонтирована с готовым volume, есть модели embeddings
- ✅ Gateway исправлен и протестирован
- ✅ Индексация кодовой базы работает через Gateway с Redis кэшем
- ✅ Поддержка OpenAI-совместимого API /v1/embeddings реализована
- ✅ **Индексация кодовой базы: успешно инициализирована! Обработано 180 блоков, добавлены в Qdrant!**
- ✅ Реализован механизм ожидания кэша для повторных запросов
- ✅ Стабильная версия готова RAG
- Планируем: Реализовать сервис логирования кэша RAG

## Текущая задача по проекту

- Реализовать сервис логирования кэша RAG в формате `Services/CacheLogger.cs`
-- Добавить систему логов для Gateway: обёртка для вывода в одну строку, переключение формата (text/json), подготовка к отправке во внешние системы (Loki/Prometheus)

### Контекст задачи

-- Переключение типа логов через `appsettings.json`
-- Внедрение в три эндпоинта: `/api/embed`, `/api/embeddings`, `/v1/embeddings`
-- Замер времени инференса через `Stopwatch`
-- Модель `qwen3-embedding:0.6b-q8_0` требует `BatchSize ≤ 10` для стабильности на CPU N100

### Требования к реализации

--- **Статический класс** `CacheLogger` с методами:
---- `Hit(string key, int size)` — кэш-хит
---- `Miss(string key, int size, double durationSeconds)` — кэш-мисс с временем инференса
---- `Coalesced(string key)` — запрос подписан на уже идущий инференс

--- **Формат вывода** переключается через `appsettings.json`:

```json
"Logging": { "CacheFormat": "text" } // или "json"
```

--- **Форматы логов**:
---- Text: `[CACHE_HIT] emb:a3f5... | 3.0KB | 12:27:36.261`
---- JSON: `{"ts":"...","event":"CACHE_HIT","key":"emb:...","size":3000,"duration":null}`

--- **Технические детали**:
---- `System.Text.Json` для сериализации (без внешних зависимостей)
---- `_useJson` — `volatile` для потокобезопасности
---- Форматирование размера: `B` / `KB` / `MB`
---- Валидация: `key != null`, `size >= 0`

### Ожидаемый результат

--- Файл `Services/CacheLogger.cs` с реализацией (необходимо создать его)
--- Обновлённый `Program.cs` с вызовами `CacheLogger.Hit/Miss/Coalesced`
--- Пример `appsettings.json` с настройкой `"CacheFormat": "text"`
--- (Опционально) Регистрация метрик Prometheus

### Критерии приёмки

--- [ ] Код компилируется в .NET 8
--- [ ] При `CacheFormat: "text"` — читаемый вывод в консоль
--- [ ] При `CacheFormat: "json"` — валидный JSON одной строкой
--- [ ] Методы потокобезопасны (нет гонок при смене формата)
--- [ ] Размер форматируется корректно: `500B` / `2.3KB` / `1.1MB`

### Возможности которые добавим после текущей задачи - система логов

-- Prometheus-метрики (опционально, но желательно):
rag_cache_hits_total — счётчик хитов
rag_cache_misses_total — счётчик миссов
rag_cache_coalesced_total — счётчик coalesced-запросов

### Интеграция

- Добавить систему логов для нашего gateway в Program.cs внедрить вызовы CacheLogger.Hit/Miss/Coalesced
- Добавить Stopwatch для замера времени инференса в блоке try эндпоинтов

-- Пример использования в Program.cs

```csharp
// В начале try-блока:
var stopwatch = System.Diagnostics.Stopwatch.StartNew();

// После сохранения в кэш:
if (response.IsSuccessStatusCode)
{
    await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(CacheTtlDays));
    stopwatch.Stop();
    CacheLogger.Miss(cacheKey, body.Length, stopwatch.Elapsed.TotalSeconds);
}

// При кэш-хите:
if (cachedResult.HasValue)
{
    CacheLogger.Hit(cacheKey, body.Length);
    // ... возврат ответа
}

// При coalesced:
if (inProgress.HasValue)
{
    CacheLogger.Coalesced(cacheKey);
    await WaitForCacheAsync(...);
}
```

--- 🛠 Пример вставки в текущий код (без singleflight)

```csharp
// В блоке кэш-хита
if (cachedResult.HasValue)
{
    CacheLogger.Hit(cacheKey, body.Length); // ← одна строка
    context.Response.ContentType = "application/json";
    await context.Response.WriteAsync(cachedResult!);
    return;
}

// В блоке ожидания чужого запроса
if (inProgress.HasValue)
{
    CacheLogger.Coalesced(cacheKey); // ← одна строка
    await WaitForCacheAsync(context, db, cacheKey, inProgressKey);
    return;
}

// После сохранения результата от Ollama
if (response.IsSuccessStatusCode)
{
    await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(CacheTtlDays));
    CacheLogger.Miss(cacheKey, body.Length, stopwatch.Elapsed.TotalSeconds); // ← одна строка
}
```

-- appsettings.jsons — готов к внедрению

```json
{
  "Logging": {
    "CacheFormat": "text"
  },
  "Ollama": {
    "Url": "http://ollama:11434"
  },
  "Redis": {
    "Host": "redis",
    "Port": 6379
  }
}
```

-- CacheLogger.cs — готов к внедрению

```csharp
// File: Services/CacheLogger.cs
using System.Text.Json;

namespace EmbeddingGateway.Services;

public static class CacheLogger
{
    private static volatile bool _useJson = false; // Переключатель: текст/JSON

    public static void Configure(bool useJson) => _useJson = useJson;

    public static void Hit(string key, int size) => Log("CACHE_HIT", key, size, null);
    public static void Miss(string key, int size, double durationSec) => Log("CACHE_MISS", key, size, durationSec);
    public static void Coalesced(string key) => Log("CACHE_COALESCED", key, 0, null);

    private static void Log(string @event, string key, int size, double? durationSec)
    {
        var ts = DateTime.UtcNow;
        if (_useJson)
        {
            // Готов к Loki/ELK/Prometheus
            var entry = new { ts, @event, key, size, duration = durationSec };
            Console.WriteLine(JsonSerializer.Serialize(entry));
        }
        else
        {
            // Человекочитаемый формат для отладки
            var dur = durationSec.HasValue ? $" | {durationSec:F1}s" : "";
            var sz = size > 1024 * 1024 ? $"{size / (1024 * 1024):F1}MB" : 
                     size > 1024 ? $"{size / 1024:F1}KB" : $"{size}B";
            Console.WriteLine($"[{@event}] {key} | {sz}{dur} | {ts:HH:mm:ss.fff}");
        }
    }
}
```

## Подзадачи (статус)

- Пример

*>* уровень 1 (статус)
*>>* уровень 2 (статус)
*>>>* уровень 3 (статус)

- Текущие подзадачи

*>* Реализация CacheLogger.cs (🔄 в работе)
*>>* Статический класс с методами Hit/Miss/Coalesced (⏳ ожидает)
*>>* Переключатель формата через конфигурацию (⏳ ожидает))
*>>* Форматирование размера B/KB/MB (⏳ ожидает)
*>>* Потокобезопасность через volatile (⏳ ожидает)

*>* Интеграция в Gateway (⏳ ожидает)
*>>* /api/embed — замена `Console.WriteLine` на `CacheLogger.*`
*>>* /api/embeddings — аналогично
*>>* /v1/embeddings — аналогично + замер длительности через `Stopwatch`

*>* Обновление appsettings.json (⏳ ожидает)
*>>* Добавить секцию `"Logging": { "CacheFormat": "text" }`
*>>* Документировать переключение формата

*>* Предложения по обновлению .kilocode\rules\rag-plan.md (❓ требует вашего ОК)
*>>* Зафиксировать: поддержка двух Ollama embedding API (`/api/embed`, `/api/embeddings`)
*>>* Добавить: механизм кэш-ожидания (polling) как штатный паттерн
*>>* Уточнить: модель `qwen3-embedding:0.6b-q8_0` требует `BatchSize ≤ 10` на CPU N100
*>>* Добавить: сервис логирования кэша `CacheLogger` с поддержкой text/json
