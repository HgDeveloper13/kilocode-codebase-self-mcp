#!/bin/bash
# Qdrant Status - Скрипт запуска для Linux/Mac
# Проверка статуса всех коллекций

echo "============================================================"
echo " QDRANT STATUS - Проверка статуса всех коллекций"
echo "============================================================"
echo

# Проверяем наличие Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python не найден! Установите Python 3"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "macOS: brew install python3"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Определяем команду Python (python3 или python)
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Используется Python: $PYTHON_CMD"

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip не найден! Установите pip"
    exit 1
fi

# Проверяем наличие зависимостей
$PYTHON_CMD -c "import qdrant_client" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Зависимости не установлены!"
    echo "Устанавливаю зависимости..."
    
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    $PIP_CMD install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка установки зависимостей"
        exit 1
    fi
fi

echo "✅ Проверка окружения завершена"
echo

# Запускаем qdrant_status с переданными параметрами
$PYTHON_CMD qdrant_status.py "$@"

EXIT_CODE=$?

echo
echo "============================================================"
echo " Операция завершена (код выхода: $EXIT_CODE)"
echo "============================================================"

# Если скрипт запущен не в интерактивном режиме, не ждем нажатия клавиши
if [[ $- == *i* ]]; then
    read -p "Нажмите Enter для продолжения..."
fi

exit $EXIT_CODE