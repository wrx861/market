FROM node:20-alpine as build

WORKDIR /app

# Копирование package.json и yarn.lock
COPY package.json yarn.lock ./

# Установка зависимостей
RUN yarn install --frozen-lockfile

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN yarn build

# Production stage
FROM nginx:alpine

# Копирование собранных файлов
COPY --from=build /app/build /usr/share/nginx/html

# Создание конфигурации nginx для SPA
RUN cat > /etc/nginx/conf.d/default.conf << 'NGCONF'
server {
    listen 3000;
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
NGCONF

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
