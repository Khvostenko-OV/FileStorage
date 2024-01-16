# File Storage backend

## Развертывание проекта:

### 1. Настройка сервера Ubuntu

a) Войти на сервер под юзером root

b) Инсталлировать пакеты:

    $ apt update
    $ apt upgrade
    $ apt install postgresql python3-venv python3-pip nginx

c) Настроить Postgress, создать БД:

    $ su postgres
    $ psql
    # ALTER USER postgres WITH PASSWORD 'postgres';
    # CREATE DATABASE filestorage_db;
    # \q

d) Создать рабочего юзера (например www):

    $ adduser www
    $ usermod www -aG sudo

### 2. Деплой бэкенда

a) Войти на сервер под рабочим юзером www

b) Клонировать репозиторий с GitHub:

    $ git clone https://github.com/Khvostenko-OV/FileStorage-backend

c) Создать виртуальную среду:

    $ cd FileStorage-backend
    $ python3 -m venv venv

d) Активировать виртуальную среду:

    $ source venv/bin/activate

e) Создать файл .env с настройками проекта. *Можно использовать шаблон .env_sample*:

    $ mv .env_sample .env
    $ sudo nano .env

f) Выполнить миграции:

    $ python manage.py migrate

g) Собрать статику:

    $ python manage.py collectstatic

h) Создать суперюзера *(не обязательно)*:

    $ python manage.py createsuperuser

### 3. Настройка nginx

a) Создать файл конфигурации:

    $ sudo nano /etc/nginx/sites-available/default

*Пример файла конфигурации:*

    server {
      listen 80;
      server_name IP-сервера;
      location /backend/static/ { root /home/www/FileStorage-backend; }
      location / { proxy_pass http://127.0.0.1:8000; }
    }

b) Настроить права доступа к файлам и папкам в рабочей директрии проекта:

*Находясь в корневой директории юзера:*

    $ sudo chmod 755 FileStorage-backend
    $ cd FileStorage-backend
    $ sudo chmod 644 *
    $ sudo chmod 755 backend

*и далее применить sudo chmod 755 ко всем папкам, вложенным в backend*

c) Запустить nginx:

    $ sudo service nginx start

d) Запустить WSGI:

    $ gunicorn back.wsgi -b 127.0.0.1:8000

e) Остановка WSGI:

    $ fuser -k 8000/tcp

### 4. Деплой фронтенда

a) Клонировать репозиторий:

    $ git clone https://github.com/Khvostenko-OV/FileStorage-frontend

b) Войти в созданную папку. Отредактировать файл .env *(задать один параметр - IP-сервера)*

c) Собрать бандл:

    $ npm run build

d) Войти на сервер под рабочим юзером www

e) Создать директорию и скопировать в нее бандл фронтенда:

    $ mkdir FileStorage-frontend

*Копирование:*

    $ scp -r ./build/* www@IP-сервера:/home/www/FileStorage-frontend/

f) Отредактировать файл конфигурации nginx:

    $ sudo nano /etc/nginx/sites-available/default

*Пример файла конфигурации:*

    server {
      listen 80;
      listen [::]:80;

      server_name IP-сервера;

      location /backend/static/ { root /home/www/FileStorage-backend; }

      location ~*^/(admin|user|storage) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
      }

      location / {
        root /home/www/FileStorage-frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
      }
    }

g) Перезагрузить конфигурационный файл:

    $ sudo nginx -s reload

h) Запустить WSGI:

    $ gunicorn back.wsgi -b 127.0.0.1:8000
