import asyncio
import time
import httpx

async def fire_request(client, url):
    await client.get(url)

async def run_benchmark(endpoint_name: str, url: str, concurrency: int = 20):
    print(f"Firing {concurrency} concurrent requests to {endpoint_name}...")
    
    start_time = time.time()
    
    # httpx.AsyncClient allows us to make concurrent HTTP requests
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fire_request(client, url) for _ in range(concurrency)]
        await asyncio.gather(*tasks) # Execute all 20 simultaneously
        
    total_time = time.time() - start_time
    print(f"Result for {endpoint_name}: {total_time:.2f} seconds\n")

async def main():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Test the blocked event loop
    await run_benchmark("BAD ENDPOINT", f"{base_url}/test-bad-async")
    
    # 2. Test the correctly yielding event loop
    await run_benchmark("GOOD ENDPOINT", f"{base_url}/test-good-async")

if __name__ == "__main__":
    asyncio.run(main())
    