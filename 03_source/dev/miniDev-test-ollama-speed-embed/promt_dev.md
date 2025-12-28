# Тестирование моделей в Ollama, ollama расположена в docker

В папку "miniDev-test-ollama-speed-embed\variant test <VARIANT>", добавь скрипт, написанно профессионально, согласно последним стандартам разработки python для тестирования ollama llm embedding моделей , ollama запущен локально в doker desctop!

С учетом, что железо слабое! Ожидание может занимать минуты работы ollama!

Делаем скрипт без ожидания и подтверждения для начала теста!

Адресс ollama:
    http://localhost:11434/

Пример запроса к ollam в docker через терминал:
    docker exec ollama ollama list

Список моделей для тестирования:
    NAME                                ID              SIZE      MODIFIED
        embeddinggemma:300m-qat-q8_0        e84a7acc2394    338 MB    3 weeks ago
        qwen3-embedding:0.6b-fp16           67a7592a8852    1.2 GB    3 weeks ago
        qwen3-embedding:0.6b-q8_0           ac6da0dfba84    639 MB    3 weeks ago
        embeddinggemma:300m-qat-q4_0        101341d65c2c    238 MB    3 weeks ago
        all-minilm:22m-l6-v2-fp16           1b226e2802db    45 MB     3 weeks ago
        bge-m3:567m-fp16                    790764642607    1.2 GB    3 weeks ago
        embeddinggemma:300m-bf16            85462619ee72    621 MB    3 weeks ago
        nomic-embed-text:137m-v1.5-fp16     0a109f422b47    274 MB    3 weeks ago
        qllama/multilingual-e5-small:f16    3c8dead9831d    241 MB    3 weeks ago
        all-minilm:l6-v2                    1b226e2802db    45 MB     4 weeks ago
