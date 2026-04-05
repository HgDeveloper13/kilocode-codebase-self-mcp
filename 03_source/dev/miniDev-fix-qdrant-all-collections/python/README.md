# Qdrant Manager - Упрощенная версия

Простые скрипты для управления и оптимизации коллекций Qdrant с фокусом на массовое исправление `indexing_threshold`.

## ⚡ Быстрый старт

Для быстрой настройки и начала работы следуйте [**чек-листу в QUICKSTART.md**](./QUICKSTART.md).

⏱️ **Время настройки**: ~5 минут

## 🎯 Цель проекта

Автоматическое управление и оптимизация коллекций в Qdrant с основной задачей - исправление `indexing_threshold` для всех коллекций одновременно.

**Ключевая проблема**: В Qdrant коллекции могут иметь высокий `indexing_threshold`, что замедляет процесс индексации векторов. Проект решает эту проблему массовым исправлением на значение 1.

## 📁 Структура проекта

```
python/
├── qdrant_fixer.py      # Основной скрипт для исправления indexing_threshold
├── qdrant_status.py     # Скрипт для проверки статуса всех коллекций
├── requirements.txt     # Зависимости проекта
├── .env.example         # Пример файла переменных окружения
├── QUICKSTART.md        # ✅ Чек-лист для быстрого старта (5 минут)
├── test_imports.py      # Скрипт для тестирования импортов и структуры
├── LICENSE              # MIT лицензия
├── CONTRIBUTING.md      # Guidelines для разработчиков
├── run_fix.bat          # Скрипт запуска для Windows (исправление)
├── run_status.bat       # Скрипт запуска для Windows (проверка статуса)
├── run_fix.sh           # Скрипт запуска для Linux/Mac (исправление)
├── run_status.sh        # Скрипт запуска для Linux/Mac (проверка статуса)
├── .gitignore           # Исключения для Git
└── README.md            # Данная документация
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd python
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте пример файла и настройте свои параметры:

```bash
# Копируем пример файла
cp .env.example .env

# Редактируем .env файл с вашими настройками
# Откройте .env в текстовом редакторе и заполните:
# QDRANT_URL="http://your-qdrant:6333"
# QDRANT_API_KEY="your-api-key-here"
```

Или установите переменные окружения напрямую:

```bash
# Базовые настройки
export QDRANT_URL="http://localhost:6333"

# С API ключом (если требуется)
export QDRANT_URL="https://your-qdrant.com:6333"
export QDRANT_API_KEY="your-api-key-here"
```

### 3. Запуск скриптов

#### Windows:
```cmd
# Проверка статуса
run_status.bat

# Исправление коллекций (интерактивно)
run_fix.bat

# Автоматическое исправление
run_fix.bat --auto
```

#### Linux/Mac:
```bash
# Проверка статуса
./run_status.sh

# Исправление коллекций (интерактивно)
./run_fix.sh

# Автоматическое исправление
./run_fix.sh --auto
```

#### Прямой запуск Python:
```bash
# Проверка статуса
python qdrant_status.py

# Исправление коллекций
python qdrant_fixer.py
```

### 4. Проверка статуса

```bash
python qdrant_status.py
```

### 5. Исправление коллекций

```bash
# Интерактивное исправление с подтверждением
python qdrant_fixer.py

# Автоматическое исправление без подтверждения
python qdrant_fixer.py --auto

# Тестовый режим (без реальных изменений)
python qdrant_fixer.py --dry-run
```

## 🛠 Основные скрипты

### Проверка статуса (qdrant_status.py)

Получает подробную информацию о всех коллекциях и анализирует их состояние.

**Основные возможности:**
- Получение статуса всех коллекций
- Анализ `indexing_threshold` значений
- Выявление коллекций, требующих исправления
- Генерация подробного отчета в `reports/`

**Примеры использования:**

```bash
# Базовый статус
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

### Исправление коллекций (qdrant_fixer.py)

Массово исправляет `indexing_threshold` для всех коллекций с настройкой дополнительных параметров.

**Основные возможности:**
- Массовое исправление `indexing_threshold` для всех коллекций
- Настройка `vacuum_min_vector_number = 100`
- Поддержка dry-run режима для тестирования
- Генерация отчетов о результатах операций
- Простой CLI интерфейс

**Примеры использования:**

```bash
# Базовое исправление с подтверждением
python qdrant_fixer.py

# Автоматическое исправление без подтверждения
python qdrant_fixer.py --auto

# Тестовый режим
python qdrant_fixer.py --dry-run

# Исправление с конкретным threshold
python qdrant_fixer.py --threshold 5

# Использование с параметрами подключения
python qdrant_fixer.py --url http://my-qdrant:6333 --api-key my-key --auto
```

## ⚙️ Конфигурация

### Переменные окружения

Скрипты поддерживают следующие переменные окружения:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `QDRANT_URL` | URL для подключения к Qdrant | `http://localhost:6333` |
| `QDRANT_API_KEY` | API ключ для аутентификации | не используется |

### Приоритет настроек

1. **Аргументы командной строки** (имеют наивысший приоритет)
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

4. **Ошибки при исправлении**:
   ```bash
   ❌ Ошибка при исправлении коллекции: Collection not found
   ```
   **Решение:**
   - Используйте `--dry-run` для тестирования
   - Проверьте логи в консоли
   - Убедитесь в корректности названий коллекций

### Отладка

Для отладки используйте следующие подходы:

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

## 📝 Зависимости

Основные зависимости проекта указаны в `requirements.txt`:

- `qdrant-client>=1.6.0` - Официальный клиент Qdrant

Для установки зависимостей:
```bash
pip install -r requirements.txt
```

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](./LICENSE) для получения дополнительной информации.

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте [**чек-лист в QUICKSTART.md**](./QUICKSTART.md)
2. Используйте [`--dry-run`](./README.md#исправление-коллекций-qdrant_fixerpy) для тестирования
3. Проверьте отчеты в директории `reports/`
4. Запустите `test_imports.py` для диагностики
5. Используйте `--quiet` для минимального вывода при отладке

## 🛠️ Разработка

Для разработчиков:
- Прочитайте [CONTRIBUTING.md](./CONTRIBUTING.md) для guidelines
- Запустите `test_imports.py` для проверки структуры
- Используйте `--dry-run` для безопасного тестирования изменений

---

**⚠️ Важно**: Всегда используйте `--dry-run` для тестирования перед выполнением реальных операций на продакшн окружении.

**💡 Совет**: Начните с `qdrant_status.py` для анализа текущего состояния, затем используйте `qdrant_fixer.py --dry-run` для тестирования изменений.