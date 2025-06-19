import os
from BugsfreeStreams.collector import run_collector

source_urls = [os.environ['M3U_SOURCE']]

# filtro personalizzato per contenuti ITA
def keep_only_italian_channels(extinf_line: str) -> bool:
    lowered = extinf_line.lower()
    return 'it|' in lowered or '.it' in lowered

run_collector(
    country_name="MyList",                  # cartella di output
    source_urls=source_urls,
    skip_keywords=[],                       # ← non escludiamo nulla
    filter_function=keep_only_italian_channels,  # ← funzione personalizzata per selezione ITA
)
