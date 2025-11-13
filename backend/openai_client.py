import os
from typing import Optional, Dict, List
import logging
import json
import re
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Используем gpt-4o для более качественных ответов
        self.model = "gpt-4o"
        # Для простых задач можно использовать gpt-4o-mini
        self.mini_model = "gpt-4o-mini"
    
    def diagnose_obd_code(self, obd_code: str, vehicle_info: str) -> str:
        """
        Диагностика OBD-II кода ошибки через OpenAI API
        """
        try:
            logger.info(f"Starting OBD diagnosis for {obd_code} on {vehicle_info}")
            
            # Детальный промпт для диагностики OBD кода
            prompt = f"""Ты - эксперт автомеханик с 20-летним опытом диагностики автомобилей в городе Тюмень.

Автомобиль: {vehicle_info}
Код ошибки OBD-II: {obd_code}

Предоставь детальный анализ этого кода ошибки специально для данного автомобиля.

ВАЖНО: Ответ должен быть БЕЗ markdown форматирования (без **, ##, ###). Используй только обычный текст, эмодзи и переносы строк для структуры.

Структура ответа для мобильного телефона:

🔍 РАСШИФРОВКА КОДА {obd_code}

(Полное техническое название и объяснение что означает этот код)


⚙️ ВОЗМОЖНЫЕ ПРИЧИНЫ ДЛЯ {vehicle_info}

(Перечисли наиболее вероятные причины в порядке убывания вероятности. Каждую причину с новой строки с символом •)

• Причина 1
• Причина 2
• Причина 3


📊 СИМПТОМЫ

(Какие признаки может заметить водитель. Каждый симптом с новой строки)

• Изменения в работе двигателя
• Звуки, вибрации
• Индикаторы на панели
• Расход топлива и динамика


🔧 РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ

Что проверить первым делом:
• Шаг 1
• Шаг 2
• Шаг 3

Можно сделать самостоятельно:
• Действие 1
• Действие 2

Требует обращения в СТО:
• Процедура 1
• Процедура 2


💰 СТОИМОСТЬ РЕМОНТА В ТЮМЕНИ

Минимальная: от X,XXX руб.
(описание простого случая)

Средняя: от X,XXX до X,XXX руб.
(описание типичного случая)

Максимальная: до XX,XXX руб.
(описание сложного случая)

Время работы: X-X часов


Ответ должен быть детальным, структурированным и ЛЕГКО ЧИТАТЬСЯ НА ТЕЛЕФОНЕ. Без лишних символов форматирования. Используй простой текст, эмодзи и переносы строк. Каждый раздел отделяй двумя переносами строк."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - опытный автомеханик-диагност с глубокими знаниями OBD-II систем. Твои ответы всегда точные, детальные и практичные. Ты даешь конкретные рекомендации основанные на реальном опыте."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            diagnosis = response.choices[0].message.content
            logger.info(f"OBD diagnosis completed for {obd_code}, length: {len(diagnosis)} chars")
            
            return diagnosis.strip()
            
        except Exception as e:
            logger.error(f"Error in diagnose_obd_code: {str(e)}")
            
            # Fallback - простой анализ
            try:
                fallback_prompt = f"""Проанализируй код ошибки OBD-II {obd_code} для {vehicle_info}.

Предоставь краткую информацию:
1. Что означает этот код
2. Основные причины
3. Рекомендации по устранению
4. Примерная стоимость ремонта в рублях

Ответь структурированно на русском языке."""
                
                fallback_response = self.client.chat.completions.create(
                    model=self.mini_model,
                    messages=[
                        {"role": "user", "content": fallback_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                result = fallback_response.choices[0].message.content
                return f"⚠️ Базовая информация:\n\n{result}"
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                return f"❌ Ошибка диагностики: {str(fallback_error)}\n\nПожалуйста, попробуйте позже или обратитесь в СТО."
    
    def analyze_text(self, prompt: str, use_mini: bool = False) -> str:
        """
        Универсальный метод для анализа текста
        """
        try:
            model = self.mini_model if use_mini else self.model
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error in analyze_text: {str(e)}")
            return f"Ошибка анализа: {str(e)}"
    
    def analyze_car_info(self, car_info: Dict) -> Dict:
        """
        Анализ информации об автомобиле
        """
        try:
            prompt = f"""Проанализируй информацию об автомобиле и верни её в структурированном виде.

Данные:
- Марка: {car_info.get('make', 'N/A')}
- Модель: {car_info.get('model', 'N/A')}
- Год: {car_info.get('year', 'N/A')}
- Двигатель: {car_info.get('engine', 'N/A')}
- Детали двигателя: {car_info.get('engine_details', 'N/A')}
- КПП: {car_info.get('transmission', 'N/A')}

Верни только JSON без дополнительного текста:
{{"make": "", "model": "", "year": "", "generation": "", "engine_type": ""}}"""
            
            result_text = self.analyze_text(prompt, use_mini=True)
            result_text = self._clean_json_response(result_text)
            result = json.loads(result_text)
            
            # Добавляем дополнительные поля
            result.update({
                'engine_code': car_info.get('engine'),
                'engine_details': car_info.get('engine_details'),
                'transmission': car_info.get('transmission'),
                'production_period': car_info.get('production_period')
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing car info: {str(e)}")
            return car_info
    
    def find_part_by_description(self, car_info: Dict, part_query: str, catalog_content: str) -> List[str]:
        """
        Поиск запчасти по описанию
        """
        try:
            car_desc = f"{car_info.get('make')} {car_info.get('model')} {car_info.get('year')}"
            if car_info.get('engine'):
                car_desc += f" двигатель {car_info.get('engine')}"
            
            prompt = f"""Ты - эксперт по автозапчастям.

Автомобиль: {car_desc}
Запрос пользователя: "{part_query}"

Каталог доступных запчастей:
{catalog_content[:5000]}

ЗАДАЧА: Найди в каталоге артикулы запчастей, которые соответствуют запросу пользователя.
Артикулы обычно выглядят так: "1K0505435Q", "8E0407151A", "51750A6000"

Верни только JSON массив артикулов без дополнительного текста:
["артикул1", "артикул2", "артикул3"]

Если ничего не нашёл, верни пустой массив: []"""
            
            result_text = self.analyze_text(prompt, use_mini=True)
            result_text = self._clean_json_response(result_text)
            articles = json.loads(result_text)
            
            if not isinstance(articles, list):
                return []
            
            # Валидация артикулов
            valid_articles = []
            for art in articles:
                if isinstance(art, str) and re.match(r'^[A-Z0-9\-\.]{4,20}$', art, re.I):
                    valid_articles.append(art.upper())
            
            logger.info(f"Found {len(valid_articles)} articles for query: {part_query}")
            return valid_articles[:5]
            
        except Exception as e:
            logger.error(f"Error finding part: {str(e)}")
            return []
    
    def _clean_json_response(self, text: str) -> str:
        """
        Очистка JSON от markdown форматирования
        """
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        return text.strip()
