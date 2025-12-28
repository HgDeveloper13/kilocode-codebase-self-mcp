# Qdrant в Docker, для Kilocode Codebase Indexing

## Подготовка
docker pull qdrant/qdrant:latest

## Docker контейнер первый раз 
docker-compose down
docker volume ls
docker volume rm qdrant_storage
docker-compose up -d
docker logs qdrant

## Перезапуск Docker контейнера
docker-compose down && docker-compose up -d