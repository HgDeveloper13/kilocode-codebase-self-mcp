#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QDRANT STATUS CHECKER
Скрипт для проверки статуса всех коллекций в Qdrant
"""

import sys
import os
from datetime import datetime

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем конфигурационный модуль
from .config.config_loader import (
    get_qdrant_url, 
    get_qdrant_api_key,
    ConfigError
)
from qdrant_manager import QdrantConfigManager


def print_header(title: str):
    """Печать заголовка"""
    print("\n" + "=" * 60)
    print(f"STATUS: {title}")
    print("=" * 60)

def print_collection_info(name: str, info: dict, index: int, total: int):
    """Печать информации о коллекции"""
    if 'error' in info:
        print(f"  {index:2d}/{total} [ERROR] {name:20} | {info['error']}")
        return
    
    points = info.get('points', 0)
    indexed = info.get('indexed', 0)
    threshold = info.get('threshold', 'N/A')
    
    # Вычисляем процент индексации
    if points > 0:
        indexed_percent = (indexed / points) * 100
        indexed_str = f"{indexed:6} ({indexed_percent:5.1f}%)"
    else:
        indexed_str = f"{indexed:6} (0.0%)"
    
    # Определяем статус коллекции
    if threshold == 1:
        status_icon = "[OK]"
        status_text = "OPTIMIZED"
    elif threshold > 1:
        status_icon = "[WARN]"
        status_text = "NEEDS_FIX"
    else:
        status_icon = "[INFO]"
        status_text = f"THRESHOLD: {threshold}"
    
    print(f"  {index:2d}/{total} {status_icon} {name:20} | {points:6} points | {indexed_str} | {status_text}")

def generate_summary(status: dict):
    """Генерация сводки"""
    total_collections = len(status)
    collections_with_errors = sum(1 for info in status.values() if 'error' in info)
    
    # Статистика по коллекциям
    valid_collections = {k: v for k, v in status.items() if 'error' not in v}
    
    total_points = sum(info.get('points', 0) for info in valid_collections.values())
    total_indexed = sum(info.get('indexed', 0) for info in valid_collections.values())
    
    optimized_collections = sum(1 for info in valid_collections.values() if info.get('threshold', 0) == 1)
    needs_fix_collections = sum(1 for info in valid_collections.values() if info.get('threshold', 0) > 1)
    
    return {
        'total_collections': total_collections,
        'collections_with_errors': collections_with_errors,
        'valid_collections': len(valid_collections),
        'total_points': total_points,
        'total_indexed': total_indexed,
        'optimized_collections': optimized_collections,
        'needs_fix_collections': needs_fix_collections
    }

def main():
    """Главная функция"""
    try:
        print_header("QDRANT COLLECTIONS STATUS CHECKER")
        print(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Загружаем конфигурацию из конфигурационного модуля
        print("🔧 Загрузка конфигурации...")
        qdrant_url = get_qdrant_url()
        qdrant_api_key = get_qdrant_api_key()
        
        print(f"✅ Конфигурация загружена:")
        print(f"   URL: {qdrant_url}")
        print(f"   API Key: {qdrant_api_key[:10]}...")
        
        # Создаем менеджер
        manager = QdrantConfigManager(qdrant_url, qdrant_api_key)
        
        print(f"\nFetching status of all collections...")
        status = manager.get_collections_status()
        
        if not status:
            print("ERROR: No collections found or connection error")
            return 1
        
        # Печатаем детали по каждой коллекции
        print_header("COLLECTIONS STATUS")
        collections = list(status.items())
        for i, (name, info) in enumerate(collections, 1):
            print_collection_info(name, info, i, len(collections))
        
        # Генерируем сводку
        summary = generate_summary(status)
        
        print_header("SUMMARY")
        print(f"Total collections: {summary['total_collections']}")
        print(f"Successful: {summary['valid_collections']}")
        print(f"With errors: {summary['collections_with_errors']}")
        
        if summary['valid_collections'] > 0:
            overall_indexed = (summary['total_indexed'] / summary['total_points'] * 100) if summary['total_points'] > 0 else 0
            print(f"Total points: {summary['total_points']:,}")
            print(f"Indexed: {summary['total_indexed']:,} ({overall_indexed:.1f}%)")
            
            print(f"\nOptimization status:")
            print(f"   [OK] Optimized: {summary['optimized_collections']}")
            print(f"   [WARN] Needs fix: {summary['needs_fix_collections']}")
            
            if summary['needs_fix_collections'] > 0:
                print(f"\nRECOMMENDATION: Run python/check_and_fix.py for automatic fixing")
        
        # Сохраняем отчет в файл
        report_file = f"qdrant_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"QDRANT COLLECTIONS STATUS REPORT\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL: {qdrant_url}\n\n")
            
            f.write(f"SUMMARY:\n")
            f.write(f"- Total collections: {summary['total_collections']}\n")
            f.write(f"- Successful: {summary['valid_collections']}\n")
            f.write(f"- With errors: {summary['collections_with_errors']}\n")
            f.write(f"- Optimized: {summary['optimized_collections']}\n")
            f.write(f"- Needs fix: {summary['needs_fix_collections']}\n\n")
            
            f.write(f"COLLECTIONS DETAILS:\n")
            for i, (name, info) in enumerate(status.items(), 1):
                if 'error' in info:
                    f.write(f"{i:2d}. {name} - ERROR: {info['error']}\n")
                else:
                    f.write(f"{i:2d}. {name} - {info.get('points', 0)} points, threshold: {info.get('threshold', 'N/A')}\n")
        
        print(f"\nReport saved to: {report_file}")
        
        return 0
        
    except ConfigError as e:
        print(f"🚨 Ошибка конфигурации: {e}")
        print("\n💡 Подсказка:")
        print("   - Проверьте файл .config/config.json")
        print("   - Или установите переменные окружения:")
        print("     export QDRANT_URL='ваш_url'")
        print("     export QDRANT_API_KEY='ваш_api_key'")
        return 1
        
    except KeyboardInterrupt:
        print(f"\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)