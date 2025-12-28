import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigError(Exception):
    """Исключение для ошибок конфигурации."""
    pass


class ConfigLoader:
    """Загрузчик конфигурации с приоритетом переменных окружения над файлом конфигурации."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация загрузчика конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации. Если не указан, используется .config/config.json
        """
        self.config_path = config_path or Path(__file__).parent / ".config" / "config.json"
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации с приоритетом переменных окружения.
        
        Returns:
            Словарь с конфигурацией
            
        Raises:
            ConfigError: Если не удалось загрузить конфигурацию
        """
        if self._config is not None:
            return self._config
        
        # Загружаем базовую конфигурацию из файла
        base_config = self._load_from_file()
        
        # Применяем переменные окружения с приоритетом
        self._config = self._apply_env_overrides(base_config)
        
        # Валидируем конфигурацию
        self._validate_config(self._config)
        
        return self._config
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Загрузка конфигурации из JSON-файла."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigError(f"Файл конфигурации не найден: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Ошибка парсинга JSON в файле конфигурации: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка чтения файла конфигурации: {e}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применение переменных окружения с приоритетом над файлом конфигурации.
        
        Поддерживаемые переменные окружения:
        - QDRANT_URL: URL Qdrant сервера
        - QDRANT_API_KEY: API ключ для Qdrant
        """
        # Создаем копию конфигурации для модификации
        result_config = json.loads(json.dumps(config))
        
        # Qdrant URL
        qdrant_url = os.getenv('QDRANT_URL')
        if qdrant_url:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            result_config['qdrant']['url'] = qdrant_url
        
        # Qdrant API Key
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        if qdrant_api_key:
            if 'qdrant' not in result_config:
                result_config['qdrant'] = {}
            result_config['qdrant']['api_key'] = qdrant_api_key
        
        return result_config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Валидация конфигурации."""
        # Проверка наличия обязательных секций
        if 'qdrant' not in config:
            raise ConfigError("Отсутствует обязательная секция 'qdrant' в конфигурации")
        
        qdrant_config = config['qdrant']
        
        # Проверка обязательных полей
        required_fields = ['url', 'api_key']
        for field in required_fields:
            if field not in qdrant_config:
                raise ConfigError(f"Отсутствует обязательное поле '{field}' в секции 'qdrant'")
            
            if not qdrant_config[field]:
                raise ConfigError(f"Поле '{field}' в секции 'qdrant' не может быть пустым")
        
        # Валидация URL
        url = qdrant_config['url']
        if not url.startswith(('http://', 'https://')):
            raise ConfigError(f"Некорректный URL Qdrant: {url}. URL должен начинаться с http:// или https://")
        
        # Валидация API ключа
        api_key = qdrant_config['api_key']
        if len(api_key.strip()) < 10:
            raise ConfigError(f"API ключ слишком короткий. Длина должна быть не менее 10 символов")
    
    def get_qdrant_config(self) -> Dict[str, str]:
        """
        Получение конфигурации Qdrant.
        
        Returns:
            Словарь с настройками Qdrant
        """
        config = self.load()
        return config['qdrant']
    
    def get_qdrant_url(self) -> str:
        """Получение URL Qdrant."""
        return self.get_qdrant_config()['url']
    
    def get_qdrant_api_key(self) -> str:
        """Получение API ключа Qdrant."""
        return self.get_qdrant_config()['api_key']


# Глобальный экземпляр загрузчика для удобства использования
config_loader = ConfigLoader()


def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации (глобальная функция)."""
    return config_loader.load()


def get_qdrant_config() -> Dict[str, str]:
    """Получение конфигурации Qdrant (глобальная функция)."""
    return config_loader.get_qdrant_config()


def get_qdrant_url() -> str:
    """Получение URL Qdrant (глобальная функция)."""
    return config_loader.get_qdrant_url()


def get_qdrant_api_key() -> str:
    """Получение API ключа Qdrant (глобальная функция)."""
    return config_loader.get_qdrant_api_key()