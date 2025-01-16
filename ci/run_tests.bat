py -3.10 -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python manage.py migrate
venv\Scripts\python -m pytest tests