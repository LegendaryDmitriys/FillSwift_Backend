FillSwift

Описание
Этот проект разработан с использованием Django, веб-фреймворка для Python. Он представляет собой cерверную часть FillSwift.

Установка
Склонируйте репозиторий:
bash
Copy code
git clone https://github.com/LegendaryDmitriys/FillSwift_Backend
Установите зависимости:
bash
Copy code
pip install -r requirements.txt
Выполните миграции базы данных:
bash
Copy code
python manage.py migrate
Запустите локальный сервер:
bash
Copy code
python manage.py runserver
Использование
После запуска сервера вы сможете открыть приложение в вашем веб-браузере по адресу http://localhost:8000.

Структура проекта
backend: Основное приложение проекта.
authenticate: Приложение авторизации проекта
Gas/: Основной каталог проекта.
templates/: HTML шаблоны.
media/: шрифты, pdf, изображения.
manage.py: Файл для управления проектом Django.

Лицензия
Этот проект лицензирован под [FillSwift].
