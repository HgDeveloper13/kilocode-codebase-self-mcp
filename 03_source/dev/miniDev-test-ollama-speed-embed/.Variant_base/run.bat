@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
echo ================================================
echo  Ollama Embedding Models Speed Tester (Variant B)
echo ================================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден. Установите Python 3.10+
    exit /b 1
)

REM Создание виртуального окружения (опционально)
if not exist "venv" (
    echo [INFO] Создание виртуального окружения...
    python -m venv venv
    echo.
)

REM Активация виртуального окружения и установка зависимостей
echo [INFO] Установка зависимостей...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    pip install -r requirements.txt
)

echo.
echo [INFO] Запуск тестирования...
echo.

REM Запуск теста с конфигурацией
python test_ollama_speed_pro.py --config config.yaml

echo.
echo ================================================
echo [DONE] Тестирование завершено!
echo ================================================
pause