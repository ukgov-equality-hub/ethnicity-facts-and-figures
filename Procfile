web: gunicorn -b 0.0.0.0:$PORT application.wsgi:app

release: python manage.py db upgrade