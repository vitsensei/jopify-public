import asyncio
import time
from pprint import pprint

from jopify.celery import app
from job_scraper.models import *
from scraper.stackoverflow import StackOverflowScrapper


def create_new_job(job):
    if "technology" in job:
        for key in job["technology"]:
            job[key] = job["technology"][key]

        job.pop("technology", None)

    return Job(**job)


@app.task
def scrape_job():
    start = time.time()
    scraper = StackOverflowScrapper()

    jobs = asyncio.run(scraper.extract_jobs())
    for job in jobs:
        if not Job.objects.filter(url=job["url"]).exists():
            new_job = create_new_job(job)

            new_job.save()

    print(f"Elapsed time for {len(jobs)} jobs ({scraper.n_failed_request} failed.): {time.time() - start}")


if __name__ == '__main__':
    scrape_job()