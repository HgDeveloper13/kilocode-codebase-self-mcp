# Текущей контекст проекта RAG

## Расположение текущего проекта

> qdrant-ollama-docker-cfg\pr-core-train-to-ollama-qdrant

- Только в данной папке проводим изменения!

## Работаем на стеке

> C# (.NET 8, ASP.NET 8) + Redis (8.6.2-alpine) + Nginx (1.28.1-alpine) + Ollama (0.13.5) + Qdrant (v1.16.2)

## Текущий статус проекта

- Сборка успешна завершена проект контейнер успешно запущен
- Ollama успешно смонтирована с готовым уже volume, есть модели embeddings.
- Ollama успешно генерировала в прошлой верси RAG (nginx to ollama, qdrant).
- Проверка gateway, нужно убедится что он верно получает запросы для генерации эмбедингов которые nginx ему направляет.

## Текущая задача по проекту

- Исправить nginx.conf (qdrant-ollama-docker-cfg\pr-core-train-to-ollama-qdrant\nginx\nginx.conf), чтобы трафик направлялся на Ollama, мимо gateway, таким образом поймем, что Ollama работает исправно, а проблема текущая в gateway!
