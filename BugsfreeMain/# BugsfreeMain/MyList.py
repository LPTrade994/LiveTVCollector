# BugsfreeMain/MyList.py
import os

source_urls = [os.environ['M3U_SOURCE']]   # ← prende l'URL dal segreto

skip_keywords = ["vod", "movie", "serie", "film", "catchup"]

from BugsfreeStreams.collector import run_collector
run_collector(country_name="MyList", source_urls=source_urls,
              skip_keywords=skip_keywords)
