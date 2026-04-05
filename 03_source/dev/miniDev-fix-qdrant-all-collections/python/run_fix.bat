@echo off
REM Qdrant Fixer - Скрипт запуска для Windows
REM Массовое исправление indexing_threshold коллекций

echo ============================================================
echo  QDRANT FIXER - Массовое исправление indexing_threshold
echo ============================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python и добавьте его в PATH
    echo Скачать Python можно с: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Проверяем наличие зависимостей
python -c "import qdrant_client" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Зависимости не установлены!
    echo Устанавливаю зависимости...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
)

echo ✅ Проверка окружения завершена
echo.

REM Запускаем qdrant_fixer с переданными параметрами
python qdrant_fixer.py %*

echo.
echo ============================================================
echo  Операция завершена
echo ============================================================
pause