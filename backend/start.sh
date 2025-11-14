#!/bin/bash

# Запуск FastAPI сервера в фоне
uvicorn server:app --host 0.0.0.0 --port 8001 &

# Небольшая задержка чтобы сервер успел запуститься
sleep 5

# Запуск Telegram бота
python telegram_bot.py &

# Ожидаем завершения любого из процессов
wait -n

# Если один процесс упал, останавливаем другой
exit $?
