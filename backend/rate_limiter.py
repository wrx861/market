import time
from collections import deque
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate Limiter для ограничения частоты запросов к API
    Использует алгоритм "скользящего окна"
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Args:
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = {}
        
    def _clean_old_requests(self, key: str):
        """Удаляет устаревшие запросы из очереди"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        if key in self.requests:
            while self.requests[key] and self.requests[key][0] < cutoff_time:
                self.requests[key].popleft()
    
    def is_allowed(self, key: str = "default") -> bool:
        """
        Проверяет, разрешен ли запрос
        
        Args:
            key: Ключ для идентификации клиента/ресурса
            
        Returns:
            True если запрос разрешен, False если превышен лимит
        """
        current_time = time.time()
        
        # Инициализируем очередь для нового ключа
        if key not in self.requests:
            self.requests[key] = deque()
        
        # Очищаем старые запросы
        self._clean_old_requests(key)
        
        # Проверяем лимит
        if len(self.requests[key]) >= self.max_requests:
            oldest_request = self.requests[key][0]
            wait_time = self.time_window - (current_time - oldest_request)
            logger.warning(
                f"Rate limit exceeded for key '{key}'. "
                f"Wait {wait_time:.1f} seconds before next request."
            )
            return False
        
        # Добавляем текущий запрос
        self.requests[key].append(current_time)
        logger.debug(
            f"Request allowed for key '{key}'. "
            f"Count: {len(self.requests[key])}/{self.max_requests}"
        )
        return True
    
    def wait_if_needed(self, key: str = "default", timeout: float = 60) -> bool:
        """
        Ожидает, если превышен лимит запросов
        
        Args:
            key: Ключ для идентификации
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            True если запрос разрешен, False если превышен timeout
        """
        start_time = time.time()
        
        while not self.is_allowed(key):
            if time.time() - start_time > timeout:
                logger.error(f"Rate limiter timeout exceeded for key '{key}'")
                return False
            
            # Очищаем старые запросы
            self._clean_old_requests(key)
            
            # Вычисляем время ожидания
            if key in self.requests and self.requests[key]:
                oldest_request = self.requests[key][0]
                wait_time = max(0.1, self.time_window - (time.time() - oldest_request))
                wait_time = min(wait_time, 5)  # Максимум 5 секунд за раз
                
                logger.info(f"Waiting {wait_time:.1f}s due to rate limit...")
                time.sleep(wait_time)
            else:
                break
        
        return True
    
    def get_remaining_requests(self, key: str = "default") -> int:
        """Возвращает количество оставшихся разрешенных запросов"""
        self._clean_old_requests(key)
        
        if key not in self.requests:
            return self.max_requests
        
        return max(0, self.max_requests - len(self.requests[key]))
    
    def get_reset_time(self, key: str = "default") -> float:
        """Возвращает время до сброса лимита в секундах"""
        if key not in self.requests or not self.requests[key]:
            return 0
        
        oldest_request = self.requests[key][0]
        reset_time = self.time_window - (time.time() - oldest_request)
        return max(0, reset_time)
    
    def reset(self, key: str = "default"):
        """Сбрасывает счетчик для ключа"""
        if key in self.requests:
            self.requests[key].clear()
            logger.info(f"Rate limiter reset for key '{key}'")
