# Qdrant API v1.16.2 - Отчёт о тестировании

## Конфигурация

- **Версия Qdrant**: 1.16.2 (docker image: `qdrant/qdrant:v1.16.2`)
- **HTTP порт**: 6333
- **gRPC порт**: 6334
- **Прокси**: nginx 1.28.1
- **Режим**: Docker с internal сетью

---

## Результаты тестирования API

### ✅ Работающие endpoints

| Endpoint | Метод | Статус | Описание |
|----------|-------|--------|-----------|
| `/` | GET | ✅ 200 | Информация о Qdrant (версия, commit) |
| `/collections` | GET | ✅ 200 | Получение списка коллекций |
| `/collections/{name}` | GET | ✅ 200 | Информация о коллекции |
| `/collections/{name}` | PUT | ✅ 200 | Создание коллекции |
| `/collections/{name}` | DELETE | ✅ 200 | Удаление коллекции |
| `/collections/{name}/points` | PUT | ✅ 200 | Добавление/обновление точек (upsert) |
| `/collections/{name}/points/search` | POST | ✅ 200 | Поиск по векторам |

### ⚠️ Неработающие endpoints (проблемы с методом)

| Endpoint (ожидаемый) | Метод | Фактический результат | Корректный метод |
|---------------------|-------|----------------------|------------------|
| `/collections` | POST | ❌ 404 | Используйте PUT `/collections/{name}` |
| `/collections/{name}/points` | POST | ❌ 404 | Используйте PUT `/collections/{name}/points` |
| `/collections/{name}/search` | POST | ❌ 404 | Используйте POST `/collections/{name}/points/search` |
| `/points/search` | POST | ❌ 404 | Используйте POST `/collections/{name}/points/search` |

---

## Выявленные проблемы

### 1. Неверный HTTP метод для создания коллекции

**Описание**: В документации и запросах использовался метод `POST /collections`, но в Qdrant API v1.16.2 коллекции создаются через `PUT /collections/{collection_name}`.

**Ошибочный запрос**:
```bash
curl -X POST http://localhost:6333/collections \
  -H "Content-Type: application/json" \
  -d '{"name":"test","vectors":{"size":4,"distance":"Cosine"}}'
# Результат: 404 Not Found
```

**Правильный запрос**:
```bash
curl -X PUT http://localhost:6333/collections/test_collection \
  -H "Content-Type: application/json" \
  -d '{"vectors":{"size":4,"distance":"Cosine"}}'
# Результат: {"result":true,"status":"ok"}
```

### 2. Неверный endpoint для поиска

**Описание**: Поиск выполняется не через `/collections/{name}/search`, а через `/collections/{name}/points/search`.

**Ошибочный запрос**:
```bash
curl -X POST http://localhost:6333/collections/test_collection/search \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.1,0.2,0.3,0.4],"limit":3}'
# Результат: 404 Not Found
```

**Правильный запрос**:
```bash
curl -X POST http://localhost:6333/collections/test_collection/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.1,0.2,0.3,0.4],"limit":3}'
# Результат: {"result":[{"id":1,"version":1,"score":1.0}],"status":"ok"}
```

### 3. Неверный endpoint для добавления точек

**Описание**: Добавление точек выполняется через PUT, а не POST.

**Ошибочный запрос**:
```bash
curl -X POST http://localhost:6333/collections/test_collection/points \
  -H "Content-Type: application/json" \
  -d '{"points":[{"id":1,"vector":[0.1,0.2,0.3,0.4]}]}'
# Результат: 404 Not Found
```

**Правильный запрос**:
```bash
curl -X PUT http://localhost:6333/collections/test_collection/points \
  -H "Content-Type: application/json" \
  -d '{"points":[{"id":1,"vector":[0.1,0.2,0.3,0.4],"payload":{"text":"hello"}}]}'
# Результат: {"result":{"operation_id":1,"status":"acknowledged"},"status":"ok"}
```

---

## Примеры успешных операций

### Создание коллекции
```bash
curl -X PUT http://localhost:6333/collections/my_collection \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 4,
      "distance": "Cosine"
    }
  }'
```

### Добавление точек
```bash
curl -X PUT http://localhost:6333/collections/my_collection/points \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {
        "id": 1,
        "vector": [0.1, 0.2, 0.3, 0.4],
        "payload": {"text": "hello world"}
      }
    ]
  }'
```

### Поиск
```bash
curl -X POST http://localhost:6333/collections/my_collection/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, 0.3, 0.4],
    "limit": 5
  }'
```

---

## Выводы

1. **API Qdrant v1.16.2 работает корректно** - все основные операции выполняются при использовании правильных HTTP методов и endpoints.

2. **Основная проблема - несоответствие ожидаемому API**: 
   - POST методы для создания коллекций и точек не работают
   - Нужно использовать PUT методы
   - Endpoint для поиска отличается от документации

3. **Это не баг Qdrant**, а особенность API v1.16.2, которая требует использования PUT для создания/обновления ресурсов.

4. **Nginx прокси работает корректно** - он правильно проксирует все методы (GET, POST, PUT, DELETE) к Qdrant.