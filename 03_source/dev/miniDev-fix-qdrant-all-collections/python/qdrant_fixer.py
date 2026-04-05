#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant Fixer - Простой скрипт для массового исправления indexing_threshold

Основные функции:
- Массовое исправление indexing_threshold для всех коллекций
- Простой CLI интерфейс с argparse
- Поддержка переменных окружения QDRANT_URL, QDRANT_API_KEY
- Поддержка dry-run режима для тестирования
- Генерация отчетов о результатах

Использование:
    python qdrant_fixer.py [--url QDRANT_URL] [--api-key QDRANT_API_KEY] 
                          [--threshold THRESHOLD] [--dry-run] [--auto]

Переменные окружения:
    QDRANT_URL - URL для подключения к Qdrant (например: http://localhost:6333)
    QDRANT_API_KEY - API ключ для аутентификации (опционально)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError as e:
    print(f"❌ Ошибка импорта qdrant-client: {e}")
    print("Установите зависимости: pip install qdrant-client")
    sys.exit(1)


def load_config() -> Dict[str, Any]:
    """
    Загрузка конфигурации из переменных окружения
    
    Returns:
        Словарь с параметрами подключения к Qdrant
    """
    # Получаем параметры из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    qdrant_api_key = os.getenv('QDRANT_API_KEY', '')
    
    # Проверяем аргументы командной строки (они имеют приоритет)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--url', default=None, help='URL для подключения к Qdrant')
    parser.add_argument('--api-key', default=None, help='API ключ для аутентификации')
    
    # Парсим только эти аргументы, остальные будут обработаны позже
    temp_args, _ = parser.parse_known_args()
    
    if temp_args.url:
        qdrant_url = temp_args.url
    if temp_args.api_key:
        qdrant_api_key = temp_args.api_key
    
    return {
        'url': qdrant_url,
        'api_key': qdrant_api_key if qdrant_api_key else None,
        'timeout': 30
    }


def init_qdrant_client(config: Dict[str, Any]) -> QdrantClient:
    """
    Инициализация клиента Qdrant
    
    Args:
        config: Конфигурация подключения
        
    Returns:
        Инициализированный клиент Qdrant
        
    Raises:
        Exception: При ошибке подключения
    """
    try:
        if config['api_key']:
            client = QdrantClient(
                url=config['url'],
                api_key=config['api_key'],
                timeout=config['timeout']
            )
        else:
            client = QdrantClient(
                url=config['url'],
                timeout=config['timeout']
            )
        
        # Проверяем соединение
        client.get_collections()
        return client
        
    except Exception as e:
        raise Exception(f"Ошибка подключения к Qdrant: {e}")


def get_all_collections(client: QdrantClient) -> List[str]:
    """
    Получение списка всех коллекций
    
    Args:
        client: Клиент Qdrant
        
    Returns:
        Список имен коллекций
    """
    try:
        collections_info = client.get_collections()
        return [collection.name for collection in collections_info.collections]
    except Exception as e:
        print(f"❌ Ошибка получения списка коллекций: {e}")
        return []


def get_collection_info(client: QdrantClient, collection_name: str) -> Dict[str, Any]:
    """
    Получение информации о коллекции
    
    Args:
        client: Клиент Qdrant
        collection_name: Имя коллекции
        
    Returns:
        Словарь с информацией о коллекции
    """
    try:
        collection_info = client.get_collection(collection_name)
        
        # Извлекаем optimizer_config для получения indexing_threshold
        optimizer_config = getattr(collection_info.config, 'optimizer_config', {})
        indexing_threshold = getattr(optimizer_config, 'indexing_threshold', 'unknown')
        
        return {
            "name": collection_name,
            "vectors_count": collection_info.vectors_count,
            "indexed_vectors_count": collection_info.indexed_vectors_count,
            "indexing_threshold": indexing_threshold,
            "status": str(collection_info.status),
            "optimizer_config": optimizer_config,
            "error": None
        }
    except Exception as e:
        return {
            "name": collection_name,
            "error": str(e),
            "needs_fix": True
        }


def fix_collection_threshold(client: QdrantClient, collection_name: str, new_threshold: int = 1) -> bool:
    """
    Исправление indexing_threshold для одной коллекции
    
    Args:
        client: Клиент Qdrant
        collection_name: Имя коллекции
        new_threshold: Новое значение indexing_threshold
        
    Returns:
        True если исправление прошло успешно
    """
    try:
        optimizer_config = {
            "indexing_threshold": new_threshold,
            "vacuum_min_vector_number": 100
        }
        
        client.update_collection(
            collection_name=collection_name,
            optimizer_config=optimizer_config
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка исправления коллекции {collection_name}: {e}")
        return False


def fix_all_collections(client: QdrantClient, new_threshold: int = 1, dry_run: bool = False) -> Dict[str, bool]:
    """
    Массовое исправление indexing_threshold для всех коллекций
    
    Args:
        client: Клиент Qdrant
        new_threshold: Новое значение indexing_threshold
        dry_run: Режим тестирования без реальных изменений
        
    Returns:
        Словарь с результатами исправления для каждой коллекции
    """
    results = {}
    collections = get_all_collections(client)
    
    if not collections:
        print("⚠️  Коллекции не найдены")
        return results
    
    print(f"🔍 Найдено коллекций: {len(collections)}")
    print(f"🎯 Новый indexing_threshold: {new_threshold}")
    print(f"🧪 Dry run режим: {'ВКЛЮЧЕН' if dry_run else 'ВЫКЛЮЧЕН'}")
    print()
    
    for i, collection_name in enumerate(collections, 1):
        print(f"[{i}/{len(collections)}] Обрабатываю коллекцию: {collection_name}")
        
        # Получаем информацию о коллекции
        collection_info = get_collection_info(client, collection_name)
        
        if collection_info.get('error'):
            print(f"  ❌ Ошибка получения информации: {collection_info['error']}")
            results[collection_name] = False
            continue
        
        current_threshold = collection_info.get("indexing_threshold")
        vectors_count = collection_info.get('vectors_count', 0)
        
        print(f"  📊 Текущий threshold: {current_threshold}")
        print(f"  📈 Количество векторов: {vectors_count:,}")
        
        # Проверяем, нужно ли исправлять
        if current_threshold == new_threshold:
            print(f"  ✅ Threshold уже установлен правильно")
            results[collection_name] = True
            continue
        
        # Выполняем исправление
        if dry_run:
            print(f"  🔍 [DRY RUN] Будет изменен с {current_threshold} на {new_threshold}")
            results[collection_name] = True
        else:
            success = fix_collection_threshold(client, collection_name, new_threshold)
            results[collection_name] = success
            
            if success:
                print(f"  ✅ Исправлен успешно")
            else:
                print(f"  ❌ Ошибка при исправлении")
        
        print()
    
    return results


def generate_report(results: Dict[str, bool], operation_type: str = "fix", config: Dict[str, Any] = None) -> str:
    """
    Генерация отчета о выполненных операциях
    
    Args:
        results: Результаты операций
        operation_type: Тип операции (fix/dry_run)
        config: Конфигурация для отчета
        
    Returns:
        Путь к созданному файлу отчета
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"qdrant_{operation_type}_report_{timestamp}.txt"
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    report_content = f"""================================================================
                   QDRANT COLLECTIONS FIX REPORT
================================================================
Время выполнения: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Операция: {operation_type.upper()}
Qdrant URL: {config['url'] if config else 'N/A'}
API Key: {'***настроен***' if config and config['api_key'] else 'не настроен'}

ОБЩАЯ СТАТИСТИКА:
- Обработано коллекций: {total}
- Успешно исправлено: {successful}
- Ошибок: {total - successful}
- Процент успеха: {(successful/total*100):.1f}%

ДЕТАЛИ ПО КОЛЛЕКЦИЯМ:
"""
    
    for collection_name, success in results.items():
        status = "✅ УСПЕШНО" if success else "❌ ОШИБКА"
        report_content += f"  {collection_name}: {status}\n"
    
    report_content += f"""
================================================================
Рекомендации:
"""
    
    if successful == total:
        report_content += "- ✅ Все операции выполнены успешно!\n"
    else:
        failed = total - successful
        report_content += f"- ⚠️  {failed} коллекций не удалось исправить\n"
        report_content += f"- Проверьте логи для получения подробной информации об ошибках\n"
    
    report_content += f"""
================================================================
Конец отчета
================================================================
"""
    
    try:
        # Создаем директорию для отчетов если её нет
        os.makedirs("reports", exist_ok=True)
        report_path = os.path.join("reports", report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Отчет сохранен: {report_path}")
        return report_path
        
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета: {e}")
        return ""


def ask_confirmation(message: str) -> bool:
    """
    Запрос подтверждения от пользователя
    
    Args:
        message: Сообщение для подтверждения
        
    Returns:
        True если пользователь подтвердил
    """
    try:
        response = input(f"\n❓ {message} [y/N]: ").strip().lower()
        return response in ['y', 'yes', 'да', 'д']
    except KeyboardInterrupt:
        print("\n⏹️  Операция прервана пользователем")
        return False


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Qdrant Fixer - массовое исправление indexing_threshold коллекций",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Исправление всех коллекций с подтверждением
  python qdrant_fixer.py

  # Автоматическое исправление без подтверждения
  python qdrant_fixer.py --auto

  # Dry-run режим для тестирования
  python qdrant_fixer.py --dry-run

  # Исправление с конкретным threshold
  python qdrant_fixer.py --threshold 5

  # Использование с переменными окружения
  export QDRANT_URL="http://your-qdrant:6333"
  export QDRANT_API_KEY="your-api-key"
  python qdrant_fixer.py --auto

Переменные окружения:
  QDRANT_URL     URL для подключения к Qdrant (по умолчанию: http://localhost:6333)
  QDRANT_API_KEY API ключ для аутентификации (опционально)
        """
    )
    
    parser.add_argument("--url", help="URL для подключения к Qdrant")
    parser.add_argument("--api-key", help="API ключ для аутентификации")
    parser.add_argument("--threshold", type=int, default=1, 
                       help="Новое значение indexing_threshold (по умолчанию: 1)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Режим тестирования без реальных изменений")
    parser.add_argument("--auto", action="store_true",
                       help="Автоматическое выполнение без подтверждения")
    
    args = parser.parse_args()
    
    print("🚀 QDRANT FIXER - Массовое исправление indexing_threshold")
    print("=" * 60)
    print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Загружаем конфигурацию
    try:
        config = load_config()
        print(f"✅ Конфигурация загружена:")
        print(f"   URL: {config['url']}")
        print(f"   API Key: {'***настроен***' if config['api_key'] else 'не настроен'}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        sys.exit(1)
    
    # Инициализируем клиент
    try:
        client = init_qdrant_client(config)
        print("✅ Подключение к Qdrant установлено")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка инициализации клиента: {e}")
        sys.exit(1)
    
    # Запрашиваем подтверждение (если не auto и не dry-run)
    if not args.auto and not args.dry_run:
        if not ask_confirmation(f"Будет выполнено массовое исправление indexing_threshold на {args.threshold}"):
            print("❌ Операция отменена пользователем")
            sys.exit(0)
    
    # Выполняем исправление
    try:
        print(f"🔧 Начинаем исправление коллекций...")
        results = fix_all_collections(client, args.threshold, args.dry_run)
        
        if not results:
            print("❌ Не удалось получить список коллекций или произошла ошибка")
            sys.exit(1)
        
        # Итоговая статистика
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ:")
        print(f"✅ Успешно: {successful}/{total}")
        print(f"❌ Ошибки: {total - successful}/{total}")
        print(f"📈 Процент успеха: {(successful/total*100):.1f}%")
        print("=" * 60)
        
        # Генерируем отчет
        operation_type = "dry_run" if args.dry_run else "fix"
        generate_report(results, operation_type, config)
        
        # Финальный статус
        if successful == total:
            print("🎉 Все операции выполнены успешно!")
            sys.exit(0)
        else:
            print("⚠️  Некоторые операции завершились с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()