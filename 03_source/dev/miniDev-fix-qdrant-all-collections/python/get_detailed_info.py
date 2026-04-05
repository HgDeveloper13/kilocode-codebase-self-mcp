#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_collections_detailed_info():
    # Получаем параметры подключения из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print("=" * 80)
    print("QDRANT COLLECTIONS DETAILED INFORMATION REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Qdrant URL: {qdrant_url}")
    print()
    
    try:
        # Создаем клиент Qdrant
        if qdrant_api_key:
            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=30
            )
        else:
            client = QdrantClient(
                url=qdrant_url,
                timeout=30
            )
        
        # Получаем список коллекций
        collections = client.get_collections()
        
        if not collections.collections:
            print("No collections found.")
            return
        
        print(f"Found {len(collections.collections)} collections:")
        print("-" * 80)
        
        for i, collection_info in enumerate(collections.collections, 1):
            collection_name = collection_info.name
            print(f"\n{i}. COLLECTION: {collection_name}")
            print("-" * 40)
            
            try:
                # Получаем подробную информацию о коллекции
                collection = client.get_collection(collection_name)
                
                # Базовую информацию
                print(f"Status: {collection.status}")
                print(f"Index Status: {collection.index_status}")
                
                # Количество векторов (если доступно)
                if hasattr(collection, 'vectors_count'):
                    print(f"Vectors Count: {collection.vectors_count}")
                elif hasattr(collection, 'points_count'):
                    print(f"Points Count: {collection.points_count}")
                else:
                    print("Vectors/Points Count: Information not available")
                
                # Конфигурация
                if hasattr(collection, 'config'):
                    print(f"Config Type: {type(collection.config)}")
                    if hasattr(collection.config, 'params'):
                        params = collection.config.params
                        print(f"Parameters: {params}")
                        
                        # Индексация threshold
                        if hasattr(params, 'indexing_threshold'):
                            print(f"Indexing Threshold: {params.indexing_threshold}")
                        
                        # Информация о векторах
                        if hasattr(params, 'vectors'):
                            vectors_config = params.vectors
                            print(f"Vector Config: {vectors_config}")
                            
                            if hasattr(vectors_config, 'size'):
                                print(f"Vector Size: {vectors_config.size}")
                            if hasattr(vectors_config, 'distance'):
                                print(f"Distance Metric: {vectors_config.distance}")
                
                # Сканы коллекции для получения статистики
                try:
                    # Получаем информацию о количестве точек
                    collection_info = client.get_collection_info(collection_name)
                    if hasattr(collection_info, 'points_count'):
                        print(f"Total Points: {collection_info.points_count}")
                except Exception as e:
                    print(f"Could not get points count: {e}")
                
                print()
                
            except Exception as e:
                print(f"Error getting details for {collection_name}: {e}")
                print()
        
        print("=" * 80)
        print("DETAILED REPORT COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to get collections detailed info: {e}")
        return False

if __name__ == "__main__":
    get_collections_detailed_info()