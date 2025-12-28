# Qdrant-Ollama Docker Config

Краткое описание: Этот проект предоставляет готовую конфигурацию Docker Compose и сопутствующие скрипты для быстрого развертывания локальной среды RAG (Retrieval-Augmented Generation). Он объединяет Qdrant (векторная база данных) и Ollama (сервис для запуска локальных LLM) для индексации и анализа кодовых баз, таких как "Kilo Code".

## О проекте

Этот проект решает задачу создания локальной RAG-песочницы для экспериментов с кодовыми базами. Основные компоненты:

- **Qdrant**: Векторная база данных для хранения и поиска вложений (эмбеддингов) кода.
- **Ollama**: Сервис для запуска локальных языковых моделей (LLM), которые используются для генерации ответов.
- **Скрипты индексации**: Автоматизируют процесс тестирования индексации кодовой базы.
- **MCP Docker**: Набор утилит для упрощения управления Docker-контейнерами.

Вместе эти компоненты образуют RAG-пайплайн, который позволяет выполнять семантический поиск по коду и генерировать ответы на основе найденного контекста.

## Основные возможности

- Готовая связка Qdrant и Ollama в Docker для быстрого развертывания.
- Qdrant collection фикс для малых проектов (remote)
- Ollama local/Docker speed testing utilities for performance benchmarking
- Docker configuration for Qdrant and Ollama integration

These additions support development workflow improvements and provide essential documentation for AI/ML tool integration.

## Технологический стек

- Docker
- Docker Compose
- Qdrant
- Ollama
- Python/TypeScript/Bash для скриптов

## Начало работы

### Предварительные требования

- Установленный Docker
- Установленный Docker Compose

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-repo/kilocode-codebase-self-mcp.git
   cd kilocode-codebase-self-mcp
   ```

2. Настройте переменные окружения (если требуется) в файле `.env`.

3. Запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

## Лицензия

Этот проект лицензирован по лицензии MIT. Подробности см. в файле [LICENSE](LICENSE).