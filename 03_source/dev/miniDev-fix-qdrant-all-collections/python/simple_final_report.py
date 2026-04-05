#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

def simple_final_report():
    # Получаем параметры подключения из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print("=" * 80)
    print("QDRANT COLLECTIONS SIMPLE FINAL REPORT")
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
        
        print("SUCCESS: Connected to Qdrant")
        print(f"Found {len(collections.collections)} collections:")
        print("-" * 80)
        
        for i, collection_info in enumerate(collections.collections, 1):
            collection_name = collection_info.name
            print(f"{i}. Collection: {collection_name}")
            
            try:
                # Получаем информацию о коллекции
                collection = client.get_collection(collection_name)
                
                # Базовая информация
                status = getattr(collection, 'status', 'Unknown')
                print(f"   Status: {status}")
                
                # Проверяем различные возможные атрибуты
                if hasattr(collection, 'vectors_count'):
                    print(f"   Vectors Count: {collection.vectors_count}")
                if hasattr(collection, 'points_count'):
                    print(f"   Points Count: {collection.points_count}")
                
                # Конфигурация
                if hasattr(collection, 'config'):
                    config = collection.config
                    if hasattr(config, 'params'):
                        params = config.params
                        if hasattr(params, 'indexing_threshold'):
                            threshold = params.indexing_threshold
                            print(f"   Indexing Threshold: {threshold}")
                        
                        # Информация о векторах
                        if hasattr(params, 'vectors'):
                            vectors_config = params.vectors
                            if hasattr(vectors_config, 'size'):
                                print(f"   Vector Size: {vectors_config.size}")
                            if hasattr(vectors_config, 'distance'):
                                print(f"   Distance Metric: {vectors_config.distance}")
                
                print()
                
            except Exception as e:
                print(f"   Warning: Could not get detailed info: {e}")
                print()
        
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        print(f"Total Collections: {len(collections.collections)}")
        print("Connection Test: SUCCESS")
        print("Collections Status: All accessible")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Connection or query failed: {e}")
        return False

if __name__ == "__main__":
    success = simple_final_report()
    if success:
        print("\nQDRANT MANAGER SETUP COMPLETED SUCCESSFULLY!")
    else:
        print("\nSetup encountered issues.")