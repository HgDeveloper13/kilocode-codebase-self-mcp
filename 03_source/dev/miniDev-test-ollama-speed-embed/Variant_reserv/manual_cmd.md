# Ручной запуск variant test C

# Установка зависимостей
pip install -r requirements.txt

# Базовый запуск
python test_ollama_embeddings.py

# С конфигурацией
python test_ollama_embeddings.py --config config.json

# Проверка Docker
python test_ollama_embeddings.py --docker-check

# Windows автозапуск
run.bat
