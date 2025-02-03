python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python manage.py migrate
./venv/bin/python -m pytest tests