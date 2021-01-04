import logging
import re
import asyncio

import requests
import aiohttp
from bs4 import BeautifulSoup as bs

from scraper.rate_limiter import RateLimiter


# def setup_logger(name, log_file, level=logging.INFO):
#     """To setup as many loggers as you want"""
#
#     handler = logging.FileHandler(log_file)
#     handler.setFormatter(logging.Formatter('%(message)s'))
#
#     logger = logging.getLogger(name)
#     logger.setLevel(level)
#     logger.addHandler(handler)
#
#     return logger
#
#
# logger1 = setup_logger("unidentified_tech", "unidentified_tech.log")
# # logger2 = setup_logger("all_tech", "all_tech.log")


TECHNOLOGY = {
    "language": ("javascript",
                 "html",
                 "css",
                 "sql",
                 "python",
                 "java",
                 "bash",
                 "shell",
                 "powershell",
                 "c#",
                 "php",
                 "c++",
                 "typescript",
                 "c",
                 "ruby",
                 "go",
                 "assembly",
                 "swift",
                 "kotlin",
                 "r",
                 "vba",
                 "objectivec",
                 "scala",
                 "rust",
                 "dart",
                 "elixir",
                 "clojure",
                 "webassembly",
                 "html5"),
    "framework": ("react",
                  "vue",
                  "express",
                  "spring",
                  "django",
                  "flask",
                  "laravel",
                  "angular",
                  "rails",
                  "jquery",
                  "drupal",
                  "net",
                  "pytorch",
                  "flutter",
                  "pandas",
                  "tensorflow",
                  "node",
                  "spark",
                  "ansible",
                  "unity",
                  "unreal",
                  "hadoop",
                  "xamarin",
                  "cryengine",
                  "puppet",
                  "cordova",
                  "chef",
                  "jquery",
                  "amphp",
                  "mobx",
                  "meteor",
                  "selenium"),
    "database": ("mongo",
                 "postgre",
                 "elastic",
                 "redis",
                 "mysql",
                 "firebase",
                 "sqlite",
                 "cassandra",
                 "dynamo",
                 "maria",
                 "oracle",
                 "couchbase"),
    "tool": ("linux",
             "docker",
             "kubernetes",
             "aws",
             "macos",
             "ios",
             "gcp",
             "azure",
             "android",
             "windows",
             "heroku",
             "blockchain",
             "raspberry",
             "wordpress",
             "jenkins",
             "webpack",
             "jvm",
             "openshift")
}


def normalise_jobs(f):
    def classify_technology(tech, label):
        classified = False
        best_matching_score = 0
        best_matching_tech = None
        for recorded_tech in TECHNOLOGY[label]:
            if recorded_tech in tech:
                classified = True
                current_score = len(recorded_tech) / len(tech)
                if best_matching_score < current_score:
                    best_matching_score = current_score
                    best_matching_tech = recorded_tech

        return classified, best_matching_score, best_matching_tech

    async def wrapper(*args):
        jobs = await f(*args)

        # Remove empty job (because of throttling)
        jobs = [job for job in jobs if len(job) > 0]

        # Normalise all the fields
        for job in jobs:
            if "company_name" in job:
                pass

            if "location" in job:
                r = re.compile(r"[A-Z][a-z]+")
                cities_and_countries = r.findall(job["location"])
                if len(cities_and_countries) == 0:
                    job.pop("location", None)

                else:
                    job["location"] = " ".join(cities_and_countries)

            if "job_title" in job:
                preferred_job_title = ""

                if "backend" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Backend "
                elif "frontend" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Frontend "
                elif "data" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Data "
                elif "machine learning" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Machine Learning "

                if "engineer" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Engineer"
                elif "developer" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Developer"
                elif "scientist" in job["job_title"].lower():
                    preferred_job_title = preferred_job_title + "Scientist"

                preferred_job_title = preferred_job_title.strip()
                if len(preferred_job_title) > 0:
                    job["job_title"] = preferred_job_title

            if "technology" in job:
                # Further segment this into 4 fields:
                #   - language
                #   - framework
                #   - database
                #   - tool

                new_classify = dict()

                for tech in job["technology"]:
                    scores = []
                    found = []
                    recorded_techs = []
                    labels = ["language", "framework", "database", "tool"]

                    for label in labels:
                        is_classified, match_score, match_tech = classify_technology(tech, label)
                        scores.append(match_score)
                        found.append(is_classified)
                        recorded_techs.append(match_tech)

                    if any(found):
                        ind = scores.index(max(scores))
                        best_label = labels[ind]
                        best_tech = recorded_techs[ind]

                        if best_label not in new_classify:
                            new_classify[best_label] = []

                        new_classify[best_label].append(best_tech)
                    else:
                        pass
                        # logger1.info(tech)

                if len(new_classify) > 0:
                    job["technology"] = new_classify
                else:
                    job.pop("technology", None)

        return jobs

    return wrapper


class StackOverflowScrapper():
    def __init__(self):
        self._url = r"https://stackoverflow.com/jobs"
        self._regex_pattern = r"jobs\/\d+\/"
        self.n_failed_request = 0

    async def _find_job_urls_single_page(self, session, url):
        r = await session.get(url)
        if r.status == 200:
            soup = bs(await r.text(), "lxml")

            a = soup.find_all("a", href=re.compile(self._regex_pattern))
            urls = []
            for url in a:
                urls.append(self._url + url["href"][5:])

            return urls

        else:
            self.n_failed_request += 1
            return None

    async def _find_job_urls(self, session):
        job_urls = []

        number_of_pages = 5
        page_urls = [self._url + f"/?pg={i}" for i in range(number_of_pages)]
        job_urls_lists = await asyncio.gather(*(self._find_job_urls_single_page(session, page_urls[i]) for i in range(number_of_pages)))

        for l in job_urls_lists:
            if l is not None:
                job_urls.extend(l)

        if len(job_urls) == 0:
            return None
        else:
            return job_urls

    async def _extract_job_from_url(self, session, url, headers):
        def tag_with_job_description(tag):
            return tag.name == "h2" and "Job description" in tag.text

        def tag_with_company_name(tag):
            if tag.name == "a":
                if tag.has_attr("class"):
                    if "employer" in tag["class"]:
                        return True
                    elif tag.has_attr("href"):
                        return re.search(r"\/jobs\/companies\/\w+", tag["href"])

            return False

        def tag_with_job_details_header(tag):
            if tag.has_attr("class") and tag.name == "header":
                return "job-details--header" in tag["class"]

        r = await session.get(url, headers=headers)

        job = {}

        if r.status == 200:
            job["url"] = url
            soup = bs(await r.text(), "lxml")

            job_description_header = soup.find(tag_with_job_details_header)
            if job_description_header is not None:
                # Company name
                company_name_tag = job_description_header.find(tag_with_company_name)
                job["company_name"] = company_name_tag.get_text()

                # Job location
                job["location"] = company_name_tag.next_sibling.next_sibling.get_text()

                # Job tite
                job["job_title"] = job_description_header.find("a", href=re.compile(r"jobs\/\d+\/")).get_text()

            # Technologies
            technologies = [text for text in soup.find("h2", text="Technologies").next_sibling.next_sibling.stripped_strings]
            job["technology"] = technologies

        else:
            self.n_failed_request += 1

        if len(job) == 0:
            return None

        return job

    @normalise_jobs
    async def extract_jobs(self):
        async with aiohttp.ClientSession() as session:
            session = RateLimiter(session)
            urls = await self._find_job_urls(session)

            headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
            if urls is not None:
                tasks = (self._extract_job_from_url(session, url, headers) for url in urls)
                jobs = await asyncio.gather(*tasks)
                jobs = [job for job in jobs if job is not None]

                return jobs

            else:
                return None


def main():
    from pprint import pprint
    import time

    start = time.time()
    scraper = StackOverflowScrapper()

    jobs = asyncio.run(scraper.extract_jobs())

    import json
    f = open("jobs.json", "w")
    f.write(json.dumps(jobs))
    f.close()

    pprint(jobs)
    print(f"Elapsed time for {len(jobs)} jobs ({scraper.n_failed_request} failed.): {time.time() - start}")


if __name__ == '__main__':
    main()