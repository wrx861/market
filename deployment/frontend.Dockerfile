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

# Копирование конфигурации nginx для SPA
RUN echo 'server { \n\
    listen 3000; \n\
    location / { \n\
        root /usr/share/nginx/html; \n\
        index index.html; \n\
        try_files $uri $uri/ /index.html; \n\
    } \n\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
