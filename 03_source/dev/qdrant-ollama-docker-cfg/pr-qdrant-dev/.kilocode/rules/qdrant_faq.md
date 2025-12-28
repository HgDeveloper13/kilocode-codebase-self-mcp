# Пошаговое руководство по установке Qdrant

На основе анализа предоставленных документов, вот сводная инструкция по установке и базовой настройке Qdrant.

#### Шаг 1: Предварительные требования

Единственным обязательным требованием для запуска Qdrant является установленный и запущенный **Docker**.

#### Шаг 2: Установка Qdrant с использованием Docker

Существует два основных способа запуска Qdrant с помощью Docker.

**Способ 1: Простая команда `docker run` (для быстрого старта)**

Этот метод подходит для быстрого запуска и тестирования.

1.  **Загрузите последнюю версию образа Qdrant:**
    ```bash
    docker pull qdrant/qdrant
    ```

2.  **Запустите контейнер:**
    Эта команда запускает Qdrant и связывает локальную папку `qdrant_storage` для постоянного хранения данных.

    ```bash
    docker run -p 6333:6333 -p 6334:6334 \
        -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
        qdrant/qdrant
    ```
    *   `-p 6333:6333`: Пробрасывает порт для REST API и веб-интерфейса.
    *   `-p 6334:6334`: Пробрасывает порт для gRPC API.
    *   `-v ...`: Создает постоянное хранилище в папке `qdrant_storage` в вашем текущем каталоге.

**Способ 2: Использование Docker Compose (Рекомендуется)**

Этот метод более удобен для управления и является рекомендуемым.

1.  **Создайте директорию для вашего проекта:**
    ```bash
    mkdir qdrant-docker && cd qdrant-docker
    ```

2.  **Создайте файл `docker-compose.yml`** со следующим содержимым:
    ```yaml
    version: '3.8'

    services:
      qdrant:
        image: qdrant/qdrant:latest
        container_name: qdrant
        ports:
          - "6333:6333"  # HTTP API
          - "6334:6334"  # gRPC API
        volumes:
          - qdrant_storage:/qdrant/storage
        restart: unless-stopped

    volumes:
      qdrant_storage:
    ```

3.  **Запустите Qdrant в фоновом режиме:**
    ```bash
    docker-compose up -d
    ```

#### Шаг 3: Проверка работы

После запуска убедитесь, что Qdrant работает корректно.

1.  **Проверьте статус контейнера:**
    *   Для Docker Compose: `docker-compose ps`
    *   Для `docker run`: `docker ps`

2.  **Проверьте API здоровья:**
    Выполните команду `curl http://localhost:6333/health`. Вы должны получить ответ с информацией о статусе.

3.  **Откройте веб-интерфейс:**
    Перейдите по адресу `http://localhost:6333/dashboard` в вашем браузере.

#### Шаг 4: Установка клиентских библиотек (SDK)

Для взаимодействия с Qdrant из вашего приложения необходимо установить соответствующий клиент.

*   **Python:**
    ```bash
    pip install qdrant-client[fastembed]
    ```
    
*   **JavaScript / TypeScript:**
    ```bash
    npm install @qdrant/js-client-rest
    ```

*   **Rust:**
    ```bash
    cargo add qdrant-client
    ```

*   **Go:**
    ```bash
    go get github.com/qdrant/go-client
    ```

*   **.NET:**
    ```bash
    dotnet add package Qdrant.Client
    ```

После выполнения этих шагов ваш экземпляр Qdrant будет готов к работе.