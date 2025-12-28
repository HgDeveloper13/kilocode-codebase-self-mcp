# Конфигурационный модуль

Этот модуль предоставляет гибкую систему управления конфигурацией для проекта miniDev-fix-qdrant-all-collections.

## Структура

```
.config/
├── __init__.py          # Пакет Python
├── config.json          # Файл конфигурации по умолчанию
├── config_loader.py     # Модуль загрузки конфигурации
└── test_config.py       # Тестовый скрипт
```

## Использование

### Базовое использование

```python
from .config.config_loader import get_qdrant_url, get_qdrant_api_key

# Получение URL Qdrant
url = get_qdrant_url()

# Получение API ключа
api_key = get_qdrant_api_key()
```

### Расширенное использование

```python
from .config.config_loader import config_loader, ConfigError

try:
    # Загрузка всей конфигурации
    config = config_loader.load()
    
    # Получение конфигурации Qdrant
    qdrant_config = config_loader.get_qdrant_config()
    
    print(f"URL: {qdrant_config['url']}")
    print(f"API Key: {qdrant_config['api_key']}")
    
except ConfigError as e:
    print(f"Ошибка конфигурации: {e}")
```

## Приоритет конфигурации

Модуль поддерживает следующий порядок приоритета:

1. **Переменные окружения** (наивысший приоритет)
2. **Файл конфигурации** (низший приоритет)

### Переменные окружения

- `QDRANT_URL` - URL Qdrant сервера
- `QDRANT_API_KEY` - API ключ для Qdrant

Пример использования переменных окружения:

```bash
export QDRANT_URL="https://your-qdrant-server.com:6333"
export QDRANT_API_KEY="your-api-key"
```

### Файл конфигурации

Файл `config.json` содержит настройки по умолчанию:

```json
{
  "qdrant": {
    "url": "https://6888345.us-west-2-0.aws.cloud.qdrant.io:6333",
    "api_key": "zAs2626623k6-zF1cDJ-hfxY"
  }
}
```

## Валидация

Модуль автоматически проверяет:

- Наличие обязательных секций и полей
- Корректность URL (должен начинаться с http:// или https://)
- Длину API ключа (не менее 10 символов)

## Тестирование

Для тестирования модуля запустите:

```bash
cd miniDev-fix-qdrant-all-collections/python
python .config/test_config.py
```

## Интеграция с существующим кодом

Чтобы использовать новый конфигурационный модуль в существующих скриптах:

1. Импортируйте нужные функции:
   ```python
   from .config.config_loader import get_qdrant_url, get_qdrant_api_key
   ```

2. Замените жестко закодированные значения:
   ```python
   # Было
   QDRANT_URL = "https://..."
   QDRANT_API_KEY = "..."
   
   # Стало
   QDRANT_URL = get_qdrant_url()
   QDRANT_API_KEY = get_qdrant_api_key()
   ```

## Обработка ошибок

Все ошибки конфигурации выбрасываются как `ConfigError`. Рекомендуется обрабатывать эти ошибки:

```python
from .config.config_loader import ConfigError

try:
    url = get_qdrant_url()
except ConfigError as e:
    print(f"Ошибка загрузки конфигурации: {e}")
    # Обработка ошибки...