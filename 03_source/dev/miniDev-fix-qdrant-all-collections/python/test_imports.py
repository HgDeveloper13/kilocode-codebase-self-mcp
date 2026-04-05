#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест импортов - Проверка всех зависимостей и модулей
"""

def test_imports():
    """Тестирование всех импортов"""
    try:
        print("🔍 Проверка импортов...")
        
        # Базовые импорты
        import os
        import sys
        import json
        import argparse
        from datetime import datetime
        from typing import Dict, List, Any, Optional
        print("✅ Базовые импорты Python")
        
        # Qdrant импорты
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        print("✅ Qdrant client импорт")
        
        # Локальные модули
        import qdrant_fixer
        import qdrant_status
        print("✅ Локальные модули")
        
        print("\n🎉 Все импорты успешны!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\nУстановите зависимости:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_shebang_lines():
    """Проверка shebang строк в скриптах"""
    import os
    
    scripts = ['qdrant_fixer.py', 'qdrant_status.py']
    
    for script in scripts:
        script_path = os.path.join('.', script)
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!/'):
                    print(f"✅ {script}: корректная shebang строка")
                else:
                    print(f"⚠️  {script}: отсутствует shebang строка")

if __name__ == "__main__":
    print("🧪 ТЕСТ ИМПОРТОВ И СТРУКТУРЫ")
    print("=" * 50)
    
    # Проверяем импорты
    imports_ok = test_imports()
    
    print("\n📝 Проверка shebang строк:")
    test_shebang_lines()
    
    print("\n" + "=" * 50)
    if imports_ok:
        print("✅ Все тесты пройдены успешно!")
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)