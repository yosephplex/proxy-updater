fetch_proxies.py mejorado con asyncio, aiohttp y detección por país

import asyncio import aiohttp import os import re from datetime import datetime from aiohttp import ClientTimeout

=== CONFIGURACIÓN ===

SOURCES = { "http": [ "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all", "https://www.proxy-list.download/api/v1/get?type=http", ], "socks4": [ "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=3000&country=all", ], "socks5": [ "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=3000&country=all", ] }

API_GEO = "http://ip-api.com/json/{}?fields=countryCode" CONCURRENCY = 100 TIMEOUT = 10

=== FUNCIONES ===

async def fetch_url(session, url): try: async with session.get(url) as response: text = await response.text() return text.strip().splitlines() except: return []

async def validate_proxy(session, proxy, proxy_type): try: proxy_url = f"{proxy_type}://{proxy}" async with session.get("http://example.com", proxy=proxy_url, timeout=ClientTimeout(total=TIMEOUT)) as resp: if resp.status == 200: return proxy except: return None

async def get_country(session, ip): try: async with session.get(API_GEO.format(ip), timeout=ClientTimeout(total=5)) as resp: data = await resp.json() return data.get("countryCode") except: return None

async def process_type(session, proxy_type, urls): proxies = set() for url in urls: lines = await fetch_url(session, url) proxies.update([p for p in lines if re.match(r"\d+.\d+.\d+.\d+:\d+", p)])

print(f"{proxy_type.upper()} - Total descargados: {len(proxies)}")

sem = asyncio.Semaphore(CONCURRENCY)
results = []

async def check(proxy):
    async with sem:
        valid = await validate_proxy(session, proxy, proxy_type)
        if valid:
            country = await get_country(session, proxy.split(":")[0])
            results.append((valid, country))

await asyncio.gather(*(check(p) for p in proxies))
return results

async def main(): os.makedirs("proxies", exist_ok=True) async with aiohttp.ClientSession() as session: all_results = {"http": [], "socks4": [], "socks5": []}

for proxy_type, urls in SOURCES.items():
        results = await process_type(session, proxy_type, urls)
        all_results[proxy_type].extend(results)

        # Guardar por tipo
        with open(f"proxies/{proxy_type}.txt", "w") as f:
            for proxy, _ in results:
                f.write(f"{proxy}\n")

    # Guardar por país
    country_map = {}
    for proxy_type, proxies in all_results.items():
        for proxy, country in proxies:
            if not country:
                continue
            path = f"proxies/by_country/{country.upper()}"
            os.makedirs(path, exist_ok=True)
            with open(f"{path}/{proxy_type}.txt", "a") as f:
                f.write(f"{proxy}\n")

    print("Proceso finalizado.")

if name == "main": asyncio.run(main())

