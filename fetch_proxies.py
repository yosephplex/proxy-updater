import requests
import asyncio
import aiohttp
import os
import json
from datetime import datetime

# Configuración
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=3000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=3000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
]

TIMEOUT = 5
TEST_URL = "http://httpbin.org/ip"
IPINFO_URL = "http://ip-api.com/json/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Crear carpetas necesarias
for folder in ["proxies/http", "proxies/socks4", "proxies/socks5", "proxies/by_country", "logs"]:
    os.makedirs(folder, exist_ok=True)

# Obtener proxies
def fetch_all_proxies():
    proxies = {"http": set(), "socks4": set(), "socks5": set()}
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            lines = r.text.strip().split("\n")
            if "socks5" in url:
                proxies["socks5"].update(lines)
            elif "socks4" in url:
                proxies["socks4"].update(lines)
            else:
                proxies["http"].update(lines)
        except Exception as e:
            with open("logs/errors.log", "a") as f:
                f.write(f"[{datetime.utcnow()}] Error al obtener {url}: {e}\n")
    return proxies

# Verificar proxies
async def test_proxy(session, proxy, proxy_type):
    try:
        proxy_url = f"{proxy_type}://{proxy}"
        async with session.get(TEST_URL, proxy=proxy_url, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                data = await resp.json()
                ip = data["origin"]
                geo = requests.get(IPINFO_URL + ip, timeout=5).json()
                return {
                    "proxy": proxy,
                    "type": proxy_type,
                    "ip": ip,
                    "country": geo.get("countryCode", "UNKNOWN")
                }
    except:
        return None

async def validate_proxies(proxies_by_type):
    valid = {"http": [], "socks4": [], "socks5": []}
    by_country = {}

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = []
        for proxy_type, proxies in proxies_by_type.items():
            for proxy in proxies:
                tasks.append(test_proxy(session, proxy.strip(), proxy_type))
        results = await asyncio.gather(*tasks)

    for result in results:
        if result:
            proxy = result["proxy"]
            proxy_type = result["type"]
            country = result["country"]
            valid[proxy_type].append(proxy)

            if country not in by_country:
                by_country[country] = []
            by_country[country].append(proxy)

    return valid, by_country

# Guardar proxies
def save_proxies(valid, by_country):
    for proxy_type, proxies in valid.items():
        path = f"proxies/{proxy_type}/proxies.txt"
        with open(path, "w") as f:
            f.write("\n".join(proxies))

    for country, proxies in by_country.items():
        path = f"proxies/by_country/{country.upper()}.txt"
        with open(path, "w") as f:
            f.write("\n".join(proxies))

    stats = {
        "timestamp": str(datetime.utcnow()),
        "counts": {k: len(v) for k, v in valid.items()},
        "total": sum(len(v) for v in valid.values())
    }
    with open("stats.json", "w") as f:
        json.dump(stats, f, indent=2)

# Principal
def main():
    print("📡 Obteniendo proxies...")
    proxies = fetch_all_proxies()
    print("🧪 Verificando proxies...")
    valid, by_country = asyncio.run(validate_proxies(proxies))
    print("💾 Guardando proxies...")
    save_proxies(valid, by_country)
    print("✅ Listo.")

if __name__ == "__main__":
    main()
