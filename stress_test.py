
import httpx
import asyncio
import time
import statistics

BASE_URL = "http://localhost:8000"
API_KEY = "sk_live_qlDNs3nImMnwj-rAXw2DTf9QiMLVEh1i"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def make_request(client, i):
    start = time.time()
    try:
        # Usamos search que es una operación real que usa YTMusic
        res = await client.get(f"{BASE_URL}/api/v1/search/", params={"q": f"song {i}", "limit": 5}, timeout=30.0)
        duration = time.time() - start
        return duration, res.status_code
    except Exception as e:
        return time.time() - start, 500

async def run_stress(concurrency, total):
    print(f"Starting stress test: {total} total requests, {concurrency} concurrent")
    async with httpx.AsyncClient(headers=HEADERS) as client:
        results = []
        for i in range(0, total, concurrency):
            tasks = [make_request(client, j) for j in range(i, min(i + concurrency, total))]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)
            print(f"Progress: {len(results)}/{total}")
            
    durations = [r[0] for r in results]
    statuses = [r[1] for r in results]
    
    print("\n=== STRESS TEST RESULTS ===")
    print(f"Total Requests: {total}")
    print(f"Success (200): {statuses.count(200)}")
    print(f"Errors: {len(statuses) - statuses.count(200)}")
    print(f"Avg Latency: {statistics.mean(durations):.2f}s")
    if len(durations) > 1:
        print(f"P95 Latency: {statistics.quantiles(durations, n=20)[18]:.2f}s")
    print(f"Requests/sec: {total / sum(durations):.2f}")

if __name__ == '__main__':
    asyncio.run(run_stress(10, 30))
