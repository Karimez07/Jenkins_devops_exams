import os
import httpx

CAST_SERVICE_HOST_URL = 'http://localhost:8002/api/v1/casts/'

def is_cast_present(cast_id: int):
    base_url = os.environ.get('CAST_SERVICE_HOST_URL') or CAST_SERVICE_HOST_URL
    cast_url = f"{base_url.rstrip('/')}/{cast_id}/"
    r = httpx.get(cast_url)
    return True if r.status_code == 200 else False
