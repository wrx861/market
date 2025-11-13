import json
import hashlib
import time
from typing import Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Менеджер кэширования для API запросов
    Помогает избежать повторных запросов к PartsAPI и снизить нагрузку
    """
    
    def __init__(self, cache_dir: str = "/tmp/partsapi_cache", ttl: int = 3600):
        """
        Args:
            cache_dir: Директория для хранения кэша
            ttl: Время жизни кэша в секундах (по умолчанию 1 час)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl
        
    def _get_cache_key(self, vin: str, category: str, parts_type: str = "oem") -> str:
        """Генерирует уникальный ключ кэша"""
        data = f"{vin}_{category}_{parts_type}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, vin: str, category: str, parts_type: str = "oem") -> Optional[Any]:
        """
        Получает данные из кэша
        
        Returns:
            Закэшированные данные или None если кэш устарел или не найден
        """
        cache_key = self._get_cache_key(vin, category, parts_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            logger.debug(f"Cache miss for VIN {vin}, category {category}")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Проверяем время жизни кэша
            cached_time = cached_data.get('cached_at', 0)
            if time.time() - cached_time > self.ttl:
                logger.debug(f"Cache expired for VIN {vin}, category {category}")
                cache_file.unlink()  # Удаляем устаревший кэш
                return None
            
            logger.info(f"Cache hit for VIN {vin}, category {category}")
            return cached_data.get('data')
            
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def set(self, vin: str, category: str, data: Any, parts_type: str = "oem"):
        """Сохраняет данные в кэш"""
        cache_key = self._get_cache_key(vin, category, parts_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cached_data = {
                'cached_at': time.time(),
                'vin': vin,
                'category': category,
                'parts_type': parts_type,
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cached data for VIN {vin}, category {category}")
            
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def clear_expired(self):
        """Очищает устаревший кэш"""
        cleared_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                cached_time = cached_data.get('cached_at', 0)
                if time.time() - cached_time > self.ttl:
                    cache_file.unlink()
                    cleared_count += 1
                    
            except Exception as e:
                logger.error(f"Error clearing cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {cleared_count} expired cache entries")
        return cleared_count
    
    def clear_all(self):
        """Очищает весь кэш"""
        cleared_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                cleared_count += 1
            except Exception as e:
                logger.error(f"Error clearing cache file {cache_file}: {e}")
        
        logger.info(f"Cleared all cache ({cleared_count} entries)")
        return cleared_count
