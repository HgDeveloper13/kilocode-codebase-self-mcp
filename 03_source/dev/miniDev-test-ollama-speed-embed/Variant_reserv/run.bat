@echo off
chcp 65001 > nul
REM Настройка переменных окружения для обхода прокси
set PYTHONIOENCODING=utf-8
set NO_PROXY=127.0.0.1,localhost
set HTTP_PROXY=
set HTTPS_PROXY=

echo ========================================
echo  Ollama Embedding Models Tester (Variant C)
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Проверка зависимостей
echo Checking Python dependencies...
pip show httpx >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        exit /b 1
    )
)

echo [OK] All dependencies installed
echo.

REM Проверка доступности Ollama
echo Checking Ollama availability...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not available at http://127.0.0.1:11434
    echo Make sure Docker container with Ollama is running
    echo [INFO] Continuing with test anyway...
) else (
    echo [OK] Ollama available
)
echo.

REM Запуск тестирования
echo ========================================
echo Starting tests...
echo ========================================
echo.

REM Запуск с конфигурацией (простой запуск)
python test_ollama_embeddings.py --config config.json

if errorlevel 1 (
    echo.
    echo [ERROR] Testing finished with error
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Testing completed successfully!
echo ========================================
echo.
echo Results saved in files:
echo    - JSON: ollama_embedding_test_*.json
echo    - CSV: ollama_embedding_test_*.csv
echo    - Markdown: ollama_embedding_test_*.md
echo    - HTML: ollama_embedding_test_*.html
echo.
echo Auto-exit in 5 seconds...
timeout /t 5 >nul 2>&1