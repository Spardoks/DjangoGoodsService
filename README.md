# DjangoGoodsService

## Основные моменты

[Референс](https://github.com/netology-code/python-final-diplom)

[Описание сервиса и прогресс его развития](./todo_and_progress.md)

[Текущий функционал сервиса](./todo_and_progress.md#имеющийся-на-текущий-момент-функционал)

## Особенности тестирования

python 3.10+

### Windows

```
git clone https://github.com/Spardoks/DjangoGoodsService.git
cd DjangoGoodsService
ci\run_tests.bat
```

### Unix

```
git clone https://github.com/Spardoks/DjangoGoodsService.git
cd DjangoGoodsService
source ci/run_tests.sh
```

## Особенности использования

Установить python 3.10+

Загрузить репозиторий

Загрузить зависимости
```
pip3 install -r requirements.txt
```

Провести миграции для БД (также в settings.py можно изменить БД, сейчас используется sqllite)
```
python3 manage.py migrate
```

Настроить smpt в settings.py (сейчас он настроен на тестовый aiosmtpd, который можно запустить парраллельно как модуль python для мониторинга почты)

Запустить сервер для приёма запросов (сейчас используется сервер по умолчанию, но можно перед этим заменить на другой)
```
python3 manage.py run_server
```

Посылать запросы (см. пример работы в тестах api)

Можно также зайти по в админку через браузер по пути amin/ или поисследовать сами запросы в браузере, переходя по путям api/v1/*

Для админки может понадобиться superuser, которого можно быстро сделать так
```
python3 manage.py createsuperuser
```