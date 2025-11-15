from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# Import models
from models import (
    User, Cart, Order, SearchHistory, ActivityLog, Settings,
    Vehicle, ServiceRecord, LogEntry, Reminder,
    SearchArticleRequest, SearchVINRequest, AISearchRequest,
    AddToCartRequest, UpdateCartItemRequest, RemoveFromCartRequest,
    CreateOrderRequest, PartInfo, CartItem
)

# Import clients
from rossko_client import RosskoClient
from autostels_client import AutostelsClient
from autotrade_client import AutotradeClient
from berg_client import BergClient
from autotrade_oem_parser import AutotradeOEMParser
from openai_client import OpenAIClient
# from gemini_client import GeminiClient  # Заменено на OpenAI
# from partkom_parser import PartKomParser  # Отключено - используем PartsAPI
from partsapi_client import PartsApiClient
from n8n_client import TelegramNotifier

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


def normalize_article(article: str) -> str:
    """Нормализует артикул для сравнения: убирает пробелы, дефисы, приводит к верхнему регистру"""
    return article.upper().replace('-', '').replace(' ', '').replace('/', '')


def is_exact_match(search_article: str, result_article: str) -> bool:
    """Проверяет точное совпадение артикулов (с учетом нормализации)"""
    return normalize_article(search_article) == normalize_article(result_article)


def filter_relevant_results(parts: list, search_article: str) -> list:
    """
    Фильтрует результаты, оставляя только релевантные:
    - Точное совпадение артикула
    - Аналоги (is_cross=true) с точным совпадением артикула
    - НЕ показывает комплектующие (сальники, кольца и т.д.)
    """
    if not parts:
        return []
    
    filtered = []
    search_normalized = normalize_article(search_article)
    
    for part in parts:
        part_article = part.get('article', '')
        part_normalized = normalize_article(part_article)
        
        # Проверяем точное совпадение артикула
        if search_normalized == part_normalized:
            filtered.append(part)
        # Или если это аналог с тем же нормализованным артикулом
        elif part.get('is_cross', False) and search_normalized in part_normalized:
            filtered.append(part)
    
    return filtered


def deduplicate_and_prioritize(parts: list, search_article: str = "", availability_filter=None, sort_by=None) -> list:
    """
    Объединяет результаты от разных поставщиков:
    - Для одинаковых артикулов оставляет 2 позиции: самую дешевую + самую быструю
    - Если одна позиция и дешевая и быстрая - оставляем 1
    - Разные артикулы - показываем все
    - Приоритет: оригинал → запрошенный артикул → аналоги
    """
    if not parts:
        return []
    
    # Если фильтр по складам - не дедуплицируем по складу, показываем все варианты
    if availability_filter == 'in_stock_tyumen':
        # Группируем по артикулу + бренд + склад (чтобы показать все склады)
        grouped = {}
        for part in parts:
            key = f"{part['article']}_{part['brand']}_{part.get('warehouse', 'unknown')}".upper()
            
            if key not in grouped:
                grouped[key] = part
            else:
                # Если тот же склад - берем дешевле
                existing = grouped[key]
                if part['price'] < existing['price']:
                    grouped[key] = part
        
        result = list(grouped.values())
    else:
        # Новая дедупликация: для одинаковых артикулов оставляем 2 позиции
        # 1) самую дешевую, 2) самую быструю доставку
        grouped = {}
        
        for part in parts:
            # Нормализуем артикул для группировки
            article_normalized = normalize_article(part['article'])
            brand = part.get('brand', 'UNKNOWN').upper()
            key = f"{article_normalized}_{brand}"
            
            if key not in grouped:
                grouped[key] = {'cheapest': part, 'fastest': part}
            else:
                # Обновляем самую дешевую
                if part['price'] < grouped[key]['cheapest']['price']:
                    grouped[key]['cheapest'] = part
                
                # Обновляем самую быструю
                if part['delivery_days'] < grouped[key]['fastest']['delivery_days']:
                    grouped[key]['fastest'] = part
        
        # Собираем результат: дешевую + быструю (если они разные)
        result = []
        for key, offers in grouped.items():
            cheapest = offers['cheapest']
            fastest = offers['fastest']
            
            # Добавляем самую дешевую
            result.append(cheapest)
            
            # Добавляем самую быструю только если это другая позиция
            if cheapest != fastest:
                # Проверяем что это действительно разные предложения
                if (cheapest.get('provider') != fastest.get('provider') or
                    cheapest.get('warehouse') != fastest.get('warehouse') or
                    cheapest.get('price') != fastest.get('price')):
                    result.append(fastest)
    
    # Применяем фильтр по наличию если нужно
    if availability_filter == 'in_stock_tyumen':
        # "В наличии" = склады Тюмени с быстрой доставкой (0-1 день)
        result = [p for p in result if 'тюмень' in p.get('warehouse', '').lower() and p.get('delivery_days', 999) <= 1]
    elif availability_filter == 'on_order':
        result = [p for p in result if p.get('delivery_days', 999) > 1]
    
    # Добавляем флаги для frontend
    search_normalized = normalize_article(search_article) if search_article else ""
    for part in result:
        part_normalized = normalize_article(part.get('article', ''))
        
        # Помечаем оригинальный артикул (не аналог)
        part['is_original'] = not part.get('is_cross', False)
        
        # Помечаем запрошенный артикул
        part['is_requested'] = (part_normalized == search_normalized)
    
    # Приоритизация результатов
    def get_priority(part):
        # 1. Оригинал (не аналог) - высший приоритет
        if part.get('is_original', False):
            return 0
        # 2. Запрошенный артикул - второй приоритет  
        elif part.get('is_requested', False):
            return 1
        # 3. Остальные аналоги
        else:
            return 2
    
    # Сортировка
    if sort_by == 'price_asc':
        result.sort(key=lambda x: (get_priority(x), x.get('price', 999999)))
    elif sort_by == 'price_desc':
        result.sort(key=lambda x: (get_priority(x), -x.get('price', 0)))
    elif sort_by == 'delivery_asc':
        result.sort(key=lambda x: (get_priority(x), x.get('delivery_days', 999)))
    else:
        # По умолчанию: приоритет (оригинал > запрошенный > аналоги), потом по доставке
        result.sort(key=lambda x: (get_priority(x), x.get('delivery_days', 999)))
    
    return result

# Initialize clients
rossko_client = RosskoClient()
autostels_client = AutostelsClient()
autotrade_client = AutotradeClient()
berg_client = BergClient()
oem_parser = AutotradeOEMParser()

# Optional clients - only if API keys are provided
try:
    ai_client = OpenAIClient()
except ValueError:
    ai_client = None
    print("⚠️  OpenAI client not initialized - OPENAI_API_KEY not provided")

try:
    partsapi_client = PartsApiClient()
except (ValueError, Exception) as e:
    partsapi_client = None
    print(f"⚠️  PartsAPI client not initialized: {str(e)}")

telegram_notifier = TelegramNotifier()

# Create the main app
app = FastAPI(title="Market Auto Parts API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============ USER ENDPOINTS ============

@api_router.get("/users/{telegram_id}")
async def get_user(telegram_id: int):
    """Получение информации о пользователе"""
    user = await db.users.find_one({"telegram_id": telegram_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@api_router.post("/users")
async def create_or_update_user(user_data: dict):
    """Создание или обновление пользователя"""
    telegram_id = user_data.get("telegram_id")
    
    existing_user = await db.users.find_one({"telegram_id": telegram_id})
    
    if existing_user:
        # Update existing user
        await db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": user_data}
        )
    else:
        # Create new user
        user = User(**user_data)
        doc = user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
    
    return {"status": "success", "telegram_id": telegram_id}


# ============ SEARCH ENDPOINTS ============

@api_router.post("/search/article")
async def search_by_article(request: SearchArticleRequest):
    """Поиск запчастей по артикулу через Rossko и Autotrade API с фильтрами"""
    try:
        # Получаем параметры фильтрации из запроса (если есть)
        availability_filter = getattr(request, 'availability_filter', None)
        sort_by = getattr(request, 'sort_by', None)
        
        # Получаем наценку из настроек
        settings = await db.settings.find_one({}, {"_id": 0})
        markup_percent = settings.get('markup_percent', 0) if settings else 0
        
        # Параллельный поиск через оба API
        import asyncio
        
        async def search_rossko():
            return rossko_client.search_by_article(
                request.article,
                availability_filter=availability_filter,
                sort_by=sort_by,
                markup_percent=markup_percent
            )
        
        async def search_autotrade():
            try:
                # Для Autotrade используем синхронный метод в executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: autotrade_client.search_by_article(request.article, cross=True, replace=False)
                )
            except Exception as e:
                logger.error(f"Autotrade search error: {str(e)}")
                return []
        
        async def search_berg():
            try:
                # Для Berg используем синхронный метод в executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: berg_client.search_by_article(request.article, analogs=True)
                )
            except Exception as e:
                logger.error(f"Berg search error: {str(e)}")
                return []
        
        async def search_autostels():
            try:
                # Для Autostels используем синхронный метод в executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: autostels_client.search_by_article(request.article)
                )
            except Exception as e:
                logger.error(f"Autostels search error: {str(e)}")
                return []
        
        # Запускаем все ЧЕТЫРЕ поиска параллельно
        rossko_parts, autotrade_parts, berg_parts, autostels_parts = await asyncio.gather(
            search_rossko(),
            search_autotrade(),
            search_berg(),
            search_autostels(),
            return_exceptions=True
        )
        
        # Обрабатываем возможные ошибки
        if isinstance(rossko_parts, Exception):
            logger.error(f"Rossko search failed: {str(rossko_parts)}")
            rossko_parts = []
        
        if isinstance(autotrade_parts, Exception):
            logger.error(f"Autotrade search failed: {str(autotrade_parts)}")
            autotrade_parts = []
        
        if isinstance(berg_parts, Exception):
            logger.error(f"Berg search failed: {str(berg_parts)}")
            berg_parts = []
        
        if isinstance(autostels_parts, Exception):
            logger.error(f"Autostels search failed: {str(autostels_parts)}")
            autostels_parts = []
        
        # Если Autotrade ничего не нашел, пробуем поиск по OEM номерам из других поставщиков
        if len(autotrade_parts) == 0:
            logger.info("Autotrade returned 0 results, trying OEM search...")
            
            # Функция для генерации вариантов артикула
            def generate_article_variants(article: str) -> set:
                """Генерирует варианты артикула для поиска"""
                variants = {article}
                
                # Убираем дефисы
                no_dash = article.replace('-', '')
                variants.add(no_dash)
                
                # Добавляем ST- префикс если его нет
                if not article.upper().startswith('ST-') and not article.upper().startswith('ST'):
                    variants.add(f'ST-{article}')
                    variants.add(f'ST-{no_dash}')
                
                # Пробуем заменить суффиксы (например 1PA1A -> H5103)
                # Берем базовую часть (первые 5 цифр)
                import re
                digits = re.findall(r'\d+', article)
                if digits:
                    base_number = digits[0]
                    if len(base_number) >= 5:
                        # Пробуем популярные суффиксы для Hyundai/Kia
                        common_suffixes = ['H5103', '1PA1A', 'AA100', '35503']
                        for suffix in common_suffixes:
                            variants.add(f'{base_number}-{suffix}')
                            variants.add(f'ST-{base_number}-{suffix}')
                
                return variants
            
            # Собираем OEM номера из результатов других поставщиков
            oem_numbers = set()
            
            # Из Berg (берем до 20 уникальных артикулов)
            berg_articles = set()
            for part in berg_parts:
                article = part.get('article', '').strip()
                if article and article.upper() != request.article.upper():
                    berg_articles.add(article)
                    if len(berg_articles) >= 20:
                        break
            
            for article in berg_articles:
                variants = generate_article_variants(article)
                oem_numbers.update(variants)
            
            # Из Rossko (берем до 10 уникальных артикулов)
            rossko_articles = set()
            for part in rossko_parts:
                article = part.get('article', '').strip()
                if article and article.upper() != request.article.upper():
                    rossko_articles.add(article)
                    if len(rossko_articles) >= 10:
                        break
            
            for article in rossko_articles:
                variants = generate_article_variants(article)
                oem_numbers.update(variants)
            
            # Из Autostels (берем до 10 уникальных артикулов)
            autostels_articles = set()
            for part in autostels_parts:
                article = part.get('article', '').strip()
                if article and article.upper() != request.article.upper():
                    autostels_articles.add(article)
                    if len(autostels_articles) >= 10:
                        break
            
            for article in autostels_articles:
                variants = generate_article_variants(article)
                oem_numbers.update(variants)
            
            logger.info(f"Found {len(oem_numbers)} OEM variants to search in Autotrade")
            
            # Ищем в Autotrade по каждому OEM номеру (максимум 3 чтобы не перегружать API)
            if oem_numbers:
                oem_search_tasks = []
                for oem in list(oem_numbers)[:3]:  # Берем первые 3 OEM
                    async def search_by_oem(oem_number):
                        try:
                            loop = asyncio.get_event_loop()
                            return await loop.run_in_executor(
                                None,
                                lambda: autotrade_client.search_by_article(oem_number, markup_percent)
                            )
                        except Exception as e:
                            logger.error(f"OEM search failed for {oem_number}: {str(e)}")
                            return []
                    
                    oem_search_tasks.append(search_by_oem(oem))
                
                # Выполняем поиски параллельно
                oem_results = await asyncio.gather(*oem_search_tasks, return_exceptions=True)
                
                # Объединяем результаты
                for result in oem_results:
                    if not isinstance(result, Exception) and result:
                        logger.info(f"Found {len(result)} results from OEM search")
                        autotrade_parts.extend(result)
                
                if len(autotrade_parts) > 0:
                    logger.info(f"✅ Autotrade OEM search successful: found {len(autotrade_parts)} parts")
        
        # Применяем наценку к Autotrade, Berg и Autostels если нужно
        if markup_percent > 0:
            for part in autotrade_parts:
                part['price'] = round(part['price'] * (1 + markup_percent / 100), 2)
            for part in berg_parts:
                part['price'] = round(part['price'] * (1 + markup_percent / 100), 2)
            for part in autostels_parts:
                part['price'] = round(part['price'] * (1 + markup_percent / 100), 2)
        
        # Объединяем результаты и дедуплицируем
        all_parts = rossko_parts + autotrade_parts + berg_parts + autostels_parts
        parts = deduplicate_and_prioritize(all_parts, availability_filter, sort_by)
        
        # Сохраняем историю поиска
        user = await db.users.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        if user:
            search_history = SearchHistory(
                user_id=user['id'],
                telegram_id=request.telegram_id,
                query=request.article,
                search_type="article",
                results_count=len(parts)
            )
            doc = search_history.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.search_history.insert_one(doc)
        
        # Логируем активность для админ-панели
        await log_activity(
            request.telegram_id,
            "search_article",
            {
                "article": request.article,
                "results_count": len(parts),
                "filters": {
                    "availability": availability_filter,
                    "sort": sort_by
                }
            }
        )
        
        return {
            "status": "success",
            "query": request.article,
            "results": parts,
            "count": len(parts)
        }
        
    except Exception as e:
        logger.error(f"Error searching article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/search/vin")
async def search_by_vin(request: SearchVINRequest):
    """Анализ VIN номера через PartsAPI.ru"""
    try:
        logger.info(f"Searching VIN via PartsAPI: {request.vin}")
        
        # Проверяем доступен ли PartsAPI клиент
        if not partsapi_client:
            raise HTTPException(status_code=503, detail="PartsAPI service not available - API key not configured")
        
        # Получаем информацию об автомобиле через PartsAPI
        car_info = partsapi_client.get_car_info_by_vin(request.vin)
        
        if not car_info:
            raise HTTPException(status_code=400, detail="VIN не найден. Проверьте правильность VIN номера.")
        
        # Получаем группы каталога
        catalog_groups = partsapi_client.get_catalog_groups(request.vin)
        
        # Дополнительный анализ через AI (если доступен)
        if car_info.get('make') and ai_client:
            try:
                enhanced_info = ai_client.analyze_car_info(car_info)
                car_info.update(enhanced_info)
            except Exception as e:
                logger.warning(f"AI analysis failed: {str(e)}")
        
        # Сохраняем историю поиска
        user = await db.users.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        if user:
            search_history = SearchHistory(
                user_id=user['id'],
                telegram_id=request.telegram_id,
                query=request.vin,
                search_type="vin",
                results_count=1
            )
            doc = search_history.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.search_history.insert_one(doc)
        
        return {
            "status": "success",
            "vin": request.vin,
            "car_info": car_info,
            "catalog_available": len(catalog_groups) > 0,
            "catalog_groups": catalog_groups[:20]  # Ограничиваем 20 группами
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing VIN: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске VIN: {str(e)}")


@api_router.post("/search/vin_oem")
async def search_vin_oem(request: dict):
    """Поиск OEM артикулов по VIN через каталог Autotrade"""
    try:
        vin = request.get('vin', '').strip().upper()
        part_name = request.get('part_name', '').strip()
        telegram_id = request.get('telegram_id')
        
        if not vin or len(vin) != 17:
            raise HTTPException(status_code=400, detail="Введите корректный VIN номер (17 символов)")
        
        if not part_name:
            raise HTTPException(status_code=400, detail="Введите название запчасти")
        
        logger.info(f"OEM search: VIN={vin}, part={part_name}")
        
        # Запускаем парсер Autotrade OEM каталога
        result = await oem_parser.search_by_vin(vin, part_name)
        
        if not result.get('success'):
            error_msg = result.get('error', 'Не удалось найти автомобиль по VIN')
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Сохраняем историю поиска
        user = await db.users.find_one({"telegram_id": telegram_id}, {"_id": 0})
        if user:
            search_history = SearchHistory(
                user_id=user['id'],
                telegram_id=telegram_id,
                query=f"{vin} - {part_name}",
                search_type="vin_oem",
                results_count=len(result.get('oem_parts', []))
            )
            doc = search_history.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.search_history.insert_one(doc)
        
        return {
            "status": "success",
            "vin": vin,
            "vehicle_info": result.get('vehicle_info'),
            "oem_parts": result.get('oem_parts', []),
            "count": len(result.get('oem_parts', []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OEM search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске в OEM каталоге: {str(e)}")


@api_router.post("/search/ai")
async def ai_search(request: AISearchRequest):
    """Поиск запчастей по описанию через PartsAPI с артикулами + fallback на Rossko"""
    try:
        logger.info(f"AI search for VIN: {request.vin}, query: {request.query}")
        
        # Проверяем доступен ли PartsAPI клиент
        if not partsapi_client:
            raise HTTPException(status_code=503, detail="PartsAPI service not available - API key not configured")
        
        # Получаем информацию об автомобиле через PartsAPI
        car_info = partsapi_client.get_car_info_by_vin(request.vin)
        
        if not car_info:
            raise HTTPException(status_code=400, detail="VIN не найден")
        
        # Ищем запчасти напрямую через PartsAPI по запросу пользователя
        logger.info(f"Searching parts via PartsAPI for query: {request.query}")
        partsapi_results = partsapi_client.search_parts_by_query(request.vin, request.query, 'oem')
        
        # Преобразуем результаты PartsAPI в формат для frontend
        parts = []
        articles_found = []
        
        for part in partsapi_results[:20]:  # Ограничиваем 20 запчастями
            article = part.get('article', '')
            brand = part.get('brand', 'Unknown')
            name = part.get('name', 'Unknown')
            
            if article:
                articles_found.append(article)
                
                # Пробуем найти цену и наличие через Rossko
                rossko_info = rossko_client.search_by_article(article)
                
                if rossko_info and len(rossko_info) > 0:
                    # Используем данные из Rossko (с ценами)
                    for rossko_part in rossko_info[:1]:  # Берем первый результат
                        parts.append({
                            'article': article,
                            'brand': brand,
                            'name': name,
                            'price': rossko_part.get('price', 0),
                            'delivery_days': rossko_part.get('delivery_days', 'Неизвестно'),
                            'availability': rossko_part.get('availability', 'Под заказ'),
                            'supplier': rossko_part.get('supplier', brand),
                            'source': 'partsapi+rossko'
                        })
                else:
                    # Только данные из PartsAPI (без цен)
                    parts.append({
                        'article': article,
                        'brand': brand,
                        'name': name,
                        'price': 0,
                        'delivery_days': 'Уточняйте',
                        'availability': 'Оригинал',
                        'supplier': brand,
                        'source': 'partsapi'
                    })
        
        logger.info(f"Found {len(parts)} parts from PartsAPI, {len(articles_found)} unique articles")
        
        # Если через PartsAPI ничего не нашли, пробуем Rossko напрямую
        if not parts:
            logger.info("No parts found via PartsAPI, trying Rossko direct search")
            search_query = request.query.strip()
            parts = rossko_client.search_by_article(search_query)
            logger.info(f"Rossko direct search found {len(parts)} parts")
        
        # Получаем количество групп каталога (если доступен)
        try:
            catalog_groups = partsapi_client.get_catalog_groups(request.vin) if partsapi_client else []
        except Exception as e:
            logger.warning(f"Failed to get catalog groups: {str(e)}")
            catalog_groups = []
        
        # Сохраняем историю поиска
        user = await db.users.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        if user:
            search_history = SearchHistory(
                user_id=user['id'],
                telegram_id=request.telegram_id,
                query=f"VIN: {request.vin}, Query: {request.query}",
                search_type="ai_search",
                results_count=len(parts)
            )
            doc = search_history.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.search_history.insert_one(doc)
        
        return {
            "status": "success",
            "car_info": car_info,
            "query": request.query,
            "results": parts,
            "count": len(parts),
            "articles_found": articles_found,
            "catalog_groups_count": len(catalog_groups)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI search: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка AI поиска: {str(e)}")


# ============ CART ENDPOINTS ============

@api_router.get("/cart/{telegram_id}")
async def get_cart(telegram_id: int):
    """Получение корзины пользователя"""
    cart = await db.carts.find_one({"telegram_id": telegram_id}, {"_id": 0})
    
    if not cart:
        # Создаем пустую корзину
        user = await db.users.find_one({"telegram_id": telegram_id}, {"_id": 0})
        
        # Если пользователя нет, создаем его
        if not user:
            new_user = User(
                telegram_id=telegram_id,
                username=None,
                name=None
            )
            user_doc = new_user.model_dump()
            user_doc['created_at'] = user_doc['created_at'].isoformat()
            await db.users.insert_one(user_doc)
            user = user_doc
        
        new_cart = Cart(
            user_id=user['id'],
            telegram_id=telegram_id,
            items=[]
        )
        doc = new_cart.model_dump()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.carts.insert_one(doc)
        return doc
    
    return cart


@api_router.post("/cart/add")
async def add_to_cart(request: AddToCartRequest):
    """Добавление товара в корзину"""
    try:
        cart = await db.carts.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        
        if not cart:
            # Создаем новую корзину
            user = await db.users.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            new_cart = Cart(
                user_id=user['id'],
                telegram_id=request.telegram_id,
                items=[request.item]
            )
            doc = new_cart.model_dump()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.carts.insert_one(doc)
        else:
            # Проверяем, есть ли товар в корзине
            items = cart.get('items', [])
            found = False
            
            for item in items:
                if item['article'] == request.item.article:
                    item['quantity'] += request.item.quantity
                    found = True
                    break
            
            if not found:
                items.append(request.item.model_dump())
            
            # Обновляем корзину
            await db.carts.update_one(
                {"telegram_id": request.telegram_id},
                {
                    "$set": {
                        "items": items,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
        
        # Логируем активность
        await log_activity(
            request.telegram_id,
            "add_to_cart",
            {
                "article": request.item.article,
                "brand": request.item.brand,
                "price": request.item.price,
                "quantity": request.item.quantity
            }
        )
        
        return {"status": "success", "message": "Item added to cart"}
        
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/cart/update")
async def update_cart_item(request: UpdateCartItemRequest):
    """Обновление количества товара в корзине"""
    try:
        cart = await db.carts.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        items = cart.get('items', [])
        
        for item in items:
            if item['article'] == request.article:
                item['quantity'] = request.quantity
                break
        
        await db.carts.update_one(
            {"telegram_id": request.telegram_id},
            {
                "$set": {
                    "items": items,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {"status": "success", "message": "Cart updated"}
        
    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/cart/remove")
async def remove_from_cart(request: RemoveFromCartRequest):
    """Удаление товара из корзины"""
    try:
        cart = await db.carts.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        items = cart.get('items', [])
        items = [item for item in items if item['article'] != request.article]
        
        await db.carts.update_one(
            {"telegram_id": request.telegram_id},
            {
                "$set": {
                    "items": items,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {"status": "success", "message": "Item removed from cart"}
        
    except Exception as e:
        logger.error(f"Error removing from cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/cart/{telegram_id}")
async def clear_cart(telegram_id: int):
    """Очистка корзины"""
    try:
        await db.carts.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "items": [],
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {"status": "success", "message": "Cart cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ORDER ENDPOINTS ============

@api_router.post("/orders")
async def create_order(request: CreateOrderRequest):
    """Создание заказа"""
    try:
        # Получаем корзину
        cart = await db.carts.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        
        if not cart or not cart.get('items'):
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Получаем пользователя
        user = await db.users.find_one({"telegram_id": request.telegram_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Рассчитываем сумму
        total = sum(item['price'] * item['quantity'] for item in cart['items'])
        
        # Создаем заказ
        order = Order(
            user_id=user['id'],
            telegram_id=request.telegram_id,
            items=cart['items'],
            total=total,
            user_info=request.user_info
        )
        
        doc = order.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.orders.insert_one(doc)
        
        # Очищаем корзину
        await db.carts.update_one(
            {"telegram_id": request.telegram_id},
            {"$set": {"items": [], "updated_at": datetime.utcnow().isoformat()}}
        )
        
        # Отправляем уведомление админу в Telegram
        order_data = {
            "order_id": doc['id'],
            "telegram_id": request.telegram_id,
            "user_info": request.user_info,
            "items": cart['items'],
            "total": total,
            "created_at": doc['created_at']
        }
        telegram_notifier.send_order_notification(order_data)
        
        # Логируем активность
        await log_activity(
            request.telegram_id,
            "create_order",
            {
                "order_id": doc['id'],
                "total": total,
                "items_count": len(cart['items']),
                "user_info": request.user_info
            }
        )
        
        return {
            "status": "success",
            "order_id": doc['id'],
            "total": total,
            "message": "Order created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/orders/{telegram_id}")
async def get_orders(telegram_id: int):
    """Получение списка заказов пользователя"""
    try:
        orders = await db.orders.find(
            {"telegram_id": telegram_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "status": "success",
            "orders": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/orders/detail/{order_id}")
async def get_order_detail(order_id: str):
    """Получение детальной информации о заказе"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


# ============ TELEGRAM BOT WEBHOOK ============

@api_router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Webhook для Telegram бота"""
    try:
        data = await request.json()
        logger.info(f"Received Telegram webhook: {data}")
        
        # Здесь будет обработка сообщений от бота
        # Пока просто логируем
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============ GARAGE ENDPOINTS ============

@api_router.get("/garage/{telegram_id}")
async def get_user_vehicles(telegram_id: int):
    """Получение всех автомобилей пользователя"""
    try:
        vehicles = await db.vehicles.find(
            {"telegram_id": telegram_id},
            {"_id": 0}
        ).sort("is_active", -1).to_list(100)
        
        return {
            "status": "success",
            "vehicles": vehicles,
            "count": len(vehicles)
        }
        
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/garage")
async def add_vehicle(vehicle_data: dict):
    """Добавление нового автомобиля"""
    try:
        telegram_id = vehicle_data.get("telegram_id")
        
        # Получаем пользователя
        user = await db.users.find_one({"telegram_id": telegram_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        vehicle = Vehicle(
            user_id=user['id'],
            telegram_id=telegram_id,
            make=vehicle_data.get("make"),
            model=vehicle_data.get("model"),
            year=vehicle_data.get("year"),
            vin=vehicle_data.get("vin"),
            color=vehicle_data.get("color"),
            license_plate=vehicle_data.get("license_plate"),
            mileage=vehicle_data.get("mileage", 0),
            purchase_date=vehicle_data.get("purchase_date"),
            is_active=vehicle_data.get("is_active", True)
        )
        
        doc = vehicle.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.vehicles.insert_one(doc)
        
        # Логируем активность
        await log_activity(
            telegram_id,
            "add_vehicle",
            {"make": vehicle.make, "model": vehicle.model, "year": vehicle.year}
        )
        
        return {
            "status": "success",
            "vehicle_id": doc['id'],
            "message": "Vehicle added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding vehicle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/garage/vehicle/{vehicle_id}")
async def get_vehicle_detail(vehicle_id: str):
    """Получение детальной информации об автомобиле"""
    try:
        vehicle = await db.vehicles.find_one({"id": vehicle_id}, {"_id": 0})
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Получаем статистику
        service_count = await db.service_records.count_documents({"vehicle_id": vehicle_id})
        log_count = await db.log_entries.count_documents({"vehicle_id": vehicle_id})
        reminders_count = await db.reminders.count_documents({
            "vehicle_id": vehicle_id,
            "is_completed": False
        })
        
        # Последнее обслуживание
        last_service = await db.service_records.find(
            {"vehicle_id": vehicle_id},
            {"_id": 0}
        ).sort("service_date", -1).limit(1).to_list(1)
        last_service = last_service[0] if last_service else None
        
        return {
            "status": "success",
            "vehicle": vehicle,
            "stats": {
                "service_count": service_count,
                "log_count": log_count,
                "active_reminders": reminders_count,
                "last_service": last_service
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicle detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/garage/vehicle/{vehicle_id}")
async def update_vehicle(vehicle_id: str, vehicle_data: dict):
    """Обновление информации об автомобиле"""
    try:
        await db.vehicles.update_one(
            {"id": vehicle_id},
            {
                "$set": {
                    **vehicle_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {"status": "success", "message": "Vehicle updated"}
        
    except Exception as e:
        logger.error(f"Error updating vehicle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/garage/vehicle/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """Удаление автомобиля"""
    try:
        logger.info(f"Deleting vehicle with id: {vehicle_id}")
        
        # Удаляем автомобиль
        vehicle_result = await db.vehicles.delete_one({"id": vehicle_id})
        logger.info(f"Vehicle deleted, count: {vehicle_result.deleted_count}")
        
        # Также удаляем все связанные данные
        service_result = await db.service_records.delete_many({"vehicle_id": vehicle_id})
        logger.info(f"Service records deleted: {service_result.deleted_count}")
        
        log_result = await db.log_entries.delete_many({"vehicle_id": vehicle_id})
        logger.info(f"Log entries deleted: {log_result.deleted_count}")
        
        reminder_result = await db.reminders.delete_many({"vehicle_id": vehicle_id})
        logger.info(f"Reminders deleted: {reminder_result.deleted_count}")
        
        cache_result = await db.diagnostic_cache.delete_many({"cache_key": {"$regex": f"^.*{vehicle_id}"}})
        logger.info(f"Diagnostic cache deleted: {cache_result.deleted_count}")
        
        logger.info(f"Vehicle {vehicle_id} and all related data deleted successfully")
        return {"status": "success", "message": "Vehicle deleted", "vehicle_id": vehicle_id}
        
    except Exception as e:
        logger.error(f"Error deleting vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/garage/vehicle/{vehicle_id}/expenses")
async def get_vehicle_expenses(vehicle_id: str, period: str = "all"):
    """Получение аналитики расходов по автомобилю"""
    try:
        from datetime import timedelta
        
        # Определяем период
        now = datetime.utcnow()
        if period == "month":
            start_date = (now - timedelta(days=30)).isoformat()
        elif period == "3months":
            start_date = (now - timedelta(days=90)).isoformat()
        elif period == "year":
            start_date = (now - timedelta(days=365)).isoformat()
        else:  # all
            start_date = None
        
        # Получаем записи обслуживания
        service_filter = {"vehicle_id": vehicle_id}
        if start_date:
            service_filter["service_date"] = {"$gte": start_date}
        
        service_records = await db.service_records.find(
            service_filter,
            {"_id": 0, "service_type": 1, "title": 1, "cost": 1, "service_date": 1}
        ).to_list(10000)
        
        # Получаем записи из бортжурнала
        log_filter = {"vehicle_id": vehicle_id}
        if start_date:
            log_filter["entry_date"] = {"$gte": start_date}
        
        log_entries = await db.log_entries.find(
            log_filter,
            {"_id": 0, "entry_type": 1, "title": 1, "fuel_cost": 1, "expense_amount": 1, "expense_category": 1, "entry_date": 1}
        ).to_list(10000)
        
        # Категории расходов
        categories = {
            "service": {"name": "Обслуживание", "total": 0, "count": 0},
            "fuel": {"name": "Топливо", "total": 0, "count": 0},
            "parts": {"name": "Запчасти", "total": 0, "count": 0},
            "wash": {"name": "Мойка", "total": 0, "count": 0},
            "parking": {"name": "Парковка", "total": 0, "count": 0},
            "fines": {"name": "Штрафы", "total": 0, "count": 0},
            "insurance": {"name": "Страховка", "total": 0, "count": 0},
            "other": {"name": "Другое", "total": 0, "count": 0}
        }
        
        all_expenses = []
        total = 0
        
        # Обрабатываем записи обслуживания
        for record in service_records:
            if record.get("cost", 0) > 0:
                cost = float(record["cost"])
                categories["service"]["total"] += cost
                categories["service"]["count"] += 1
                total += cost
                
                all_expenses.append({
                    "date": record.get("service_date"),
                    "category": "service",
                    "title": record.get("title"),
                    "amount": cost
                })
        
        # Обрабатываем записи бортжурнала
        for entry in log_entries:
            amount = 0
            category = "other"
            
            # Заправка
            if entry.get("entry_type") == "refuel" and entry.get("fuel_cost"):
                amount = float(entry["fuel_cost"])
                category = "fuel"
            # Расход
            elif entry.get("entry_type") == "expense" and entry.get("expense_amount"):
                amount = float(entry["expense_amount"])
                exp_cat = entry.get("expense_category", "other")
                if exp_cat in categories:
                    category = exp_cat
            
            if amount > 0:
                categories[category]["total"] += amount
                categories[category]["count"] += 1
                total += amount
                
                all_expenses.append({
                    "date": entry.get("entry_date"),
                    "category": category,
                    "title": entry.get("title"),
                    "amount": amount
                })
        
        # Сортируем расходы по дате (новые первыми)
        all_expenses.sort(key=lambda x: x["date"] or "", reverse=True)
        
        # Формируем итоговую структуру
        categories_list = []
        for key, data in categories.items():
            if data["total"] > 0:
                percentage = (data["total"] / total * 100) if total > 0 else 0
                categories_list.append({
                    "key": key,
                    "name": data["name"],
                    "total": round(data["total"], 2),
                    "count": data["count"],
                    "percentage": round(percentage, 1)
                })
        
        # Сортируем категории по сумме
        categories_list.sort(key=lambda x: x["total"], reverse=True)
        
        return {
            "status": "success",
            "total": round(total, 2),
            "period": period,
            "categories": categories_list,
            "expenses": all_expenses[:100],  # Последние 100 расходов
            "expenses_count": len(all_expenses)
        }
        
    except Exception as e:
        logger.error(f"Error getting vehicle expenses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Service Records
@api_router.get("/garage/vehicle/{vehicle_id}/service")
async def get_service_records(vehicle_id: str):
    """Получение истории обслуживания"""
    try:
        records = await db.service_records.find(
            {"vehicle_id": vehicle_id},
            {"_id": 0}
        ).sort("service_date", -1).to_list(1000)
        
        return {
            "status": "success",
            "records": records,
            "count": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error getting service records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/garage/vehicle/{vehicle_id}/service")
async def add_service_record(vehicle_id: str, record_data: dict):
    """Добавление записи об обслуживании"""
    try:
        telegram_id = record_data.get("telegram_id")
        
        record = ServiceRecord(
            vehicle_id=vehicle_id,
            telegram_id=telegram_id,
            service_type=record_data.get("service_type"),
            title=record_data.get("title"),
            description=record_data.get("description"),
            mileage=record_data.get("mileage"),
            cost=record_data.get("cost", 0),
            service_date=record_data.get("service_date"),
            service_provider=record_data.get("service_provider"),
            parts_used=record_data.get("parts_used")
        )
        
        doc = record.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.service_records.insert_one(doc)
        
        # Обновляем пробег автомобиля
        await db.vehicles.update_one(
            {"id": vehicle_id},
            {"$set": {"mileage": record.mileage, "updated_at": datetime.utcnow().isoformat()}}
        )
        
        return {"status": "success", "record_id": doc['id']}
        
    except Exception as e:
        logger.error(f"Error adding service record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/garage/service/{record_id}")
async def update_service_record(record_id: str, record_data: dict):
    """Редактирование записи об обслуживании"""
    try:
        # Проверяем существование записи
        existing = await db.service_records.find_one({"id": record_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Service record not found")
        
        # Обновляем только переданные поля
        update_data = {}
        if "service_type" in record_data:
            update_data["service_type"] = record_data["service_type"]
        if "title" in record_data:
            update_data["title"] = record_data["title"]
        if "description" in record_data:
            update_data["description"] = record_data["description"]
        if "mileage" in record_data:
            update_data["mileage"] = record_data["mileage"]
        if "cost" in record_data:
            update_data["cost"] = record_data["cost"]
        if "service_date" in record_data:
            update_data["service_date"] = record_data["service_date"]
        if "service_provider" in record_data:
            update_data["service_provider"] = record_data["service_provider"]
        if "parts_used" in record_data:
            update_data["parts_used"] = record_data["parts_used"]
        
        if update_data:
            await db.service_records.update_one(
                {"id": record_id},
                {"$set": update_data}
            )
        
        return {"status": "success", "message": "Service record updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/garage/service/{record_id}")
async def delete_service_record(record_id: str):
    """Удаление записи об обслуживании"""
    try:
        result = await db.service_records.delete_one({"id": record_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Service record not found")
        
        return {"status": "success", "message": "Service record deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Log Entries (Бортжурнал)
@api_router.get("/garage/vehicle/{vehicle_id}/log")
async def get_log_entries(vehicle_id: str):
    """Получение записей бортжурнала"""
    try:
        entries = await db.log_entries.find(
            {"vehicle_id": vehicle_id},
            {"_id": 0}
        ).sort("entry_date", -1).to_list(1000)
        
        return {
            "status": "success",
            "entries": entries,
            "count": len(entries)
        }
        
    except Exception as e:
        logger.error(f"Error getting log entries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/garage/vehicle/{vehicle_id}/log")
async def add_log_entry(vehicle_id: str, entry_data: dict):
    """Добавление записи в бортжурнал"""
    try:
        telegram_id = entry_data.get("telegram_id")
        
        entry = LogEntry(
            vehicle_id=vehicle_id,
            telegram_id=telegram_id,
            entry_type=entry_data.get("entry_type"),
            title=entry_data.get("title"),
            description=entry_data.get("description"),
            fuel_amount=entry_data.get("fuel_amount"),
            fuel_cost=entry_data.get("fuel_cost"),
            fuel_type=entry_data.get("fuel_type"),
            trip_distance=entry_data.get("trip_distance"),
            trip_purpose=entry_data.get("trip_purpose"),
            expense_amount=entry_data.get("expense_amount"),
            expense_category=entry_data.get("expense_category"),
            mileage=entry_data.get("mileage"),
            entry_date=entry_data.get("entry_date")
        )
        
        doc = entry.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.log_entries.insert_one(doc)
        
        # Обновляем пробег автомобиля
        await db.vehicles.update_one(
            {"id": vehicle_id},
            {"$set": {"mileage": entry.mileage, "updated_at": datetime.utcnow().isoformat()}}
        )
        
        return {"status": "success", "entry_id": doc['id']}
        
    except Exception as e:
        logger.error(f"Error adding log entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/garage/log/{entry_id}")
async def update_log_entry(entry_id: str, entry_data: dict):
    """Редактирование записи бортжурнала"""
    try:
        # Проверяем существование записи
        existing = await db.log_entries.find_one({"id": entry_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        # Обновляем только переданные поля
        update_data = {}
        if "entry_type" in entry_data:
            update_data["entry_type"] = entry_data["entry_type"]
        if "title" in entry_data:
            update_data["title"] = entry_data["title"]
        if "description" in entry_data:
            update_data["description"] = entry_data["description"]
        if "fuel_amount" in entry_data:
            update_data["fuel_amount"] = entry_data["fuel_amount"]
        if "fuel_cost" in entry_data:
            update_data["fuel_cost"] = entry_data["fuel_cost"]
        if "fuel_type" in entry_data:
            update_data["fuel_type"] = entry_data["fuel_type"]
        if "trip_distance" in entry_data:
            update_data["trip_distance"] = entry_data["trip_distance"]
        if "trip_purpose" in entry_data:
            update_data["trip_purpose"] = entry_data["trip_purpose"]
        if "expense_amount" in entry_data:
            update_data["expense_amount"] = entry_data["expense_amount"]
        if "expense_category" in entry_data:
            update_data["expense_category"] = entry_data["expense_category"]
        if "mileage" in entry_data:
            update_data["mileage"] = entry_data["mileage"]
        if "entry_date" in entry_data:
            update_data["entry_date"] = entry_data["entry_date"]
        
        if update_data:
            await db.log_entries.update_one(
                {"id": entry_id},
                {"$set": update_data}
            )
        
        return {"status": "success", "message": "Log entry updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating log entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/garage/log/{entry_id}")
async def delete_log_entry(entry_id: str):
    """Удаление записи бортжурнала"""
    try:
        result = await db.log_entries.delete_one({"id": entry_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        return {"status": "success", "message": "Log entry deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting log entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Reminders
@api_router.get("/garage/vehicle/{vehicle_id}/reminders")
async def get_reminders(vehicle_id: str):
    """Получение напоминаний"""
    try:
        reminders = await db.reminders.find(
            {"vehicle_id": vehicle_id},
            {"_id": 0}
        ).sort("is_completed", 1).to_list(1000)
        
        return {
            "status": "success",
            "reminders": reminders,
            "count": len(reminders)
        }
        
    except Exception as e:
        logger.error(f"Error getting reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/garage/vehicle/{vehicle_id}/reminders")
async def add_reminder(vehicle_id: str, reminder_data: dict):
    """Добавление напоминания"""
    try:
        telegram_id = reminder_data.get("telegram_id")
        
        reminder = Reminder(
            vehicle_id=vehicle_id,
            telegram_id=telegram_id,
            reminder_type=reminder_data.get("reminder_type"),
            title=reminder_data.get("title"),
            description=reminder_data.get("description"),
            remind_at_date=reminder_data.get("remind_at_date"),
            remind_at_mileage=reminder_data.get("remind_at_mileage")
        )
        
        doc = reminder.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.reminders.insert_one(doc)
        
        return {"status": "success", "reminder_id": doc['id']}
        
    except Exception as e:
        logger.error(f"Error adding reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/garage/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: str):
    """Отметить напоминание как выполненное"""
    try:
        await db.reminders.update_one(
            {"id": reminder_id},
            {
                "$set": {
                    "is_completed": True,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {"status": "success", "message": "Reminder completed"}
        
    except Exception as e:
        logger.error(f"Error completing reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/garage/reminders/{reminder_id}")
async def update_reminder(reminder_id: str, reminder_data: dict):
    """Редактирование напоминания"""
    try:
        # Проверяем существование напоминания
        existing = await db.reminders.find_one({"id": reminder_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        # Обновляем только переданные поля
        update_data = {}
        if "reminder_type" in reminder_data:
            update_data["reminder_type"] = reminder_data["reminder_type"]
        if "title" in reminder_data:
            update_data["title"] = reminder_data["title"]
        if "description" in reminder_data:
            update_data["description"] = reminder_data["description"]
        if "remind_at_date" in reminder_data:
            update_data["remind_at_date"] = reminder_data["remind_at_date"]
        if "remind_at_mileage" in reminder_data:
            update_data["remind_at_mileage"] = reminder_data["remind_at_mileage"]
        
        if update_data:
            await db.reminders.update_one(
                {"id": reminder_id},
                {"$set": update_data}
            )
        
        return {"status": "success", "message": "Reminder updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/garage/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """Удаление напоминания"""
    try:
        result = await db.reminders.delete_one({"id": reminder_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {"status": "success", "message": "Reminder deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Diagnostics
@api_router.post("/garage/diagnostics")
async def diagnose_obd_code(request: dict):
    """Диагностика OBD-II кода ошибки через Gemini AI"""
    try:
        obd_code = request.get("obd_code")
        vehicle_id = request.get("vehicle_id")
        telegram_id = request.get("telegram_id")
        
        # Получаем информацию об автомобиле
        vehicle = await db.vehicles.find_one({"id": vehicle_id}, {"_id": 0})
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle_info = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
        
        logger.info(f"Starting OBD diagnosis for {obd_code} on {vehicle_info}")
        
        # Проверяем доступен ли AI клиент
        if not ai_client:
            raise HTTPException(status_code=503, detail="AI diagnostics service not available - OpenAI API key not configured")
        
        # Проверяем кэш - может быть уже была диагностика этого кода для этого авто
        cache_key = f"{vehicle_info}_{obd_code}"
        cached = await db.diagnostic_cache.find_one({"cache_key": cache_key}, {"_id": 0})
        
        if cached:
            # Используем кэшированный результат (действителен 7 дней)
            from datetime import timedelta
            cache_date = datetime.fromisoformat(cached['created_at'])
            if datetime.utcnow() - cache_date < timedelta(days=7):
                logger.info(f"Using cached diagnosis for {obd_code}")
                diagnosis = cached['diagnosis']
            else:
                # Кэш устарел
                try:
                    diagnosis = ai_client.diagnose_obd_code(obd_code, vehicle_info)
                    await db.diagnostic_cache.update_one(
                        {"cache_key": cache_key},
                        {"$set": {"diagnosis": diagnosis, "created_at": datetime.utcnow().isoformat()}},
                        upsert=True
                    )
                except Exception as e:
                    logger.error(f"AI diagnosis failed: {str(e)}")
                    diagnosis = cached['diagnosis']  # Используем старый кэш
        else:
            # Новая диагностика
            try:
                diagnosis = ai_client.diagnose_obd_code(obd_code, vehicle_info)
                
                # Сохраняем в кэш
                await db.diagnostic_cache.insert_one({
                    "cache_key": cache_key,
                    "obd_code": obd_code,
                    "vehicle_info": vehicle_info,
                    "diagnosis": diagnosis,
                    "created_at": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"AI diagnosis failed: {str(e)}")
                diagnosis = {
                    "summary": "AI диагностика недоступна",
                    "description": f"Код ошибки: {obd_code}",
                    "possible_causes": ["AI сервис временно недоступен"],
                    "recommended_actions": ["Обратитесь к специалисту для диагностики"],
                    "severity": "unknown"
                }
        
        # Сохраняем диагностику в бортжурнал
        log_entry = LogEntry(
            vehicle_id=vehicle_id,
            telegram_id=telegram_id,
            entry_type="diagnostic",
            title=f"Диагностика OBD-II: {obd_code}",
            description=diagnosis,
            mileage=vehicle.get('mileage', 0),
            entry_date=datetime.utcnow().isoformat()
        )
        
        doc = log_entry.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.log_entries.insert_one(doc)
        
        # Логируем активность
        await log_activity(
            telegram_id,
            "obd_diagnostics",
            {"obd_code": obd_code, "vehicle": vehicle_info}
        )
        
        return {
            "status": "success",
            "obd_code": obd_code,
            "vehicle": vehicle_info,
            "diagnosis": diagnosis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error diagnosing OBD code: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============ ADMIN ENDPOINTS ============

async def log_activity(telegram_id: int, action: str, details: dict = None):
    """Логирование активности пользователя"""
    try:
        # Получаем информацию о пользователе
        user = await db.users.find_one({"telegram_id": telegram_id}, {"_id": 0})
        
        activity = ActivityLog(
            telegram_id=telegram_id,
            username=user.get('username') if user else None,
            name=user.get('name') if user else None,
            action=action,
            details=details or {}
        )
        
        doc = activity.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.activity_logs.insert_one(doc)
        
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")


@api_router.get("/admin/activity")
async def get_activity_logs(limit: int = 100, skip: int = 0):
    """Получение логов активности для админ-панели"""
    try:
        # Получаем логи активности
        logs = await db.activity_logs.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        # Получаем общую статистику
        total_logs = await db.activity_logs.count_documents({})
        total_users = await db.users.count_documents({})
        total_orders = await db.orders.count_documents({})
        
        return {
            "status": "success",
            "logs": logs,
            "total_logs": total_logs,
            "total_users": total_users,
            "total_orders": total_orders,
            "pagination": {
                "limit": limit,
                "skip": skip
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/users")
async def get_all_users():
    """Получение списка всех пользователей"""
    try:
        users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        return {
            "status": "success",
            "users": users,
            "count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/settings")
async def get_settings():
    """Получение настроек системы"""
    try:
        settings = await db.settings.find_one({}, {"_id": 0})
        
        if not settings:
            # Создаём настройки по умолчанию
            default_settings = Settings(markup_percent=0.0)
            doc = default_settings.model_dump()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.settings.insert_one(doc)
            settings = doc
        
        return {
            "status": "success",
            "settings": settings
        }
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/settings")
async def update_settings(request: dict):
    """Обновление настроек системы (наценка)"""
    try:
        markup_percent = request.get('markup_percent', 0)
        telegram_id = request.get('telegram_id')
        
        # Проверяем что это админ
        ADMIN_ID = int(os.environ.get('TELEGRAM_ADMIN_ID', 508352361))
        if telegram_id != ADMIN_ID:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Обновляем или создаём настройки
        settings = await db.settings.find_one({})
        
        if settings:
            await db.settings.update_one(
                {},
                {
                    "$set": {
                        "markup_percent": markup_percent,
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": telegram_id
                    }
                }
            )
        else:
            new_settings = Settings(
                markup_percent=markup_percent,
                updated_by=telegram_id
            )
            doc = new_settings.model_dump()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.settings.insert_one(doc)
        
        # Логируем активность
        await log_activity(
            telegram_id,
            "update_markup",
            {"markup_percent": markup_percent}
        )
        
        return {
            "status": "success",
            "message": "Settings updated",
            "markup_percent": markup_percent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/stats")
async def get_admin_stats():
    """Получение общей статистики для админ-панели"""
    try:
        # Статистика по пользователям
        total_users = await db.users.count_documents({})
        
        # Статистика по заказам
        total_orders = await db.orders.count_documents({})
        total_revenue = 0
        
        orders = await db.orders.find({}, {"total": 1, "_id": 0}).to_list(10000)
        total_revenue = sum(order.get('total', 0) for order in orders)
        
        # Статистика по поискам
        total_searches = await db.search_history.count_documents({})
        
        # Популярные запросы
        pipeline = [
            {"$group": {
                "_id": "$query",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        popular_queries = await db.search_history.aggregate(pipeline).to_list(10)
        
        return {
            "status": "success",
            "stats": {
                "total_users": total_users,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_searches": total_searches
            },
            "popular_queries": popular_queries
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {
        "message": "Market Auto Parts API",
        "version": "1.1.0",
        "status": "running"
    }


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
