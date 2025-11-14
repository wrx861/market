# 🚀 Быстрое обновление - Шпаргалка

## Обновить приложение после изменений в GitHub

```bash
cd /root/market-auto-parts
bash deployment/update.sh
```

## Создать быструю команду (один раз)

```bash
echo 'alias update-app="cd /root/market-auto-parts && bash deployment/update.sh"' >> ~/.bashrc
source ~/.bashrc
```

Теперь просто:
```bash
update-app
```

## Полезные команды

```bash
# Перейти в директорию проекта
cd /root/market-auto-parts/deployment

# Статус контейнеров
docker-compose ps

# Логи backend
docker-compose logs -f backend

# Логи frontend  
docker-compose logs -f frontend

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Откат к предыдущей версии

```bash
cd /root/market-auto-parts
git log --oneline
git reset --hard <commit-hash>
bash deployment/update.sh
```

---

📖 Подробная инструкция: `deployment/UPDATE_INSTRUCTIONS.md`
