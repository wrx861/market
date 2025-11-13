import requests
import os
from typing import Optional, Dict, List
import logging
import json
import re

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Новый REST API endpoint для Gemini 2.0 Flash
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
    
    def analyze_car_info(self, car_info: Dict) -> Dict:
        """
        Анализ информации об автомобиле
        """
        try:
            prompt = f"""
            Проанализируй информацию об автомобиле и верни её в структурированном виде.
            
            Данные:
            - Марка: {car_info.get('make', 'N/A')}
            - Модель: {car_info.get('model', 'N/A')}
            - Год: {car_info.get('year', 'N/A')}
            - Двигатель: {car_info.get('engine', 'N/A')}
            - Детали двигателя: {car_info.get('engine_details', 'N/A')}
            - КПП: {car_info.get('transmission', 'N/A')}
            
            Верни JSON: {{"make": "", "model": "", "year": "", "generation": "", "engine_type": ""}}
            Только JSON, без текста.
            """
            
            result_text = self.analyze_text(prompt)
            result_text = self._clean_json_response(result_text)
            result = json.loads(result_text)
            
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
        Поиск запчасти по описанию через REST API
        """
        try:
            car_desc = f"{car_info.get('make')} {car_info.get('model')} {car_info.get('year')}"
            if car_info.get('engine'):
                car_desc += f" двигатель {car_info.get('engine')}"
            
            prompt = f"""
            Ты - эксперт по автозапчастям.
            
            Автомобиль: {car_desc}
            Запрос: "{part_query}"
            
            Каталог:
            {catalog_content[:5000]}
            
            ЗАДАЧА: Найди артикулы запчастей в каталоге.
            Артикулы выглядят как: "1K0505435Q", "8E0407151A"
            
            Верни JSON массив: ["артикул1", "артикул2"]
            Если не нашел - []. Только JSON.
            """
            
            result_text = self.analyze_text(prompt)
            result_text = self._clean_json_response(result_text)
            articles = json.loads(result_text)
            
            if not isinstance(articles, list):
                return []
            
            valid_articles = []
            for art in articles:
                if isinstance(art, str) and re.match(r'^[A-Z0-9\-\.]{4,20}$', art, re.I):
                    valid_articles.append(art.upper())
            
            logger.info(f"Found {len(valid_articles)} articles")
            return valid_articles[:5]
            
        except Exception as e:
            logger.error(f"Error finding part: {str(e)}")
            return []
    
    def analyze_text(self, prompt: str) -> str:
        """
        Универсальный метод для анализа текста через REST API
        """
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error in analyze_text: {str(e)}")
            return f"Ошибка анализа: {str(e)}"
    
    def diagnose_obd_with_grounding(self, obd_code: str, vehicle_info: str) -> str:
        """
        Диагностика OBD-II кода через REST API с поиском в интернете
        """
        try:
            # Формируем запрос для поиска в интернете
            prompt = f"""Найди актуальную информацию в интернете о коде ошибки OBD-II {obd_code} для автомобиля {vehicle_info}.

На основе найденной информации предоставь детальный анализ:

**1. Расшифровка кода {obd_code}**
Что означает этот код ошибки?

**2. Возможные причины для {vehicle_info}**
Перечисли все возможные причины появления этой ошибки конкретно для данного автомобиля.

**3. Симптомы**
Какие признаки и симптомы может заметить водитель?

**4. Рекомендации по устранению**
Пошаговые действия для устранения проблемы:
- Что можно проверить самостоятельно
- Что требует СТО
- Последовательность диагностики

**5. Срочность**
Оцени уровень срочности: Критическая / Важная / Умеренная / Низкая
Объясни почему и какие риски при игнорировании.

**6. Примерная стоимость ремонта**
Укажи примерную стоимость ремонта в рублях для России (минимальная и максимальная).

**7. Можно ли ездить**
Можно ли продолжать эксплуатацию автомобиля с этой ошибкой? Да/Нет и почему.

Ответь на русском языке, подробно и структурированно. Используй актуальную информацию из интернета."""

            # Формируем payload с grounding tools
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "tools": [
                    {
                        "google_search_retrieval": {}
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            
            # Пытаемся использовать grounding
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"OBD diagnosis with grounding completed for {obd_code}")
                return text.strip()
                
            except Exception as grounding_error:
                # Если grounding не работает, используем обычный запрос
                logger.warning(f"Grounding not available, using standard generation: {str(grounding_error)}")
                return self.analyze_text(prompt)
            
        except Exception as e:
            logger.error(f"Error in diagnose_obd_with_grounding: {str(e)}")
            
            # Fallback - простой анализ
            fallback_prompt = f"""Проанализируй код ошибки OBD-II {obd_code} для {vehicle_info}.

Предоставь:
1. Расшифровку кода
2. Основные причины
3. Рекомендации по устранению
4. Примерную стоимость ремонта в рублях

Ответь кратко на русском языке."""
            
            try:
                result = self.analyze_text(fallback_prompt)
                return f"⚠️ Информация из базы знаний (без поиска в интернете):\n\n{result}"
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                return f"❌ Ошибка диагностики: {str(fallback_error)}\n\nПожалуйста, попробуйте позже или обратитесь в СТО."
    
    def _clean_json_response(self, text: str) -> str:
        """
        Очистка JSON от markdown
        """
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        return text.strip()
