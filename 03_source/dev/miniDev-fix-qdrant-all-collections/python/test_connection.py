#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Загружаем переменные окружения из .env файла
load_dotenv()

def test_connection():
    # Получаем параметры подключения из переменных окружения
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print("Testing Qdrant connection...")
    print(f"URL: {qdrant_url}")
    print(f"API Key: {'*' * 20 if qdrant_api_key else 'Not set'}")
    
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
        
        # Тестируем подключение
        print("Connecting to Qdrant...")
        collections = client.get_collections()
        
        print(f"✓ Connection successful!")
        print(f"✓ Found {len(collections.collections)} collections:")
        
        for collection in collections.collections:
            print(f"  - {collection.name}")
            
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()