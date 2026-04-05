#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_collections_info():
    # Получаем параметры подключения из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print("=" * 60)
    print("QDRANT COLLECTIONS INFORMATION REPORT")
    print("=" * 60)
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
        print("-" * 60)
        
        for i, collection_info in enumerate(collections.collections, 1):
            collection_name = collection_info.name
            print(f"{i}. Collection: {collection_name}")
            
            try:
                # Получаем подробную информацию о коллекции
                collection = client.get_collection(collection_name)
                
                print(f"   Status: {collection.status}")
                print(f"   Vectors Count: {collection.vectors_count}")
                print(f"   Index Status: {collection.index_status}")
                print(f"   Config: {collection.config}")
                
                # Если есть index_params, показываем их
                if hasattr(collection.config, 'params') and collection.config.params:
                    params = collection.config.params
                    if hasattr(params, 'indexing_threshold'):
                        print(f"   Indexing Threshold: {params.indexing_threshold}")
                    if hasattr(params, 'vectors'):
                        print(f"   Vector Size: {params.vectors.size if hasattr(params.vectors, 'size') else 'N/A'}")
                
                print()
                
            except Exception as e:
                print(f"   Error getting details: {e}")
                print()
        
        print("=" * 60)
        print("Report completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to get collections info: {e}")
        return False

if __name__ == "__main__":
    get_collections_info()