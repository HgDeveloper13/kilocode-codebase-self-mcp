# Промты для запуска исправления Qdrant коллекций

## Промт 1: Локальный Qdrant (localhost:6333)

### Для AI ассистента:

```
Мне нужно проанализировать и исправить indexing_threshold для всех коллекций в локальном Qdrant.

**Подготовка:**
1. Перейди в директорию python/
2. Установи зависимости: pip install -r requirements.txt (если не установлены)
3. Создай .env файл с QDRANT_URL=http://localhost:6333 (или используй аргумент --url)

**Шаг 1: Безопасное тестирование (dry-run)**
Запусти проверку статуса всех коллекций:
```bash
cd python && python qdrant_status.py --url http://localhost:6333 --threshold 1
```

**Шаг 2: Тестовый прогон без изменений**
Запусти исправление в режиме dry-run:
```bash
cd python && python qdrant_fixer.py --url http://localhost:6333 --threshold 1 --dry-run
```

**Шаг 3: Реальное исправление**
Если тестовый прогон прошел успешно, выполни реальное исправление:
```bash
cd python && python qdrant_fixer.py --url http://localhost:6333 --threshold 1 --auto
```

**Шаг 4: Проверка результатов**
Проверь что все коллекции исправлены:
```bash
cd python && python qdrant_status.py --url http://localhost:6333 --threshold 1
```

Отчеты будут сохранены в директории python/reports/

Выполни все шаги последовательно и сообщи результаты каждого шага.
```

---

## Промт 2: Удаленный/Облачный Qdrant

### Для AI ассистента:

```
Мне нужно проанализировать и исправить indexing_threshold для всех коллекций в удаленном Qdrant.

**Подготовка:**
1. Перейди в директорию python/
2. Установи зависимости: pip install -r requirements.txt (если не установлены)
3. Создай .env файл с:
   - QDRANT_URL=https://your-qdrant-cloud-url.io:6333
   - QDRANT_API_KEY=your-api-key

Или используй аргументы командной строки --url и --api-key.

**Шаг 1: Безопасное тестирование (dry-run)**
Запусти проверку статуса всех коллекций:
```bash
cd python && python qdrant_status.py --url "https://YOUR_QDRANT_URL:6333" --api-key "YOUR_API_KEY" --threshold 1
```

**Шаг 2: Тестовый прогон без изменений**
Запусти исправление в режиме dry-run:
```bash
cd python && python qdrant_fixer.py --url "https://YOUR_QDRANT_URL:6333" --api-key "YOUR_API_KEY" --threshold 1 --dry-run
```

**Шаг 3: Реальное исправление**
Если тестовый прогон прошел успешно, выполни реальное исправление:
```bash
cd python && python qdrant_fixer.py --url "https://YOUR_QDRANT_URL:6333" --api-key "YOUR_API_KEY" --threshold 1 --auto
```

**Шаг 4: Проверка результатов**
Проверь что все коллекции исправлены:
```bash
cd python && python qdrant_status.py --url "https://YOUR_QDRANT_URL:6333" --api-key "YOUR_API_KEY" --threshold 1
```

Отчеты будут сохранены в директории python/reports/

**ВАЖНО:** Замени YOUR_QDRANT_URL и YOUR_API_KEY на реальные значения!

Выполни все шаги последовательно и сообщи результаты каждого шага.
```

---

## Краткая справка по скриптам

### qdrant_status.py - проверка статуса
| Аргумент | Описание |
|----------|----------|
| `--url` | URL для подключения к Qdrant |
| `--api-key` | API ключ для аутентификации |
| `--threshold` | Целевое значение indexing_threshold (по умолчанию: 1) |
| `--output` | Путь для сохранения отчета |
| `--quiet` | Минимальный вывод |

### qdrant_fixer.py - исправление коллекций
| Аргумент | Описание |
|----------|----------|
| `--url` | URL для подключения к Qdrant |
| `--api-key` | API ключ для аутентификации |
| `--threshold` | Новое значение indexing_threshold (по умолчанию: 1) |
| `--dry-run` | Тестовый режим без изменений |
| `--auto` | Автоматическое выполнение без подтверждения |

### Переменные окружения
- `QDRANT_URL` - URL для подключения к Qdrant
- `QDRANT_API_KEY` - API ключ для аутентификации

---

## Порядок выполнения

1. **status** → проверка текущего состояния
2. **fixer --dry-run** → безопасный тест
3. **fixer --auto** → реальное исправление
4. **status** → проверка результатов
