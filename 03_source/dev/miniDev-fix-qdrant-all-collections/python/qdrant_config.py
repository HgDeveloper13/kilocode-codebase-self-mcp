"""
Система управления конфигурацией для Qdrant Manager.

Предоставляет гибкую систему загрузки конфигурации из файлов и переменных окружения
с автоматической валидацией параметров.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path


class ConfigError(Exception):
    """Исключение для ошибок конфигурации."""
    pass


class QdrantConfig:
    """Класс для управления конфигурацией Qdrant."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации (YAML или JSON)
        """
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        
        # Загружаем конфигурацию
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла или использование значений по умолчанию."""
        if self.config_path and os.path.exists(self.config_path):
            return self.load_from_file(self.config_path)
        else:
            # Используем значения по умолчанию
            return self._get_default_config()
    
    def load_from_file(self, path: str) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла.
        
        Args:
            path: Путь к файлу конфигурации
            
        Returns:
            Словарь с конфигурацией
            
        Raises:
            ConfigError: При ошибках загрузки или валидации
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif path.endswith('.json'):
                    config = json.load(f)
                else:
                    raise ConfigError(f"Unsupported file format: {path}")
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigError(f"Failed to parse configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading configuration file: {e}")
        
        # Применяем переменные окружения с приоритетом
        return self._apply_env_overrides(config)
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применение переменных окружения с приоритетом над файлом конфигурации.
        
        Args:
            config: Базовая конфигурация из файла
            
        Returns:
            Конфигурация с примененными переменными окружения
        """
        # Создаем копию конфигурации для модификации
        result_config = json.loads(json.dumps(config))
        
        # Qdrant host
        qdrant_host = os.getenv('QDRANT_HOST')
        if qdrant_host:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            result_config['qdrant']['host'] = qdrant_host
        
        # Qdrant port
        qdrant_port = os.getenv('QDRANT_PORT')
        if qdrant_port:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            try:
                result_config['qdrant']['port'] = int(qdrant_port)
            except ValueError:
                raise ConfigError(f"Invalid QDRANT_PORT value: {qdrant_port}")
        
        # Qdrant API Key
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        if qdrant_api_key:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            result_config['qdrant']['api_key'] = qdrant_api_key
        
        # Qdrant timeout
        qdrant_timeout = os.getenv('QDRANT_TIMEOUT')
        if qdrant_timeout:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            try:
                result_config['qdrant']['timeout'] = int(qdrant_timeout)
            except ValueError:
                raise ConfigError(f"Invalid QDRANT_TIMEOUT value: {qdrant_timeout}")
        
        return result_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Получение конфигурации по умолчанию."""
        return {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': None,
                'timeout': 30
            }
        }
    
    def validate_config(self) -> None:
        """Валидация конфигурации."""
        qdrant_config = self._config.get('qdrant', {})
        
        # Проверка host
        host = qdrant_config.get('host', '')
        if not host or not isinstance(host, str):
            raise ConfigError("Invalid host in configuration")
        
        # Проверка port
        port = qdrant_config.get('port', 0)
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ConfigError("Invalid port in configuration")
        
        # Проверка timeout
        timeout = qdrant_config.get('timeout', 0)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ConfigError("Invalid timeout in configuration")
    
    @property
    def host(self) -> str:
        """Получение хоста Qdrant."""
        return self._config.get('qdrant', {}).get('host', 'localhost')
    
    @property
    def port(self) -> int:
        """Получение порта Qdrant."""
        return self._config.get('qdrant', {}).get('port', 6333)
    
    @property
    def api_key(self) -> Optional[str]:
        """Получение API ключа Qdrant."""
        return self._config.get('qdrant', {}).get('api_key', None)
    
    @property
    def timeout(self) -> int:
        """Получение таймаута соединения."""
        return self._config.get('qdrant', {}).get('timeout', 30)
    
    def get_client_params(self) -> Dict[str, Any]:
        """
        Получение параметров для создания QdrantClient.
        
        Returns:
            Словарь с параметрами для QdrantClient
        """
        params = {
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        return params
    
    @classmethod
    def create_default_config(cls, path: str = "config.yaml"):
        """
        Создание дефолтного конфигурационного файла.
        
        Args:
            path: Путь для создания файла
        """
        default_config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'your-api-key-here',
                'timeout': 30
            }
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def __str__(self) -> str:
        """Строковое представление конфигурации (без секретов)."""
        return f"QdrantConfig(host='{self.host}', port={self.port}, timeout={self.timeout}s, api_key={'***' if self.api_key else 'None'})"
    
    def __repr__(self) -> str:
        """Подробное строковое представление конфигурации."""
        return self.__str__()


def get_config(config_path: Optional[str] = None) -> QdrantConfig:
    """
    Получение экземпляра конфигурации.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Экземпляр QdrantConfig
    """
    config = QdrantConfig(config_path)
    config.validate_config()
    return config