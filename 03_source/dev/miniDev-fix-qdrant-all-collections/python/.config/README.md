# Конфигурация Qdrant Manager

Данная директория содержит конфигурационные файлы для Qdrant Manager - системы автоматического управления коллекциями Qdrant с фокусом на оптимизацию `indexing_threshold`.

## Файлы конфигурации

### 📄 config.json
Основной файл конфигурации в формате JSON. Содержит все настройки системы:
- Параметры подключения к Qdrant
- Настройки коллекций и операций
- Конфигурация логирования и отчетности
- Настройки для разных окружений

**Использование:**
```python
from qdrant_manager import QdrantConfig
config = QdrantConfig('config.json')
```

### 📄 config.example.json
Пример конфигурационного файла с подробными комментариями. Содержит:
- Описания всех параметров
- Рекомендуемые значения по умолчанию
- Пояснения по переменным окружения
- Примеры настроек для разных окружений

**Использование:** Скопируйте в `config.json` и настройте под ваши нужды.

### 📄 config.yaml
YAML версия конфигурации с расширенной поддержкой:
- Переменных окружения с fallback значениями
- Предустановленных конфигураций для разных типов нагрузки
- Настроек для development/staging/production окружений
- Интеграций с Prometheus и webhooks

**Использование:**
```python
from qdrant_manager import QdrantConfig
config = QdrantConfig('config.yaml')
```

## Переменные окружения

Для безопасного хранения секретов используйте переменные окружения:

### Обязательные переменные
```bash
export QDRANT_API_KEY="your-secret-api-key"
```

### Дополнительные переменные (опциональные)
```bash
# Qdrant настройки
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
export QDRANT_TIMEOUT="30"

# Настройки коллекций
export COLLECTIONS_DEFAULT_THRESHOLD="1"
export COLLECTIONS_BATCH_SIZE="100"

# Операции
export OPERATIONS_DRY_RUN="false"
export OPERATIONS_CONFIRM="true"

# Логирование
export LOGGING_LEVEL="INFO"
export LOGGING_FILE="logs/qdrant_manager.log"

# Окружение
export DEV_LOGGING_LEVEL="DEBUG"
export PROD_LOGGING_LEVEL="WARNING"
```

## Ключевые параметры

### indexing_threshold
**Рекомендуемое значение: 1**
- Низкое значение ускоряет индексацию новых векторов
- По умолчанию в Qdrant может быть высоким, что замедляет работу
- Проект автоматически исправляет это значение для всех коллекций

### batch_size
**Рекендуемое значение: 100**
- Размер батча для массовых операций
- Влияет на производительность при работе с большим количеством коллекций

### retry_attempts
**Рекомендуемое значение: 3**
- Количество попыток при временных сбоях
- Обеспечивает надежность операций

## Настройка для разных окружений

### Development
```bash
export DEV_LOGGING_LEVEL="DEBUG"
export DEV_DRY_RUN="true"
export DEV_CONFIRM="false"
```

### Production
```bash
export PROD_LOGGING_LEVEL="WARNING"
export PROD_DRY_RUN="false"
export PROD_CONFIRM="true"
export QDRANT_API_KEY="secure-production-key"
```

## Примеры использования

### 1. Локальная разработка
```bash
cp config.example.json config.json
# Отредактируйте config.json под ваши нужды
python qdrant_fixer.py
```

### 2. Продакшн с переменными окружения
```bash
# Установите переменные окружения
export QDRANT_API_KEY="your-production-key"
export QDRANT_HOST="qdrant.example.com"
export LOGGING_LEVEL="WARNING"

# Используйте config.yaml
python qdrant_fixer.py --config config.yaml
```

### 3. Тестирование (dry-run)
```bash
export OPERATIONS_DRY_RUN="true"
export OPERATIONS_CONFIRM="false"
python qdrant_fixer.py
```

## Безопасность

⚠️ **Важно:**
- Никогда не коммитьте API ключи в Git
- Используйте переменные окружения для секретов
- В production всегда включайте `confirm_before_fix: true`
- Регулярно обновляйте API ключи

## Поддержка

При возникновении проблем:
1. Проверьте логи в файле `logs/qdrant_manager.log`
2. Убедитесь, что Qdrant сервер доступен
3. Проверьте правильность API ключа
4. Запустите в `dry_run` режиме для тестирования

Для получения подробной информации см. `analysis_qdrant_project.md`.