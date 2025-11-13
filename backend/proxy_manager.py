import requests
import logging
from typing import Optional, Dict, List
import random
import os

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    ⚠️ WARNING: Использование proxy для обхода rate limiting может привести к:
    - Блокировке API ключа
    - Нарушению условий использования
    - Юридическим последствиям
    
    Используйте на свой риск!
    """
    
    def __init__(self):
        self.proxy_list = []
        self.current_proxy_index = 0
        self.use_proxy = os.environ.get('USE_PROXY', 'false').lower() == 'true'
        
        if self.use_proxy:
            self._load_proxies()
    
    def _load_proxies(self):
        """Загружает список proxy из переменных окружения или файла"""
        # Вариант 1: Из переменной окружения (разделенные запятой)
        proxy_string = os.environ.get('PROXY_LIST', '')
        if proxy_string:
            self.proxy_list = [p.strip() for p in proxy_string.split(',') if p.strip()]
            logger.info(f"Loaded {len(self.proxy_list)} proxies from environment")
            return
        
        # Вариант 2: Из файла
        proxy_file = '/app/backend/proxies.txt'
        try:
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    self.proxy_list = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(self.proxy_list)} proxies from file")
        except Exception as e:
            logger.error(f"Error loading proxies from file: {e}")
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        Возвращает следующий proxy из списка (rotating)
        
        Returns:
            Dict с proxy настройками или None
        """
        if not self.use_proxy or not self.proxy_list:
            return None
        
        # Rotating: берем следующий proxy по очереди
        proxy_url = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        logger.debug(f"Using proxy: {proxy_url}")
        return proxies
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Возвращает случайный proxy из списка"""
        if not self.use_proxy or not self.proxy_list:
            return None
        
        proxy_url = random.choice(self.proxy_list)
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        logger.debug(f"Using random proxy: {proxy_url}")
        return proxies
    
    def test_proxy(self, proxy_url: str, timeout: int = 10) -> bool:
        """
        Тестирует работоспособность proxy
        
        Args:
            proxy_url: URL proxy сервера
            timeout: Таймаут в секундах
            
        Returns:
            True если proxy работает
        """
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        try:
            # Тестируем на простом сервисе
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Proxy {proxy_url} is working")
                return True
            else:
                logger.warning(f"Proxy {proxy_url} returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Proxy {proxy_url} failed: {e}")
            return False
    
    def test_all_proxies(self) -> List[str]:
        """
        Тестирует все proxy и возвращает список работающих
        
        Returns:
            Список работающих proxy URLs
        """
        working_proxies = []
        
        logger.info(f"Testing {len(self.proxy_list)} proxies...")
        
        for proxy_url in self.proxy_list:
            if self.test_proxy(proxy_url):
                working_proxies.append(proxy_url)
        
        logger.info(f"Found {len(working_proxies)} working proxies out of {len(self.proxy_list)}")
        
        # Обновляем список только работающими proxy
        self.proxy_list = working_proxies
        
        return working_proxies
    
    def add_proxy(self, proxy_url: str):
        """Добавляет proxy в список"""
        if proxy_url not in self.proxy_list:
            self.proxy_list.append(proxy_url)
            logger.info(f"Added proxy: {proxy_url}")
    
    def remove_proxy(self, proxy_url: str):
        """Удаляет proxy из списка"""
        if proxy_url in self.proxy_list:
            self.proxy_list.remove(proxy_url)
            logger.info(f"Removed proxy: {proxy_url}")


# Примеры форматов proxy:
# 
# HTTP Proxy:
# http://proxy.example.com:8080
# http://username:password@proxy.example.com:8080
# 
# SOCKS5 Proxy:
# socks5://proxy.example.com:1080
# socks5://username:password@proxy.example.com:1080
# 
# Бесплатные proxy (не рекомендуется для production):
# - https://www.proxy-list.download/
# - https://free-proxy-list.net/
# - https://www.sslproxies.org/
# 
# Платные proxy сервисы (рекомендуется):
# - https://brightdata.com/ (ex Luminati)
# - https://smartproxy.com/
# - https://oxylabs.io/
# - https://proxy-seller.ru/ (российский)
