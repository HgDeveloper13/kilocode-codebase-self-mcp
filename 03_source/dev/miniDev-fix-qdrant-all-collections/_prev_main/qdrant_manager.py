import requests
import json
from typing import Dict, Any, List

# Импортируем конфигурационный модуль
from config.config_loader import (
    get_qdrant_url, 
    get_qdrant_api_key,
    ConfigError
)


class QdrantConfigManager:
    def __init__(self, url: str, api_key: str = None):
        self.base_url = url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['api-key'] = api_key
    
    def get_all_collections(self) -> List[str]:
        """Получить список всех коллекций"""
        response = requests.get(
            f"{self.base_url}/collections",
            headers=self.headers
        )
        response.raise_for_status()
        collections = response.json()['result']['collections']
        return [col['name'] for col in collections]
    
    def fix_all_collections(self, new_threshold: int = 1) -> Dict[str, bool]:
        """Исправить indexing_threshold для ВСЕХ коллекций"""
        collections = self.get_all_collections()
        results = {}
        
        print(f"🔄 Найдено коллекций: {len(collections)}")
        
        for collection_name in collections:
            try:
                print(f"🔧 Обрабатываю коллекцию: {collection_name}")
                success = self.fix_indexing_threshold(collection_name, new_threshold)
                results[collection_name] = success
                
                if success:
                    print(f"✅ {collection_name} - исправлена")
                else:
                    print(f"❌ {collection_name} - ошибка")
                    
            except Exception as e:
                print(f"🚨 {collection_name} - исключение: {e}")
                results[collection_name] = False
        
        return results
    
    def fix_indexing_threshold(self, collection_name: str, new_threshold: int = 1) -> bool:
        """Исправить indexing_threshold для одной коллекции"""
        try:
            # Получаем текущую конфигурацию
            current_info = self.get_collection_info(collection_name)
            current_config = current_info['result']['config']
            
            # Обновляем только нужные параметры
            optimizer_config = current_config['optimizer_config']
            optimizer_config['indexing_threshold'] = new_threshold
            optimizer_config['vacuum_min_vector_number'] = 100
            
            return self.update_collection_config(collection_name, optimizer_config)
        except Exception as e:
            print(f"🚨 Ошибка при обработке {collection_name}: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Получить информацию о коллекции"""
        response = requests.get(
            f"{self.base_url}/collections/{collection_name}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_collection_config(self, collection_name: str, optimizer_config: Dict[str, Any]) -> bool:
        """Обновить конфигурацию коллекции"""
        patch_data = {
            "optimizer_config": optimizer_config
        }
        
        response = requests.patch(
            f"{self.base_url}/collections/{collection_name}",
            headers=self.headers,
            data=json.dumps(patch_data)
        )
        
        return response.status_code == 200
    
    def get_collections_status(self) -> Dict[str, Dict]:
        """Получить статус всех коллекций"""
        collections = self.get_all_collections()
        status = {}
        
        for collection_name in collections:
            try:
                info = self.get_collection_info(collection_name)
                status[collection_name] = {
                    'points': info['result']['points_count'],
                    'indexed': info['result']['indexed_vectors_count'],
                    'threshold': info['result']['config']['optimizer_config']['indexing_threshold']
                }
            except Exception as e:
                status[collection_name] = {'error': str(e)}
        
        return status


def main():
    """Основная функция с использованием конфигурационного модуля."""
    try:
        # Загружаем конфигурацию из конфигурационного модуля
        print("🔧 Загрузка конфигурации...")
        qdrant_url = get_qdrant_url()
        qdrant_api_key = get_qdrant_api_key()
        
        print(f"✅ Конфигурация загружена:")
        print(f"   URL: {qdrant_url}")
        print(f"   API Key: {qdrant_api_key[:10]}...")
        
        # Создаем менеджер конфигурации
        qdrant = QdrantConfigManager(qdrant_url, qdrant_api_key)
        
        # 🔥 ИСПРАВЛЯЕМ ВСЕ КОЛЛЕКЦИИ СРАЗУ!
        print("\n🚀 Начинаю исправление ВСЕХ коллекций...")
        results = qdrant.fix_all_collections(new_threshold=1)
        
        # Статистика
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\n📊 Результаты:")
        print(f"✅ Успешно: {successful}/{total}")
        print(f"❌ Ошибки: {total - successful}/{total}")
        
        # Показываем подробности
        for collection, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {collection}")
            
    except ConfigError as e:
        print(f"🚨 Ошибка конфигурации: {e}")
        print("\n💡 Подсказка:")
        print("   - Проверьте файл .config/config.json")
        print("   - Или установите переменные окружения:")
        print("     export QDRANT_URL='ваш_url'")
        print("     export QDRANT_API_KEY='ваш_api_key'")
        
    except Exception as e:
        print(f"🚨 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()