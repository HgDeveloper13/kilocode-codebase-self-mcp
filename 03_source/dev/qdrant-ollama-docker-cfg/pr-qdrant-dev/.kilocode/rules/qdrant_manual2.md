Базовая установка Qdrant в Docker
Создание директории проекта
mkdir qdrant-docker && cd qdrant-docker
Создание docker-compose.yml
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
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  qdrant_storage:

Запуск Qdrant
docker-compose up -d
Проверка работы
# Проверка статуса
docker-compose ps

# Проверка API
curl http://localhost:6333/health

# Проверка логов
docker-compose logs qdrant
теперь Qdrant запущен и доступен по адресу http://localhost:6333

Стратегии хранения данных
Локальное хранение (разработка)
volumes:
  qdrant_storage:
    driver: local
	
	
	Настройка производительного хранения
# docker-compose.storage.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant-storage
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
      - ./config/storage.yaml:/qdrant/config/storage.yaml
    environment:
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_REQUESTS=200
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=4
    sysctls:
      - vm.max_map_count=262144
      - fs.file-max=65536
    ulimits:
      memlock:
        soft: -1
        hard: -1
    restart: unless-stopped

volumes:
  qdrant_storage:
    driver: local
    driver_opts:
      type: none
      o: bind,noatime,nodiratime
      device: /opt/qdrant/storage

Конфигурация хранения
# config/storage.yaml
storage:
  storage_path: /qdrant/storage
  
  # Настройки производительности
  performance:
    max_search_requests: 200
    max_optimization_threads: 4
    max_indexing_threads: 4
    
  # Настройки WAL (Write-Ahead Log)
  wal:
    wal_capacity_mb: 32
    wal_segments_ahead: 2
    
  # Настройки снапшотов
  snapshots:
    snapshots_path: /qdrant/snapshots
    
  # Настройки кэша
  cache:
    cache_size_mb: 1024

Резервное копирование
#!/bin/bash
# backup-qdrant.sh

BACKUP_DIR="/backup/qdrant"
QDRANT_DATA="/opt/qdrant/storage"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание снапшота
docker exec qdrant-storage curl -X POST "http://localhost:6333/collections/my_collection/snapshots"

# Копирование данных
rsync -av --delete $QDRANT_DATA/ $BACKUP_DIR/$DATE/

# Сжатие архива
tar -czf $BACKUP_DIR/qdrant_backup_$DATE.tar.gz -C $BACKUP_DIR $DATE

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "qdrant_backup_*.tar.gz" -mtime +7 -delete
Оптимизация производительности
Настройки для высоких нагрузок
# docker-compose.performance.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant-performance
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
      - ./config/performance.yaml:/qdrant/config/production.yaml
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_REQUESTS=500
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=4
      - QDRANT__STORAGE__PERFORMANCE__MAX_INDEXING_THREADS=4
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
    restart: unless-stopped
    sysctls:
      - net.core.somaxconn=65535
      - vm.max_map_count=262144

volumes:
  qdrant_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qdrant/storage
      
Рекомендации по производительности
Параметр	Рекомендуемое значение	Описание
max_search_requests	100-500	Максимальное количество одновременных поисковых запросов
max_optimization_threads	2-4	Количество потоков для оптимизации индексов
hnsw_config.m	16-32	Количество связей в графе HNSW
hnsw_config.ef_construct	100-200	Параметр точности построения индекса
Интеграция с Python
Установка клиента
pip install qdrant-client
Базовое подключение
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# Подключение к Qdrant
client = QdrantClient(host="localhost", port=6333)

# Создание коллекции
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
)

# Добавление векторов
points = [
    PointStruct(
        id=1,
        vector=np.random.rand(128).tolist(),
        payload={"text": "Пример документа 1"}
    ),
    PointStruct(
        id=2,
        vector=np.random.rand(128).tolist(),
        payload={"text": "Пример документа 2"}
    )
]

client.upsert(collection_name="my_collection", points=points)
Поиск по векторам
# Поиск похожих векторов
search_result = client.search(
    collection_name="my_collection",
    query_vector=np.random.rand(128).tolist(),
    limit=5
)

print("Найденные результаты:")
for result in search_result:
    print(f"ID: {result.id}, Score: {result.score}")
    print(f"Payload: {result.payload}")
Продвинутый пример с фильтрацией
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Поиск с фильтрацией
search_result = client.search(
    collection_name="my_collection",
    query_vector=np.random.rand(128).tolist(),
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="technology")
            )
        ]
    ),
    limit=10
)
Мониторинг и логирование
Добавление Prometheus метрик
# docker-compose.monitoring.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant-monitored
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__ENABLE_CORS=true
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: qdrant-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: qdrant-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_storage:/var/lib/grafana
    restart: unless-stopped

volumes:
  qdrant_storage:
  grafana_storage:
Конфигурация Prometheus
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: '/metrics'
    scrape_interval: 5s
Решение проблем
Частые проблемы и решения
Проблема: Qdrant не запускается
Решение: Проверьте логи: docker-compose logs qdrant

Проблема: Медленный поиск
Решение: Увеличьте max_search_requests и оптимизируйте HNSW параметры

Проблема: Нехватка памяти
Решение: Увеличьте лимиты памяти в Docker и оптимизируйте размер индекса

Полезные команды для диагностики
# Проверка статуса контейнера
docker-compose ps

# Просмотр логов
docker-compose logs -f qdrant

# Проверка использования ресурсов
docker stats qdrant

# Проверка API
curl http://localhost:6333/collections

# Проверка метрик
curl http://localhost:6333/metrics
Лучшие практики
Безопасность
Используйте HTTPS в production
Настройте аутентификацию
Ограничьте доступ к API
Регулярно обновляйте образы
Масштабирование
Используйте кластеры для больших нагрузок
Настройте репликацию данных
Мониторьте производительность
Планируйте резервное копирование
Оптимизация
Выберите правильные параметры HNSW
Настройте размеры индексов
Используйте SSD для хранения
Оптимизируйте размеры векторов
Обслуживание
Регулярно создавайте бэкапы
Мониторьте логи и метрики
Тестируйте обновления на staging
Документируйте конфигурации