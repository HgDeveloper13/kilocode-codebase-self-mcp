# Импортируем конфигурационный модуль
from .config.config_loader import (
    get_qdrant_url, 
    get_qdrant_api_key,
    ConfigError
)
from qdrant_manager import QdrantConfigManager
import requests
import json


class QdrantAdvancedManager(QdrantConfigManager):
    def create_optimized_collection(self, collection_name: str, vector_size: int = 4096) -> bool:
        """Создать оптимизированную коллекцию для разработки"""
        collection_config = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
                "on_disk": True
            },
            "optimizers_config": {
                "indexing_threshold": 1,
                "deleted_threshold": 0.2,
                "vacuum_min_vector_number": 100,
                "flush_interval_sec": 5
            },
            "hnsw_config": {
                "m": 16,
                "ef_construct": 100,
                "full_scan_threshold": 1000
            }
        }
        
        response = requests.put(
            f"{self.base_url}/collections/{collection_name}",
            headers=self.headers,
            data=json.dumps(collection_config)
        )
        
        if response.status_code == 200:
            print(f"✅ Коллекция {collection_name} создана с оптимизированными настройками!")
            return True
        else:
            print(f"❌ Ошибка создания: {response.text}")
            return False
    
    def monitor_collections(self):
        """Мониторинг всех коллекций"""
        response = requests.get(
            f"{self.base_url}/collections",
            headers=self.headers
        )
        response.raise_for_status()
        
        collections = response.json()['result']['collections']
        
        print("📊 Статус коллекций:")
        for collection in collections:
            info = self.get_collection_info(collection['name'])
            config = info['result']['config']
            points = info['result']['points_count']
            indexed = info['result']['indexed_vectors_count']
            
            status = "✅" if indexed > 0 else "⚠️"
            print(f"{status} {collection['name']}: {points} точек, {indexed} проиндексировано")

# 🚀 Использование расширенного менеджера
def advanced_management():
    try:
        # Загружаем конфигурацию из конфигурационного модуля
        print("🔧 Загрузка конфигурации...")
        qdrant_url = get_qdrant_url()
        qdrant_api_key = get_qdrant_api_key()
        
        print(f"✅ Конфигурация загружена:")
        print(f"   URL: {qdrant_url}")
        print(f"   API Key: {qdrant_api_key[:10]}...")
        
        qdrant = QdrantAdvancedManager(qdrant_url, qdrant_api_key)
        
        # Мониторинг текущего состояния
        qdrant.monitor_collections()
        
        # Создание новой оптимизированной коллекции (если нужно)
        # qdrant.create_optimized_collection("roblox-optimized")
        
        # Исправление существующей
        # qdrant.fix_indexing_threshold(COLLECTION_NAME)
        
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
    # advanced_management()  # Раскомментируй для расширенного управления
    pass