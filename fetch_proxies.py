import requests
from pathlib import Path
import time

# Crear carpetas si no existen
Path("by_type").mkdir(exist_ok=True)
Path("by_country").mkdir(exist_ok=True)

# Fuentes públicas de proxies
SOURCES = {
    "http": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    ],
    "socks4": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=3000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    ],
    "socks5": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=3000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    ],
}

# Países específicos
COUNTRIES = {
    "MX": "Mexico",
    "CL": "Chile",
    "AR": "Argentina",
}

def fetch_and_filter():
    all_proxies = {"http": set(), "socks4": set(), "socks5": set()}
    for proxy_type, urls in SOURCES.items():
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    for line in r.text.strip().splitlines():
                        if ":" in line:
                            all_proxies[proxy_type].add(line.strip())
            except Exception as e:
                print(f"Error al obtener {proxy_type} desde {url}: {e}")

    return all_proxies

def save_by_type(proxies):
    for proxy_type, proxy_list in proxies.items():
        with open(f"by_type/{proxy_type}.txt", "w") as f:
            f.write("\n".join(sorted(proxy_list)))

def save_by_country(proxies):
    for country_code in COUNTRIES:
        matched = []
        for proxy_type, proxy_list in proxies.items():
            for proxy in proxy_list:
                ip = proxy.split(":")[0]
                try:
                    r = requests.get(f"http://ip-api.com/line/{ip}?fields=countryCode", timeout=5)
                    if r.text.strip() == country_code:
                        matched.append(proxy)
                except:
                    continue
        with open(f"by_country/{country_code}.txt", "w") as f:
            f.write("\n".join(matched))

def main():
    print("Descargando proxies...")
    proxies = fetch_and_filter()
    print("Guardando por tipo...")
    save_by_type(proxies)
    print("Filtrando por país...")
    save_by_country(proxies)
    print("¡Listo!")

if __name__ == "__main__":
    main()
