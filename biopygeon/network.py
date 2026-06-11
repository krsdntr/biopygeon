import requests
import requests_cache
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from datetime import timedelta
from pathlib import Path
import urllib3

# Setup Cache
CACHE_DIR = Path.home() / ".biopygeon" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "http_cache"

cached_session = requests_cache.CachedSession(
    str(CACHE_FILE),
    expire_after=timedelta(days=7),
    allowable_codes=[200],
    allowable_methods=['GET', 'POST']
)

def is_retryable_exception(e):
    if isinstance(e, requests.exceptions.RequestException):
        if e.response is not None and e.response.status_code in [429, 500, 502, 503, 504]:
            return True
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            return True
    if isinstance(e, (urllib3.exceptions.ProtocolError, urllib3.exceptions.MaxRetryError)):
        return True
    return False

standard_retry = retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception)
)
