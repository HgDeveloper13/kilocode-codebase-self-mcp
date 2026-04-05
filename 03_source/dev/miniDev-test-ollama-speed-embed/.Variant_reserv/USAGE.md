# Руководство по использованию

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Проверка Docker

Убедитесь, что контейнер Ollama запущен:

```bash
# Windows
run.bat --docker-check

# Linux/Mac
python test_ollama_embeddings.py --docker-check
```

### 3. Запуск тестирования

```bash
# Windows - автоматический запуск
run.bat

# Linux/Mac - прямой запуск
python test_ollama_embeddings.py
```

## Примеры команд

### Базовое тестирование

```bash
# Тестирование всех моделей (по умолчанию 5 тестов на модель)
python test_ollama_embeddings.py

# С конфигурационным файлом
python test_ollama_embeddings.py --config config.json
```

### Выбор моделей

```bash
# Тестирование конкретных моделей
python test_ollama_embeddings.py --models all-minilm:l6-v2 qwen3-embedding:0.6b-q8_0

# Только быстрые модели
python test_ollama_embeddings.py --models all-minilm:l6-v2 embeddinggemma:300m-qat-q4_0
```

### Настройка параметров

```bash
# Увеличить количество тестов
python test_ollama_embeddings.py --tests-per-model 10

# Увеличить таймаут для слабого железа
python test_ollama_embeddings.py --timeout 300

# Изменить URL Ollama
python test_ollama_embeddings.py --url http://localhost:11435
```

### Сохранение результатов

```bash
# Сохранить в конкретную директорию
python test_ollama_embeddings.py --output-dir ./results

# С verbose логированием
python test_ollama_embeddings.py -v --output-dir ./detailed_results
```

### Комбинированные команды

```bash
# Полное тестирование с максимальной детализацией
python test_ollama_embeddings.py \
  --tests-per-model 10 \
  --timeout 300 \
  --output-dir ./full_test \
  -v

# Быстрое тестирование топ-3 моделей
python test_ollama_embeddings.py \
  --models all-minilm:l6-v2 qwen3-embedding:0.6b-q8_0 embeddinggemma:300m-qat-q4_0 \
  --tests-per-model 3 \
  --timeout 120
```

## Работа с Docker

### Проверка статуса

```bash
# Проверить статус контейнера
docker ps | grep ollama

# Проверить через скрипт
python test_ollama_embeddings.py --docker-check
```

### Управление контейнером

```bash
# Запустить контейнер
docker start ollama

# Остановить контейнер
docker stop ollama

# Перезапустить контейнер
docker restart ollama

# Просмотр логов
docker logs ollama
```

### Работа с моделями

```bash
# Список моделей в контейнере
docker exec ollama ollama list

# Загрузить новую модель
docker exec ollama ollama pull qwen3-embedding:0.6b-q8_0

# Удалить модель
docker exec ollama ollama rm qwen3-embedding:0.6b-q8_0
```

## Интерпретация результатов

### Консольный вывод

После завершения тестирования вы увидите:

1. **Сводную таблицу** с общей статистикой
2. **Топ-5 самых быстрых моделей** с метриками
3. **Пути к сохраненным файлам** результатов

### Файлы результатов

#### JSON файл
Содержит полные данные всех тестов:
- Конфигурация тестирования
- Статус Docker
- Детальные результаты каждого теста
- Агрегированная статистика
- Рейтинги моделей

#### CSV файл
Табличный формат для анализа:
- Легко импортируется в Excel/Google Sheets
- Содержит основные метрики
- Удобен для построения графиков

#### Markdown файл
Читаемый отчет:
- Форматированные таблицы
- Рейтинги по скорости и качеству
- Детальные результаты по каждой модели

#### HTML файл
Интерактивный отчет:
- Стилизованные таблицы
- Цветовая индикация статусов
- Готов для публикации

## Метрики производительности

### Основные метрики

- **Avg Duration**: Среднее время выполнения запроса
- **Min/Max Duration**: Диапазон времени выполнения
- **Median Duration**: Медианное значение (устойчиво к выбросам)
- **Std Dev**: Стандартное отклонение (стабильность)
- **Embedding Dim**: Размерность выходного вектора
- **Tokens/sec**: Приблизительная скорость обработки

### Интерпретация

**Быстрая модель**:
- Низкое среднее время (< 0.5s)
- Низкое стандартное отклонение (< 0.1s)
- Стабильные результаты

**Качественная модель**:
- Высокая размерность вектора (> 512)
- Стабильные результаты
- Приемлемая скорость

**Оптимальная модель**:
- Баланс между скоростью и качеством
- Низкое стандартное отклонение
- Подходящая размерность для задачи

## Рекомендации для слабого железа

### Оптимальные настройки

```json
{
  "timeout": 300,
  "tests_per_model": 3,
  "warmup_requests": 1,
  "interval_between_tests": 5
}
```

### Выбор моделей

Для слабого железа рекомендуются легкие модели:

1. `all-minilm:l6-v2` (45 MB) - самая быстрая
2. `embeddinggemma:300m-qat-q4_0` (238 MB) - хороший баланс
3. `qwen3-embedding:0.6b-q8_0` (639 MB) - качественная

Избегайте тяжелых моделей:
- `qwen3-embedding:0.6b-fp16` (1.2 GB)
- `bge-m3:567m-fp16` (1.2 GB)

### Команда для слабого железа

```bash
python test_ollama_embeddings.py \
  --models all-minilm:l6-v2 embeddinggemma:300m-qat-q4_0 \
  --tests-per-model 3 \
  --timeout 300 \
  --interval-between-tests 5
```

## Устранение проблем

### Проблема: Таймауты

**Симптомы**: Запросы завершаются по таймауту

**Решение**:
```bash
python test_ollama_embeddings.py --timeout 300
```

### Проблема: Нестабильные результаты

**Симптомы**: Высокое стандартное отклонение

**Решение**:
```bash
# Увеличить паузу между тестами
python test_ollama_embeddings.py --interval-between-tests 5

# Увеличить количество warmup запросов
# (требует изменения в config.json: "warmup_requests": 2)
```

### Проблема: Контейнер не отвечает

**Симптомы**: Cannot connect to Ollama

**Решение**:
```bash
# Перезапустить контейнер
docker restart ollama

# Проверить логи
docker logs ollama

# Проверить порт
netstat -an | findstr 11434
```

### Проблема: Модель не найдена

**Симптомы**: Model not found error

**Решение**:
```bash
# Проверить доступные модели
docker exec ollama ollama list

# Загрузить модель
docker exec ollama ollama pull <model-name>
```

## Продвинутое использование

### Создание пользовательской конфигурации

Создайте файл `my_config.json`:

```json
{
  "ollama_url": "http://localhost:11434",
  "timeout": 240,
  "tests_per_model": 7,
  "models": [
    "all-minilm:l6-v2",
    "qwen3-embedding:0.6b-q8_0"
  ],
  "output_dir": "./my_results"
}
```

Запустите:
```bash
python test_ollama_embeddings.py --config my_config.json
```

### Автоматизация тестирования

Создайте скрипт для регулярного тестирования:

**Windows (test_schedule.bat)**:
```batch
@echo off
python test_ollama_embeddings.py --output-dir ./daily_tests/%date:~-4,4%%date:~-7,2%%date:~-10,2%
```

**Linux/Mac (test_schedule.sh)**:
```bash
#!/bin/bash
python test_ollama_embeddings.py --output-dir ./daily_tests/$(date +%Y%m%d)
```

### Сравнение результатов

Используйте CSV файлы для сравнения:

```python
import pandas as pd

# Загрузить результаты
df1 = pd.read_csv('ollama_embedding_test_20241224_100000.csv')
df2 = pd.read_csv('ollama_embedding_test_20241224_150000.csv')

# Сравнить средние времена
comparison = pd.merge(
    df1[['Model', 'Avg Duration (s)']],
    df2[['Model', 'Avg Duration (s)']],
    on='Model',
    suffixes=('_morning', '_afternoon')
)
print(comparison)
```

## Лучшие практики

1. **Всегда делайте warmup**: Первый запрос обычно медленнее
2. **Используйте достаточно тестов**: Минимум 5 для статистической значимости
3. **Учитывайте нагрузку системы**: Закройте другие приложения
4. **Сохраняйте результаты**: Для последующего анализа и сравнения
5. **Тестируйте в одинаковых условиях**: Для корректного сравнения
6. **Мониторьте ресурсы**: Используйте `docker stats ollama`

## Дополнительные ресурсы

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Embedding Models Guide](https://ollama.com/blog/embedding-models)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)