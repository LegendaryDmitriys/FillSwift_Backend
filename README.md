## FillSwift

### Описание
Этот проект разработан с использованием Django, веб-фреймворка для Python. Он представляет собой cерверную часть FillSwift.

### Установка

1. Склонируйте репозиторий: 
 
```git clone https://github.com/LegendaryDmitriys/FillSwift_Backend```


2. Установите зависимости:

```python pip install -r requirements.txt```

3. Выполните миграции базы данных:

```python manage.py migrate```

4. Запустите локальный сервер:

```python manage.py runserver``` 

5. Использование После запуска сервера вы сможете открыть приложение в вашем веб-браузере по адресу http://localhost:8000.

### Структура проекта

* backend: Основное приложение проекта. 
* authenticate: Приложение авторизации проекта
* Gas/: Основной каталог проекта. templates/: 
* HTML шаблоны. media/: шрифты, pdf, изображения. 
* manage.py: Файл для управления проектом Django.

### Лицензия 
Этот проект лицензирован под [FillSwift].
