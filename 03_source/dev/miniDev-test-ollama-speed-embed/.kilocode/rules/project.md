# Структура проекта miniDev-test-ollama-speed-embed

Проект для тестирования моделей embedding в Ollama, запущенной в Docker Desktop на слабом железе.

## Структура директорий и файлов

- `promt_dev.md`: Инструкции по созданию Python скрипта для тестирования моделей embedding Ollama
- `promt_run_for_kilocode_ai_assistent.md`: Команды для запуска тестирования (Variant_base и Variant_reserv)
- `.Variant_base/`: Базовый вариант тестирования моделей LLM Embeddings
- `.Variant_reserv/`: Резервный вариант тестирования
- `Reports/`: Отчеты по результатам тестирования
  - `comparative_analysis_report.md`: Сравнительный анализ
  - `embedding_models_explanation.md`: Объяснение моделей embedding
  - `variant_c_explanation_ru.md`: Объяснение варианта C на русском

## Рекомендации

- Использовать слабое железо с учетом задержек Ollama
- Тестировать модели из списка в promt_dev.md
- Адрес Ollama: http://localhost:11434/
