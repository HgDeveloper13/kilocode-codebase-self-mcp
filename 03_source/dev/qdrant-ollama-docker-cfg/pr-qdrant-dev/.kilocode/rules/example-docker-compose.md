services:
  qdrant:
    image: qdrant/qdrant:latest
    restart: always
    container_name: qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage
      # Файлы конфигурации монтируются, но переменные окружения имеют приоритет
      - ./config.yaml:/qdrant/config/production.yaml
      - ./storage.yaml:/qdrant/config/storage.yaml
    environment:
      # --- Сервисные настройки ---
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__ENABLE_CORS=true
      - QDRANT__TELEMETRY_DISABLED=true

      # --- Настройки хранилища (Обновлено) ---
      - QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage
      - QDRANT__STORAGE__SNAPSHOTS_PATH=/qdrant/snapshots
      - QDRANT__STORAGE__ON_DISK_PAYLOAD=false # <--- Обновлено: false (payload в RAM)
      - QDRANT__STORAGE__ON_DISK_VECTORS=false # <--- Добавлено: false (вектора в RAM)
      - QDRANT__STORAGE__STRICT_MODE=false # <--- Добавлено

      # --- Настройки производительности ---
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=0
      - QDRANT__STORAGE__PERFORMANCE__OPTIMIZER_CPU_BUDGET=0
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_REQUESTS=200
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=4

      # --- Настройки оптимизаторов (Обновлено) ---
      - QDRANT__STORAGE__OPTIMIZERS__DELETED_THRESHOLD=0.1 # <--- Обновлено: 0.1
      - QDRANT__STORAGE__OPTIMIZERS__VACUUM_MIN_VECTOR_NUMBER=100 # <--- Обновлено: 100
      - QDRANT__STORAGE__OPTIMIZERS__FLUSH_INTERVAL_SEC=5
      - QDRANT__STORAGE__OPTIMIZERS__FULL_SCAN_THRESHOLD=10 # <--- Добавлено

      # --- Настройки HNSW индекса (Обновлено) ---
      - QDRANT__STORAGE__HNSW_INDEX__M=16
      - QDRANT__STORAGE__HNSW_INDEX__EF_CONSTRUCT=100
      - QDRANT__STORAGE__HNSW_INDEX__ON_DISK=false # <--- Добавлено: false (индекс в RAM)
      - QDRANT__STORAGE__HNSW_INDEX__FULL_SCAN_THRESHOLD_KB=10000 # Оставлено из эталона
      - QDRANT__STORAGE__HNSW_INDEX__FULL_SCAN_THRESHOLD=10 # <--- Добавлено
      - QDRANT__STORAGE__HNSW_INDEX__MAX_INDEXING_THREADS=0

      # --- WAL (Обновлено) ---
      - QDRANT__WAL__WAL_CAPACITY_MB=32 # <--- Добавлено

      # --- Кластеризация ---
      - QDRANT__CLUSTER__ENABLED=false

    command: ./qdrant --config-path /qdrant/config/production.yaml

volumes:
  qdrant_storage: