from celery.schedules import crontab

broker_url = 'pyamqp://'
result_backend = 'rpc://'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
enable_utc = True

beat_max_loop_interval = 100000

beat_schedule = {
    "scrape_job": {
        "task": "job_scraper.tasks.scrape_job",
        "schedule": crontab()
    }
}
timezone = "UTC"
