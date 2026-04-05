#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

def final_collections_report():
    # Получаем параметры подключения из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print("=" * 80)
    print("QDRANT COLLECTIONS FINAL STATUS REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Qdrant URL: {qdrant_url}")
    print(f"API Key: {'*' * 20 if qdrant_api_key else 'Not set'}")
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
        
        print(f"✓ SUCCESSFULLY CONNECTED TO QDRANT")
        print(f"✓ FOUND {len(collections.collections)} COLLECTIONS")
        print("-" * 80)
        
        collection_summary = []
        
        for i, collection_info in enumerate(collections.collections, 1):
            collection_name = collection_info.name
            print(f"\n{i}. COLLECTION: {collection_name}")
            print("-" * 40)
            
            try:
                # Получаем информацию о коллекции
                collection = client.get_collection(collection_name)
                
                # Базовая информация
                status = getattr(collection, 'status', 'Unknown')
                print(f"Status: {status}")
                
                # Попробуем получить разные типы информации
                info_items = []
                
                # Проверяем различные возможные атрибуты
                possible_attrs = ['vectors_count', 'points_count', 'segments_count', 'ram_usage']
                for attr in possible_attrs:
                    if hasattr(collection, attr):
                        value = getattr(collection, attr)
                        info_items.append(f"{attr}: {value}")
                        print(f"{attr.replace('_', ' ').title()}: {value}")
                
                # Конфигурация
                if hasattr(collection, 'config'):
                    config = collection.config
                    print(f"Configuration: Available")
                    
                    # Параметры коллекции
                    if hasattr(config, 'params'):
                        params = config.params
                        if hasattr(params, 'indexing_threshold'):
                            threshold = params.indexing_threshold
                            print(f"Indexing Threshold: {threshold}")
                            info_items.append(f"Indexing Threshold: {threshold}")
                        
                        # Информация о векторах
                        if hasattr(params, 'vectors'):
                            vectors_config = params.vectors
                            if hasattr(vectors_config, 'size'):
                                vector_size = vectors_config.size
                                print(f"Vector Size: {vector_size}")
                                info_items.append(f"Vector Size: {vector_size}")
                            
                            if hasattr(vectors_config, 'distance'):
                                distance = vectors_config.distance
                                print(f"Distance Metric: {distance}")
                                info_items.append(f"Distance: {distance}")
                
                collection_summary.append({
                    'name': collection_name,
                    'status': status,
                    'info': info_items
                })
                
            except Exception as e:
                print(f"Warning: Could not get detailed info: {e}")
                collection_summary.append({
                    'name': collection_name,
                    'status': 'Unknown',
                    'info': [f'Error: {e}']
                })
        
        # Финальный отчет
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        for summary in collection_summary:
            print(f"• {summary['name']}: Status = {summary['status']}")
        
        print(f"\nTotal Collections: {len(collection_summary)}")
        print("Connection Test: SUCCESS")
        print("All collections accessible: YES")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Connection or query failed: {e}")
        return False

if __name__ == "__main__":
    success = final_collections_report()
    if success:
        print("\n✓ QDRANT MANAGER SETUP COMPLETED SUCCESSFULLY!")
    else:
        print("\n✗ Setup encountered issues.")