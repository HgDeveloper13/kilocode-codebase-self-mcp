import requests
import json
from typing import Dict, Any, List

# Импортируем новую систему конфигурации
from qdrant_config import QdrantConfig, ConfigError


class QdrantManager:
    """Менеджер Qdrant с поддержкой конфигурационной системы."""
    
    def __init__(self, config_path: str = None):
        """
        Инициализация менеджера с загрузкой конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации (опционально)
        """
        try:
            # Загружаем конфигурацию
            self.config = QdrantConfig(config_path)
            
            # Создаем параметры для QdrantClient
            client_params = self.config.get_client_params()
            
            # Инициализируем базовый URL и заголовки
            self.base_url = f"http://{self.config.host}:{self.config.port}"
            self.headers = {
                'Content-Type': 'application/json'
            }
            if self.config.api_key:
                self.headers['api-key'] = self.config.api_key
                
        except ConfigError as e:
            print(f"🚨 Ошибка конфигурации: {e}")
            raise
    
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
    """Основная функция с использованием новой системы конфигурации."""
    try:
        print("🔧 Загрузка конфигурации...")
        
        # Создаем менеджер - конфигурация загружается автоматически
        manager = QdrantManager()
        
        print(f"✅ Конфигурация загружена:")
        print(f"   Host: {manager.config.host}")
        print(f"   Port: {manager.config.port}")
        print(f"   API Key: {'***' if manager.config.api_key else 'None'}")
        
        # 🔥 ИСПРАВЛЯЕМ ВСЕ КОЛЛЕКЦИИ СРАЗУ!
        print("\n🚀 Начинаю исправление ВСЕХ коллекций...")
        results = manager.fix_all_collections(new_threshold=1)
        
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
        print("   - Проверьте файл config.yaml")
        print("   - Или создайте конфигурацию:")
        print("     python -c \"from qdrant_config import QdrantConfig; QdrantConfig.create_default_config()\"")
        print("   - Или установите переменные окружения:")
        print("     export QDRANT_HOST='ваш_host'")
        print("     export QDRANT_PORT='ваш_port'")
        print("     export QDRANT_API_KEY='ваш_api_key'")
        
    except Exception as e:
        print(f"🚨 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()