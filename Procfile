web: gunicorn app:app
worker: celery worker --app=app.celery -l INFO
