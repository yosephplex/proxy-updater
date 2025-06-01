import requests
import socket
from concurrent.futures import ThreadPoolExecutor
import os

sources = {
    "http": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
    ],
    "socks4": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
    ],
    "socks5": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
    ]
}

def fetch_proxies(urls):
    proxies = set()
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                proxies.update(r.text.strip().splitlines())
        except:
            continue
    return list(proxies)

def check_proxy(proxy, proxy_type):
    try:
        ip, port = proxy.split(":")
        with socket.create_connection((ip, int(port)), timeout=3):
            return proxy
    except:
        return None

def save_proxies(name, proxies):
    os.makedirs("proxies", exist_ok=True)
    with open(f"proxies/{name}.txt", "w") as f:
        f.write("\n".join(proxies))

def main():
    for proxy_type, urls in sources.items():
        raw = fetch_proxies(urls)
        with ThreadPoolExecutor(max_workers=100) as executor:
            valid = list(filter(None, executor.map(lambda p: check_proxy(p, proxy_type), raw)))
        save_proxies(proxy_type, valid)

if __name__ == "__main__":
    main()
