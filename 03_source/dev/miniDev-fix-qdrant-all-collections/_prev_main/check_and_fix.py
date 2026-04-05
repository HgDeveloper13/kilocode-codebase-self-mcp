#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 QDRANT COLLECTIONS FIXER
Скрипт для автоматического исправления indexing_threshold всех коллекций
"""

import sys
import os
from datetime import datetime

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем конфигурационный модуль
from config.config_loader import (
    get_qdrant_url, 
    get_qdrant_api_key,
    ConfigError
)
from qdrant_manager import QdrantConfigManager


def print_header(title: str):
    """Печать заголовка"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def ask_confirmation(question: str) -> bool:
    """Запрос подтверждения от пользователя"""
    # Проверяем, передан ли флаг --auto для автоматического режима
    if '--auto' in sys.argv:
        print(f"🤖 Автоматический режим: {question} [y]")
        return True
    
    while True:
        response = input(f"\n❓ {question} [y/N]: ").strip().lower()
        if response in ['y', 'yes', 'да', 'д']:
            return True
        elif response in ['n', 'no', 'нет', 'н', '']:
            return False
        else:
            print("Пожалуйста, введите 'y' для подтверждения или 'n' для отмены")

def get_initial_status(manager):
    """Получение начального статуса"""
    print("🔍 Анализирую текущее состояние коллекций...")
    try:
        status = manager.get_collections_status()
        
        # Находим коллекции, которые нужно исправить
        needs_fix = []
        optimized = []
        errors = []
        
        for name, info in status.items():
            if 'error' in info:
                errors.append((name, info['error']))
            elif info.get('threshold', 0) > 1:
                needs_fix.append(name)
            else:
                optimized.append(name)
        
        return {
            'all_status': status,
            'needs_fix': needs_fix,
            'optimized': optimized,
            'errors': errors
        }
    except Exception as e:
        print(f"❌ Ошибка при получении статуса: {e}")
        return None

def print_analysis(analysis: dict):
    """Печать анализа состояния"""
    print_header("АНАЛИЗ СОСТОЯНИЯ")
    
    total = len(analysis['all_status'])
    needs_fix_count = len(analysis['needs_fix'])
    optimized_count = len(analysis['optimized'])
    errors_count = len(analysis['errors'])
    
    print(f"📦 Всего коллекций: {total}")
    print(f"⚠️  Нужно исправить: {needs_fix_count}")
    print(f"✅ Уже оптимизированы: {optimized_count}")
    print(f"🚨 С ошибками: {errors_count}")
    
    if needs_fix_count > 0:
        print(f"\n📋 Коллекции для исправления:")
        for i, name in enumerate(analysis['needs_fix'], 1):
            print(f"  {i:2d}. {name}")
    
    if errors_count > 0:
        print(f"\n⚠️  Коллекции с ошибками:")
        for name, error in analysis['errors']:
            print(f"  • {name}: {error}")

def run_fix_operation(manager, collections_to_fix: list):
    """Запуск операции исправления"""
    print_header("ЗАПУСК ИСПРАВЛЕНИЯ")
    
    if not collections_to_fix:
        print("✅ Нет коллекций для исправления!")
        return {}
    
    print(f"🔄 Исправляю {len(collections_to_fix)} коллекций...")
    print(f"   Устанавливаю indexing_threshold = 1")
    print(f"   Устанавливаю vacuum_min_vector_number = 100")
    
    results = manager.fix_all_collections()
    
    # Анализируем результаты
    successful = [name for name, success in results.items() if success]
    failed = [name for name, success in results.items() if not success]
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ:")
    print(f"✅ Успешно: {len(successful)}/{len(collections_to_fix)}")
    print(f"❌ Ошибки: {len(failed)}/{len(collections_to_fix)}")
    
    if successful:
        print(f"\n✅ Успешно исправлены:")
        for name in successful:
            print(f"  • {name}")
    
    if failed:
        print(f"\n❌ Ошибки при исправлении:")
        for name in failed:
            print(f"  • {name}")
    
    return results

def verify_results(manager, collections_fixed: list, fix_results: dict):
    """Проверка результатов исправления"""
    print_header("ПРОВЕРКА РЕЗУЛЬТАТОВ")
    
    print("🔍 Проверяю новые значения indexing_threshold...")
    
    try:
        new_status = manager.get_collections_status()
        
        verified_fixed = []
        still_need_fix = []
        errors = []
        
        for name in collections_fixed:
            if name in new_status:
                info = new_status[name]
                if 'error' in info:
                    errors.append((name, info['error']))
                elif info.get('threshold', 0) == 1:
                    verified_fixed.append(name)
                else:
                    still_need_fix.append((name, info.get('threshold', 'N/A')))
        
        print(f"\n✅ Проверка завершена:")
        print(f"   • Подтверждено исправление: {len(verified_fixed)}")
        print(f"   • Все еще нужно исправить: {len(still_need_fix)}")
        print(f"   • Ошибки при проверке: {len(errors)}")
        
        if still_need_fix:
            print(f"\n⚠️  Все еще нуждаются в исправлении:")
            for name, threshold in still_need_fix:
                print(f"  • {name}: текущий порог = {threshold}")
        
        if errors:
            print(f"\n🚨 Ошибки при проверке:")
            for name, error in errors:
                print(f"  • {name}: {error}")
        
        return {
            'verified_fixed': verified_fixed,
            'still_need_fix': still_need_fix,
            'errors': errors,
            'new_status': new_status
        }
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return None

def generate_fix_report(analysis: dict, fix_results: dict, verification: dict):
    """Генерация отчета об исправлении"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"qdrant_fix_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"ОТЧЕТ ПО ИСПРАВЛЕНИЮ QDRANT КОЛЛЕКЦИЙ\n")
        f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"URL: {get_qdrant_url()}\n\n")
        
        # Начальное состояние
        f.write(f"НАЧАЛЬНОЕ СОСТОЯНИЕ:\n")
        f.write(f"- Всего коллекций: {len(analysis['all_status'])}\n")
        f.write(f"- Нужно исправить: {len(analysis['needs_fix'])}\n")
        f.write(f"- Уже оптимизированы: {len(analysis['optimized'])}\n")
        f.write(f"- С ошибками: {len(analysis['errors'])}\n\n")
        
        # Результаты исправления
        f.write(f"РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ:\n")
        successful = [name for name, success in fix_results.items() if success]
        failed = [name for name, success in fix_results.items() if not success]
        f.write(f"- Успешно исправлены: {len(successful)}\n")
        f.write(f"- Ошибки при исправлении: {len(failed)}\n\n")
        
        if successful:
            f.write(f"УСПЕШНО ИСПРАВЛЕНЫ:\n")
            for name in successful:
                f.write(f"  • {name}\n")
            f.write(f"\n")
        
        if failed:
            f.write(f"ОШИБКИ ПРИ ИСПРАВЛЕНИИ:\n")
            for name in failed:
                f.write(f"  • {name}\n")
            f.write(f"\n")
        
        # Проверка результатов
        if verification:
            f.write(f"ПРОВЕРКА РЕЗУЛЬТАТОВ:\n")
            f.write(f"- Подтверждено исправление: {len(verification['verified_fixed'])}\n")
            f.write(f"- Все еще нужно исправить: {len(verification['still_need_fix'])}\n")
            f.write(f"- Ошибки при проверке: {len(verification['errors'])}\n\n")
        
        # Итоговое состояние
        if verification and 'new_status' in verification:
            new_status = verification['new_status']
            optimized_count = sum(1 for info in new_status.values() 
                                if 'error' not in info and info.get('threshold', 0) == 1)
            still_needs_fix = sum(1 for info in new_status.values() 
                                if 'error' not in info and info.get('threshold', 0) > 1)
            
            f.write(f"ИТОГОВОЕ СОСТОЯНИЕ:\n")
            f.write(f"- Оптимизированы: {optimized_count}\n")
            f.write(f"- Нужно исправить: {still_needs_fix}\n")
    
    return report_file

def main():
    """Главная функция"""
    try:
        print_header("QDRANT COLLECTIONS FIXER")
        print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Загружаем конфигурацию из конфигурационного модуля
        print("🔧 Загрузка конфигурации...")
        qdrant_url = get_qdrant_url()
        qdrant_api_key = get_qdrant_api_key()
        
        print(f"✅ Конфигурация загружена:")
        print(f"   URL: {qdrant_url}")
        print(f"   API Key: {qdrant_api_key[:10]}...")
        
        # Создаем менеджер
        manager = QdrantConfigManager(qdrant_url, qdrant_api_key)
        
        # Анализируем текущее состояние
        analysis = get_initial_status(manager)
        if analysis is None:
            return 1
        
        print_analysis(analysis)
        
        # Проверяем, есть ли коллекции для исправления
        if len(analysis['needs_fix']) == 0:
            print(f"\n✅ Все коллекции уже оптимизированы! Ничего исправлять не нужно.")
            return 0
        
        # Запрашиваем подтверждение
        if not ask_confirmation(f"Найдено {len(analysis['needs_fix'])} коллекций для исправления. Продолжить?"):
            print("❌ Операция отменена пользователем")
            return 0
        
        # Запускаем исправление
        fix_results = run_fix_operation(manager, analysis['needs_fix'])
        
        # Проверяем результаты
        fixed_collections = [name for name, success in fix_results.items() if success]
        if fixed_collections:
            verification = verify_results(manager, fixed_collections, fix_results)
        else:
            verification = None
        
        # Генерируем отчет
        report_file = generate_fix_report(analysis, fix_results, verification)
        print(f"\n💾 Подробный отчет сохранен в: {report_file}")
        
        # Итоговая сводка
        print_header("ИТОГОВАЯ СВОДКА")
        if verification:
            print(f"✅ Успешно исправлено: {len(verification['verified_fixed'])}")
            print(f"⚠️  Требует повторного исправления: {len(verification['still_need_fix'])}")
            print(f"🚨 Ошибки: {len(verification['errors'])}")
        else:
            successful = sum(1 for success in fix_results.values() if success)
            print(f"✅ Исправления выполнены: {successful}")
        
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
        print(f"\n⏹️ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n🚨 Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)