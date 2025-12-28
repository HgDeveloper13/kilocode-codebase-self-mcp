#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации использования модуля конфигурации.
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту в sys.path для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .config_loader import (
    config_loader,
    load_config,
    get_qdrant_config,
    get_qdrant_url,
    get_qdrant_api_key,
    ConfigError
)


def test_config_loading():
    """Тестирование загрузки конфигурации."""
    print("=== Тестирование загрузки конфигурации ===\n")
    
    try:
        # Тест 1: Загрузка из файла
        print("1. Загрузка конфигурации из файла:")
        config = load_config()
        print(f"   URL: {get_qdrant_url()}")
        print(f"   API Key: {get_qdrant_api_key()[:10]}...")
        print("   ✓ Конфигурация загружена успешно\n")
        
        # Тест 2: Проверка глобального экземпляра
        print("2. Проверка глобального экземпляра:")
        qdrant_config = get_qdrant_config()
        print(f"   URL: {qdrant_config['url']}")
        print(f"   API Key: {qdrant_config['api_key'][:10]}...")
        print("   ✓ Глобальный экземпляр работает\n")
        
        # Тест 3: Приоритет переменных окружения
        print("3. Тест приоритета переменных окружения:")
        original_url = os.getenv('QDRANT_URL')
        original_api_key = os.getenv('QDRANT_API_KEY')
        
        # Устанавливаем переменные окружения
        test_url = "https://test.example.com:6333"
        test_api_key = "test_api_key_1234567890"
        
        os.environ['QDRANT_URL'] = test_url
        os.environ['QDRANT_API_KEY'] = test_api_key
        
        # Перезагружаем конфигурацию
        config_loader._config = None  # Сбрасываем кэш
        config = load_config()
        
        print(f"   URL: {get_qdrant_url()}")
        print(f"   API Key: {get_qdrant_api_key()[:10]}...")
        
        # Проверяем, что переменные окружения имеют приоритет
        assert get_qdrant_url() == test_url, "URL из переменной окружения не был применен"
        assert get_qdrant_api_key() == test_api_key, "API Key из переменной окружения не был применен"
        print("   ✓ Переменные окружения имеют приоритет\n")
        
        # Восстанавливаем исходные значения
        if original_url:
            os.environ['QDRANT_URL'] = original_url
        else:
            os.environ.pop('QDRANT_URL', None)
            
        if original_api_key:
            os.environ['QDRANT_API_KEY'] = original_api_key
        else:
            os.environ.pop('QDRANT_API_KEY', None)
        
        # Тест 4: Валидация ошибок
        print("4. Тест валидации ошибок:")
        try:
            # Создаем загрузчик с несуществующим файлом
            invalid_loader = config_loader.__class__("/nonexistent/path/config.json")
            invalid_loader.load()
            print("   ✗ Ожидалась ошибка, но её не было")
        except ConfigError as e:
            print(f"   ✓ Ожидаемая ошибка: {e}")
        
        print("\n=== Все тесты пройдены успешно! ===")
        
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)