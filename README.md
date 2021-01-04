# Description
NOTE: this is the public version, not the latest version of **jopify**

A simple job scraper. Currently support StackOverflow job board.

# Quick start
Install all dependancies:
```pip install -r requirements.txt```

Django application can be launch by:
```python3 manage.py runserver```

# Dependancies
See requirements.txt. Some main dependencies are:
1. Django (backend framework)
2. Celery (task scheduler)
3. aiohttp (sending async requests)

The project use postgres database, so it requires all the setup related to postgres.

# Road map
1. Creating a public API + website
2. Add more job boards such as HackerNews, Linkedin, etc.
3. Automatically generate CV and Cover letter based on Job Description
4. Create "user database" for website version