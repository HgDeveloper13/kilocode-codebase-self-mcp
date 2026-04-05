# Qdrant Manager - Руководство для AI Ассистента

## 📋 Описание проекта

**Qdrant Manager** - упрощенная система для управления и оптимизации коллекций Qdrant с фокусом на массовое исправление `indexing_threshold`. Проект состоит из двух основных скриптов для работы с коллекциями Qdrant.

## 🎯 Основные задачи проекта

- **Массовое исправление indexing_threshold** - автоматическая оптимизация всех коллекций
- **Проверка статуса коллекций** - анализ текущего состояния и рекомендации
- **Отчетность** - автоматическая генерация детальных отчетов
- **Безопасность** - поддержка dry-run режима и интерактивного подтверждения

## 📁 Структура проекта

```
python/
├── qdrant_fixer.py          # Основной скрипт исправления indexing_threshold
├── qdrant_status.py         # Скрипт проверки статуса коллекций
├── requirements.txt         # Зависимости проекта
├── .env.example            # Пример конфигурации
├── QUICKSTART.md           # Чек-лист быстрого старта (5 минут)
├── README.md               # Подробная документация
├── test_imports.py         # Тест импортов и структуры
├── run_fix.bat/.sh         # Скрипты запуска исправления (Windows/Linux)
├── run_status.bat/.sh      # Скрипты запуска проверки статуса (Windows/Linux)
├── CONTRIBUTING.md         # Guidelines для разработчиков
└── LICENSE                 # MIT лицензия
```

## 🚀 Быстрый запуск

### 1. Базовая настройка

```bash
# Переходим в директорию проекта
cd python

# Устанавливаем зависимости
pip install -r requirements.txt

# Копируем пример конфигурации
cp .env.example .env

# Настраиваем подключение в .env файле
# QDRANT_URL="http://localhost:6333"
# QDRANT_API_KEY="your-api-key-here"
```

### 2. Проверка статуса всех коллекций

```bash
# Проверка статуса (Windows)
run_status.bat

# Проверка статуса (Linux/Mac)
./run_status.sh

# Прямой запуск Python
python qdrant_status.py
```

### 3. Исправление indexing_threshold

```bash
# Интерактивное исправление с подтверждением (Windows)
run_fix.bat

# Интерактивное исправление с подтверждением (Linux/Mac)
./run_fix.sh

# Автоматическое исправление без подтверждения (Windows)
run_fix.bat --auto

# Автоматическое исправление без подтверждения (Linux/Mac)
./run_fix.sh --auto
```

## 🛠 Основные команды

### Проверка статуса коллекций

```bash
# Базовый статус всех коллекций
python qdrant_status.py

# Минимальный вывод
python qdrant_status.py --quiet

# Сохранение отчета в файл
python qdrant_status.py --output my_status_report.txt

# Использование конкретного целевого threshold
python qdrant_status.py --threshold 1

# Использование с параметрами подключения
python qdrant_status.py --url http://my-qdrant:6333 --api-key my-key
```

### Исправление коллекций

```bash
# Базовое исправление с подтверждением
python qdrant_fixer.py

# Автоматическое исправление без подтверждения
python qdrant_fixer.py --auto

# Тестовый режим (без реальных изменений)
python qdrant_fixer.py --dry-run

# Исправление с конкретным threshold
python qdrant_fixer.py --threshold 5

# Использование с параметрами подключения
python qdrant_fixer.py --url http://my-qdrant:6333 --api-key my-key --auto
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `QDRANT_URL` | URL для подключения к Qdrant | `http://localhost:6333` |
| `QDRANT_API_KEY` | API ключ для аутентификации | не используется |

### Приоритет настроек

1. **Аргументы командной строки** (наивысший приоритет)
2. **Переменные окружения**
3. **Значения по умолчанию**

### Примеры настройки

```bash
# Локальный Qdrant без аутентификации
export QDRANT_URL="http://localhost:6333"

# Удаленный Qdrant с аутентификацией
export QDRANT_URL="https://qdrant.example.com:6333"
export QDRANT_API_KEY="your-secret-api-key"

# Переопределение через аргументы
python qdrant_fixer.py --url http://localhost:6334 --api-key different-key --auto
```

## 📊 Отчетность

### Типы отчетов

1. **Статус отчеты** (`qdrant_status_YYYYMMDD_HHMMSS.txt`):
   - Состояние всех коллекций
   - Статистика по векторам и индексации
   - Анализ `indexing_threshold` значений
   - Рекомендации по оптимизации

2. **Отчеты об исправлении** (`qdrant_fix_YYYYMMDD_HHMMSS.txt`):
   - Результаты операций исправления
   - Статистика успешных/неуспешных операций
   - Детали по каждой коллекции

### Местоположение отчетов

Все отчеты сохраняются в директорию `reports/` с автоматической генерацией имен файлов по времени создания.

## 🔧 Полный пример рабочего процесса

```bash
# 1. Проверяем текущий статус
python qdrant_status.py

# 2. Тестируем исправление в dry-run режиме
python qdrant_fixer.py --dry-run

# 3. Выполняем реальное исправление
python qdrant_fixer.py --auto

# 4. Проверяем результат
python qdrant_status.py --quiet
```

## 🐛 Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к Qdrant**:
   ```bash
   ❌ Ошибка подключения к Qdrant: Connection refused
   ```
   **Решение:**
   - Проверьте доступность хоста и порта
   - Убедитесь, что Qdrant запущен
   - Проверьте правильность URL

2. **Ошибка аутентификации**:
   ```bash
   ❌ Ошибка подключения к Qdrant: 401 Unauthorized
   ```
   **Решение:**
   - Проверьте API ключ
   - Убедитесь в корректности переменной `QDRANT_API_KEY`

3. **Коллекции не найдены**:
   ```bash
   ⚠️  Коллекции не найдены
   ```
   **Решение:**
   - Проверьте права доступа к коллекциям
   - Убедитесь в корректности подключения

### Отладка

```bash
# 1. Проверьте подключение
python qdrant_status.py --quiet

# 2. Тестируйте без изменений
python qdrant_fixer.py --dry-run

# 3. Проверьте детальный статус
python qdrant_status.py --output debug_report.txt

# 4. Используйте конкретные параметры подключения
python qdrant_fixer.py --url http://localhost:6333 --api-key test-key --dry-run
```

## 📋 Подробная справка по командам

### qdrant_status.py

```
usage: qdrant_status.py [-h] [--url URL] [--api-key API_KEY] [--output OUTPUT]
                        [--quiet] [--threshold THRESHOLD]

Qdrant Status - проверка статуса всех коллекций

optional arguments:
  -h, --help            show this help message and exit
  --url URL             URL для подключения к Qdrant
  --api-key API_KEY     API ключ для аутентификации
  --output OUTPUT       Путь для сохранения отчета
  --quiet               Минимальный вывод
  --threshold THRESHOLD
                        Целевое значение indexing_threshold (по умолчанию: 1)
```

### qdrant_fixer.py

```
usage: qdrant_fixer.py [-h] [--url URL] [--api-key API_KEY] 
                       [--threshold THRESHOLD] [--dry-run] [--auto]

Qdrant Fixer - массовое исправление indexing_threshold коллекций

optional arguments:
  -h, --help            show this help message and exit
  --url URL             URL для подключения к Qdrant
  --api-key API_KEY     API ключ для аутентификации
  --threshold THRESHOLD
                        Новое значение indexing_threshold (по умолчанию: 1)
  --dry-run             Режим тестирования без реальных изменений
  --auto                Автоматическое выполнение без подтверждения
```

## 📝 Зависимости

Основные зависимости проекта указаны в `requirements.txt`:
- `qdrant-client>=1.6.0` - Официальный клиент Qdrant

Для установки зависимостей:
```bash
pip install -r requirements.txt
```

## ⚠️ Важные замечания

**⚠️ Важно**: Всегда используйте `--dry-run` для тестирования перед выполнением реальных операций на продакшн окружении.

**💡 Совет**: Начните с `qdrant_status.py` для анализа текущего состояния, затем используйте `qdrant_fixer.py --dry-run` для тестирования изменений.

**🔐 Безопасность**: 
- Всегда тестируйте в `--dry-run` режиме
- Используйте интерактивный режим для подтверждения операций
- Создавайте резервные копии перед массовыми операциями

## 📚 Дополнительная документация

- **QUICKSTART.md** - Чек-лист для быстрого старта (5 минут)
- **CONTRIBUTING.md** - Guidelines для разработчиков
- **README.md** - Подробная техническая документация