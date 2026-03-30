
import httpx
import asyncio
from collections import Counter

BASE_URL = "http://localhost:8000"
API_KEY = "sk_live_qlDNs3nImMnwj-rAXw2DTf9QiMLVEh1i"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def fetch(client, i):
    try:
        res = await client.get(f"{BASE_URL}/api/v1/search/", params={"q": f"test {i}", "limit": 1}, timeout=60.0)
        return res.status_code
    except Exception as e:
        return str(type(e).__name__)

async def run_test():
    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [fetch(client, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        print(Counter(results))

if __name__ == '__main__':
    asyncio.run(run_test())
