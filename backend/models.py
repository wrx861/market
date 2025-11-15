from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CartItem(BaseModel):
    article: str
    name: str
    brand: str
    price: float
    quantity: int = 1
    delivery_days: Optional[int] = None
    supplier: Optional[str] = None


class Cart(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    telegram_id: int
    items: List[CartItem] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    telegram_id: int
    items: List[CartItem]
    total: float
    status: str = "new"  # new, processing, completed, cancelled
    user_info: dict  # name, phone, delivery address
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    telegram_id: int
    query: str
    search_type: str  # article, vin, ai_search
    results_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ActivityLog(BaseModel):
    """Логирование всех действий пользователей для админ-панели"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    action: str  # 'search_article', 'search_vin', 'add_to_cart', 'create_order', etc.
    details: dict  # Дополнительная информация о действии
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Settings(BaseModel):
    """Настройки системы (наценка и др.)"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    markup_percent: float = 0.0  # Наценка в процентах
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[int] = None  # telegram_id админа


# ============ GARAGE MODELS ============

class Vehicle(BaseModel):
    """Автомобиль в гараже пользователя"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    telegram_id: int
    
    # Основная информация
    make: str  # Марка (Toyota, BMW, etc.)
    model: str  # Модель (Camry, X5, etc.)
    year: int  # Год выпуска
    vin: Optional[str] = None  # VIN номер
    
    # Дополнительная информация
    color: Optional[str] = None
    license_plate: Optional[str] = None  # Гос. номер
    mileage: int = 0  # Текущий пробег в км
    
    # Фото автомобиля
    photo_url: Optional[str] = None
    
    # Даты
    purchase_date: Optional[str] = None  # Дата покупки
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Статус
    is_active: bool = True  # Основное авто или нет


class ServiceRecord(BaseModel):
    """Запись об обслуживании автомобиля"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str  # ID автомобиля
    telegram_id: int
    
    # Информация о сервисе
    service_type: str  # 'oil_change', 'tire_change', 'brake_service', 'general_maintenance', 'repair', 'other'
    title: str  # Название работы
    description: Optional[str] = None  # Описание
    
    # Детали
    mileage: int  # Пробег на момент обслуживания
    cost: float = 0.0  # Стоимость
    service_date: str  # Дата обслуживания (ISO format)
    
    # Исполнитель
    service_provider: Optional[str] = None  # СТО или самостоятельно
    
    # Запчасти
    parts_used: Optional[List[str]] = None  # Список использованных запчастей
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LogEntry(BaseModel):
    """Запись в бортжурнале"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str
    telegram_id: int
    
    # Тип записи
    entry_type: str  # 'refuel', 'trip', 'note', 'expense', 'diagnostic'
    
    # Основная информация
    title: str
    description: Optional[str] = None
    
    # Для заправок
    fuel_amount: Optional[float] = None  # Литры
    fuel_cost: Optional[float] = None  # Стоимость
    fuel_type: Optional[str] = None  # АИ-92, АИ-95, etc.
    
    # Для поездок
    trip_distance: Optional[int] = None  # Км
    trip_purpose: Optional[str] = None
    
    # Для расходов
    expense_amount: Optional[float] = None
    expense_category: Optional[str] = None  # 'fuel', 'service', 'parking', 'fines', 'insurance', 'other'
    
    # Общее
    mileage: int  # Пробег на момент записи
    entry_date: str  # Дата записи (ISO format)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Reminder(BaseModel):
    """Напоминание об обслуживании"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str
    telegram_id: int
    
    # Информация о напоминании
    reminder_type: str  # 'service', 'insurance', 'inspection', 'custom'
    title: str
    description: Optional[str] = None
    
    # Когда напомнить
    remind_at_date: Optional[str] = None  # Дата (ISO format)
    remind_at_mileage: Optional[int] = None  # Пробег
    
    # Статус
    is_completed: bool = False
    completed_at: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Request/Response Models
class SearchArticleRequest(BaseModel):
    article: str
    telegram_id: int
    availability_filter: Optional[str] = None  # 'in_stock_tyumen', 'on_order', None
    sort_by: Optional[str] = None  # 'price_asc', 'price_desc', 'delivery_asc', None


class SearchVINRequest(BaseModel):
    vin: str
    telegram_id: int


class AISearchRequest(BaseModel):
    query: str
    vin: str
    telegram_id: int


class AddToCartRequest(BaseModel):
    telegram_id: int
    item: CartItem


class UpdateCartItemRequest(BaseModel):
    telegram_id: int
    article: str
    quantity: int


class RemoveFromCartRequest(BaseModel):
    telegram_id: int
    article: str


class CreateOrderRequest(BaseModel):
    telegram_id: int
    user_info: dict  # {"name": "", "phone": "", "address": ""}


class PartInfo(BaseModel):
    article: str
    name: str
    brand: str
    price: float
    delivery_days: int
    availability: str
    supplier: str