#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant Status - Простой скрипт для проверки статуса всех коллекций

Основные функции:
- Получение статуса всех коллекций
- Анализ indexing_threshold значений
- Выявление коллекций, требующих исправления
- Генерация подробного отчета
- Простой CLI интерфейс с argparse

Использование:
    python qdrant_status.py [--url QDRANT_URL] [--api-key QDRANT_API_KEY] 
                           [--output OUTPUT_FILE] [--quiet] [--threshold THRESHOLD]

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


def get_collection_detailed_info(client: QdrantClient, collection_name: str, target_threshold: int = 1) -> Dict[str, Any]:
    """
    Получение детальной информации о коллекции
    
    Args:
        client: Клиент Qdrant
        collection_name: Имя коллекции
        target_threshold: Целевое значение indexing_threshold
        
    Returns:
        Словарь с детальной информацией о коллекции
    """
    try:
        collection_info = client.get_collection(collection_name)
        
        # Извлекаем optimizer_config для получения indexing_threshold
        optimizer_config = getattr(collection_info.config, 'optimizer_config', {})
        indexing_threshold = getattr(optimizer_config, 'indexing_threshold', 'unknown')
        
        # Вычисляем процент индексации
        vectors_count = collection_info.vectors_count
        indexed_count = collection_info.indexed_vectors_count
        
        if vectors_count > 0:
            indexing_percentage = (indexed_count / vectors_count) * 100
        else:
            indexing_percentage = 0
        
        # Определяем статус исправления
        needs_fix = indexing_threshold != target_threshold
        
        return {
            "name": collection_name,
            "vectors_count": vectors_count,
            "indexed_vectors_count": indexed_count,
            "indexing_percentage": round(indexing_percentage, 2),
            "indexing_threshold": indexing_threshold,
            "target_threshold": target_threshold,
            "needs_fix": needs_fix,
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


def get_collections_status(client: QdrantClient, target_threshold: int = 1, verbose: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Получение статуса всех коллекций
    
    Args:
        client: Клиент Qdrant
        target_threshold: Целевое значение indexing_threshold
        verbose: Выводить ли подробную информацию
        
    Returns:
        Словарь со статусом всех коллекций
    """
    collections = get_all_collections(client)
    all_status = {}
    
    if not collections:
        if verbose:
            print("⚠️  Коллекции не найдены")
        return all_status
    
    if verbose:
        print(f"🔍 Проверяем статус {len(collections)} коллекций...")
        print()
    
    for i, collection_name in enumerate(collections, 1):
        if verbose:
            print(f"[{i}/{len(collections)}] Проверяем {collection_name}...")
        
        collection_status = get_collection_detailed_info(client, collection_name, target_threshold)
        all_status[collection_name] = collection_status
        
        if verbose:
            if collection_status.get('error'):
                print(f"  ❌ Ошибка: {collection_status['error']}")
            else:
                vectors = collection_status.get('vectors_count', 0)
                indexed = collection_status.get('indexed_vectors_count', 0)
                threshold = collection_status.get('indexing_threshold', 'unknown')
                percentage = collection_status.get('indexing_percentage', 0)
                
                print(f"  📊 Векторов: {vectors:,} (проиндексировано: {indexed:,} - {percentage}%)")
                print(f"  🎯 Threshold: {threshold} (целевой: {target_threshold})")
                
                if collection_status.get('needs_fix', False):
                    print(f"  ⚠️  ТРЕБУЕТ ИСПРАВЛЕНИЯ")
                else:
                    print(f"  ✅ OK")
            
            print()
    
    return all_status


def analyze_status(status_data: Dict[str, Dict[str, Any]], target_threshold: int = 1) -> Dict[str, Any]:
    """
    Анализ статуса коллекций
    
    Args:
        status_data: Данные о статусе коллекций
        target_threshold: Целевое значение indexing_threshold
        
    Returns:
        Словарь с результатами анализа
    """
    total_collections = len(status_data)
    collections_needing_fix = 0
    collections_with_errors = 0
    total_vectors = 0
    total_indexed = 0
    
    threshold_distribution = {}
    
    for collection_name, info in status_data.items():
        # Подсчет общей статистики
        total_vectors += info.get("vectors_count", 0)
        total_indexed += info.get("indexed_vectors_count", 0)
        
        # Проверка на ошибки
        if "error" in info:
            collections_with_errors += 1
        
        # Проверка необходимости исправления
        if info.get("needs_fix", False):
            collections_needing_fix += 1
        
        # Распределение threshold значений
        threshold = info.get("indexing_threshold", "unknown")
        threshold_distribution[threshold] = threshold_distribution.get(threshold, 0) + 1
    
    # Вычисление общего процента индексации
    overall_indexing_percentage = 0
    if total_vectors > 0:
        overall_indexing_percentage = (total_indexed / total_vectors) * 100
    
    return {
        "total_collections": total_collections,
        "collections_needing_fix": collections_needing_fix,
        "collections_with_errors": collections_with_errors,
        "total_vectors": total_vectors,
        "total_indexed_vectors": total_indexed,
        "overall_indexing_percentage": round(overall_indexing_percentage, 2),
        "threshold_distribution": threshold_distribution,
        "collections_ok": total_collections - collections_needing_fix - collections_with_errors,
        "target_threshold": target_threshold
    }


def generate_status_report(status_data: Dict[str, Dict[str, Any]], analysis: Dict[str, Any], 
                          output_file: Optional[str] = None, config: Dict[str, Any] = None) -> str:
    """
    Генерация подробного отчета о статусе
    
    Args:
        status_data: Данные о статусе коллекций
        analysis: Результаты анализа
        output_file: Путь для сохранения отчета
        config: Конфигурация для отчета
        
    Returns:
        Путь к созданному файлу отчета
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not output_file:
        output_file = f"reports/qdrant_status_{timestamp}.txt"
    
    # Создаем директорию для отчетов
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    report_content = f"""================================================================
                   QDRANT COLLECTIONS STATUS REPORT
================================================================
Время проверки: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Qdrant URL: {config['url'] if config else 'N/A'}
API Key: {'***настроен***' if config and config['api_key'] else 'не настроен'}
Целевой indexing_threshold: {analysis['target_threshold']}

=== ОБЩАЯ СТАТИСТИКА ===
Всего коллекций: {analysis['total_collections']}
Коллекций с ошибками: {analysis['collections_with_errors']}
Коллекций, требующих исправления: {analysis['collections_needing_fix']}
Коллекций в порядке: {analysis['collections_ok']}

=== СТАТИСТИКА ВЕКТОРОВ ===
Всего векторов: {analysis['total_vectors']:,}
Проиндексировано: {analysis['total_indexed_vectors']:,}
Процент индексации: {analysis['overall_indexing_percentage']}%

=== РАСПРЕДЕЛЕНИЕ THRESHOLD ЗНАЧЕНИЙ ===
"""
    
    for threshold, count in analysis["threshold_distribution"].items():
        target_marker = " ✅" if threshold == analysis['target_threshold'] else ""
        report_content += f"{threshold}: {count} коллекций{target_marker}\n"
    
    report_content += f"""
=== ДЕТАЛИ ПО КОЛЛЕКЦИЯМ ===
"""
    
    # Сортируем коллекции для удобства чтения
    sorted_collections = sorted(status_data.items(), key=lambda x: x[0])
    
    for collection_name, info in sorted_collections:
        report_content += f"\n📁 {collection_name}\n"
        report_content += f"  Статус: {info.get('status', 'unknown')}\n"
        
        if "error" in info:
            report_content += f"  ❌ ОШИБКА: {info['error']}\n"
            continue
        
        vectors_count = info.get("vectors_count", 0)
        indexed_count = info.get("indexed_vectors_count", 0)
        threshold = info.get("indexing_threshold", "unknown")
        target_threshold = info.get("target_threshold", 1)
        indexing_percentage = info.get("indexing_percentage", 0)
        
        report_content += f"  Векторов: {vectors_count:,} (проиндексировано: {indexed_count:,} - {indexing_percentage}%)\n"
        report_content += f"  Threshold: {threshold} (целевой: {target_threshold})"
        
        if info.get("needs_fix", False):
            report_content += " ⚠️ ТРЕБУЕТ ИСПРАВЛЕНИЯ"
        else:
            report_content += " ✅ OK"
        
        report_content += "\n"
    
    # Рекомендации
    report_content += f"""
=== РЕКОМЕНДАЦИИ ===
"""
    
    if analysis["collections_needing_fix"] > 0:
        report_content += f"🔧 Рекомендуется исправить {analysis['collections_needing_fix']} коллекций с неоптимальным indexing_threshold\n"
        report_content += f"   Используйте: python qdrant_fixer.py --threshold {analysis['target_threshold']}\n"
    
    if analysis["collections_with_errors"] > 0:
        report_content += f"⚠️  Обнаружено {analysis['collections_with_errors']} коллекций с ошибками\n"
        report_content += f"   Проверьте подключение к Qdrant и доступность коллекций\n"
    
    if analysis["overall_indexing_percentage"] < 90:
        report_content += f"📊 Низкий процент индексации ({analysis['overall_indexing_percentage']}%)\n"
        report_content += f"   Рассмотрите оптимизацию настроек индексации\n"
    
    report_content += f"""
================================================================
Рекомендуемые команды:
  - Исправление всех коллекций: python qdrant_fixer.py --auto
  - Повторная проверка: python qdrant_status.py
================================================================
Конец отчета
================================================================
"""
    
    # Сохранение отчета
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета: {e}")
        return ""


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Qdrant Status - проверка статуса всех коллекций",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовая проверка статуса
  python qdrant_status.py

  # Проверка с сохранением в файл
  python qdrant_status.py --output my_report.txt

  # Минимальный вывод
  python qdrant_status.py --quiet

  # Проверка с конкретным целевым threshold
  python qdrant_status.py --threshold 5

  # Использование с переменными окружения
  export QDRANT_URL="http://your-qdrant:6333"
  export QDRANT_API_KEY="your-api-key"
  python qdrant_status.py

Переменные окружения:
  QDRANT_URL     URL для подключения к Qdrant (по умолчанию: http://localhost:6333)
  QDRANT_API_KEY API ключ для аутентификации (опционально)
        """
    )
    
    parser.add_argument("--url", help="URL для подключения к Qdrant")
    parser.add_argument("--api-key", help="API ключ для аутентификации")
    parser.add_argument("--output", help="Путь для сохранения отчета")
    parser.add_argument("--quiet", action="store_true", help="Минимальный вывод")
    parser.add_argument("--threshold", type=int, default=1,
                       help="Целевое значение indexing_threshold (по умолчанию: 1)")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔍 QDRANT STATUS - Проверка статуса коллекций")
        print("=" * 50)
        print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    # Загружаем конфигурацию
    try:
        config = load_config()
        if not args.quiet:
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
        if not args.quiet:
            print("✅ Подключение к Qdrant установлено")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка инициализации клиента: {e}")
        sys.exit(1)
    
    # Получаем статус всех коллекций
    try:
        status_data = get_collections_status(client, args.threshold, not args.quiet)
        
        if not status_data:
            print("❌ Коллекции не найдены или недоступны")
            sys.exit(1)
        
        # Анализируем данные
        analysis = analyze_status(status_data, args.threshold)
        
        if not args.quiet:
            print("\n" + "=" * 50)
            print("📊 АНАЛИЗ СТАТУСА:")
            print(f"📦 Всего коллекций: {analysis['total_collections']}")
            print(f"⚠️  Требуют исправления: {analysis['collections_needing_fix']}")
            print(f"❌ С ошибками: {analysis['collections_with_errors']}")
            print(f"✅ В порядке: {analysis['collections_ok']}")
            print(f"📈 Процент индексации: {analysis['overall_indexing_percentage']}%")
            print("=" * 50)
        
        # Генерируем отчет
        report_path = generate_status_report(status_data, analysis, args.output, config)
        
        if report_path and not args.quiet:
            print(f"\n📄 Подробный отчет сохранен: {report_path}")
        
        # Итоговая рекомендация
        if not args.quiet:
            if analysis['collections_needing_fix'] > 0:
                print(f"\n💡 РЕКОМЕНДАЦИЯ:")
                print(f"   Используйте: python qdrant_fixer.py --auto")
            else:
                print(f"\n✅ Все коллекции в оптимальном состоянии!")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n⏹️  Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка проверки статуса: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()