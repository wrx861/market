import requests
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        self.admin_id = os.environ['TELEGRAM_ADMIN_ID']
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_order_notification(self, order_data: Dict) -> bool:
        """
        Отправка уведомления о новом заказе напрямую админу в Telegram
        """
        try:
            # Форматируем сообщение
            items_text = ""
            for i, item in enumerate(order_data.get('items', []), 1):
                items_text += f"\n{i}. {item['name']} ({item['brand']})"
                items_text += f"\n   Артикул: {item['article']}"
                items_text += f"\n   Цена: {item['price']:,} ₽ × {item['quantity']} шт. = {item['price'] * item['quantity']:,} ₽\n"
            
            user_info = order_data.get('user_info', {})
            address_text = f"\n📍 Адрес: {user_info.get('address')}" if user_info.get('address') else ""
            
            message = f"""🆕 <b>НОВЫЙ ЗАКАЗ №{order_data.get('order_id', '')[:8]}</b>

💰 <b>Сумма: {order_data.get('total', 0):,} ₽</b>

👤 Клиент: {user_info.get('name', 'Не указано')}
📞 Телефон: {user_info.get('phone', 'Не указано')}{address_text}

📦 <b>Товары:</b>{items_text}

🆔 Telegram ID: {order_data.get('telegram_id')}
⏰ Дата: {order_data.get('created_at', '')}"""
            
            # Отправляем сообщение
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.admin_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Order notification sent successfully: {order_data.get('order_id')}")
                return True
            else:
                logger.error(f"Failed to send notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending order notification: {str(e)}")
            return False
    
    def send_message_to_user(self, telegram_id: int, message: str) -> bool:
        """
        Отправка сообщения конкретному пользователю
        """
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": telegram_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error sending message to user: {str(e)}")
            return False