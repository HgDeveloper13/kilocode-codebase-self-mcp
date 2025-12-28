# Инструкция по использованию конфигурационного модуля

## Быстрый старт

### 1. Создание конфигурации

Конфигурация автоматически создается при первом запуске. Вы можете:

- Использовать файл `.config/config.json` для настроек по умолчанию
- Установить переменные окружения для переопределения настроек

### 2. Переменные окружения

```bash
# URL Qdrant сервера
export QDRANT_URL="https://your-qdrant-server.com:6333"

# API ключ для аутентификации
export QDRANT_API_KEY="your-api-key-here"
```

### 3. Использование в коде

```python
# Простое использование
from .config.config_loader import get_qdrant_url, get_qdrant_api_key

url = get_qdrant_url()
api_key = get_qdrant_api_key()

# Расширенное использование
from .config.config_loader import config_loader

config = config_loader.load()
qdrant_config = config['qdrant']
```

## Примеры интеграции

### Существующий код

**Было:**
```python
QDRANT_URL = "https://6888345.us-west-2-0.aws.cloud.qdrant.io:6333"
API_KEY = "zAs2626623k6-zF1cDJ-hfxY"
```

**Стало:**
```python
from .config.config_loader import get_qdrant_url, get_qdrant_api_key

QDRANT_URL = get_qdrant_url()
API_KEY = get_qdrant_api_key()
```

### Новый код

```python
from .config.config_loader import config_loader, ConfigError

try:
    # Загружаем конфигурацию
    config = config_loader.load()
    
    # Используем в приложении
    qdrant_url = config['qdrant']['url']
    api_key = config['qdrant']['api_key']
    
    # Работаем с Qdrant...
    
except ConfigError as e:
    print(f"Ошибка конфигурации: {e}")
    # Обработка ошибки
```

## Безопасность

### Рекомендации

1. **Не коммитьте чувствительные данные**
   - Файл `config.json` игнорируется `.gitignore`
   - Используйте переменные окружения в production

2. **Переменные окружения**
   - Самый безопасный способ хранения API ключей
   - Не сохраняются в репозитории
   - Можно менять без перезапуска приложения

3. **Файл конфигурации**
   - Используйте только для development
   - Убедитесь, что `.gitignore` работает
   - Не используйте реальные API ключи

## Отладка

### Проверка конфигурации

```bash
# Запустите тестовый скрипт
python .config/test_config.py
```

### Проверка переменных окружения

```bash
# Проверьте установленные переменные
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Установите временные переменные для теста
export QDRANT_URL="https://test.example.com:6333"
export QDRANT_API_KEY="test_key_123"
```

### Логирование

```python
from .config.config_loader import config_loader

# Включите логирование для отладки
import logging
logging.basicConfig(level=logging.DEBUG)

config = config_loader.load()
print(f"Загружено: {config}")
```

## Ошибки и решения

### ConfigError: "Отсутствует обязательная секция 'qdrant'"

**Причина:** Файл конфигурации не содержит секцию qdrant

**Решение:**
```json
{
  "qdrant": {
    "url": "https://your-server.com:6333",
    "api_key": "your-api-key"
  }
}
```

### ConfigError: "Некорректный URL Qdrant"

**Причина:** URL не начинается с http:// или https://

**Решение:**
```bash
export QDRANT_URL="https://your-server.com:6333"
# или
export QDRANT_URL="http://localhost:6333"
```

### ConfigError: "API ключ слишком короткий"

**Причина:** API ключ менее 10 символов

**Решение:** Убедитесь, что API ключ имеет достаточную длину

## Production deployment

### Docker

```dockerfile
# В Dockerfile
ENV QDRANT_URL="https://your-production-server.com:6333"
ENV QDRANT_API_KEY="your-production-api-key"
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: qdrant-config
type: Opaque
data:
  url: <base64-encoded-url>
  api-key: <base64-encoded-api-key>
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: QDRANT_URL
          valueFrom:
            secretKeyRef:
              name: qdrant-config
              key: url
        - name: QDRANT_API_KEY
          valueFrom:
            secretKeyRef:
              name: qdrant-config
              key: api-key
```

### CI/CD

```yaml
# GitHub Actions пример
env:
  QDRANT_URL: ${{ secrets.QDRANT_URL }}
  QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}