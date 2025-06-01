import requests
import socket
from concurrent.futures import ThreadPoolExecutor
import os
import argparse
import logging
import time
from typing import List, Dict, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("proxy_updater.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fuentes de proxies ampliadas (HTTP/SOCKS4/SOCKS5)
SOURCES = {
    "http": [
        # Free APIs
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
        "https://www.proxy-list.download/api/v1/get?type=http",
        # GitHub Sources
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        # Premium-like (free tiers)
        "https://proxylist.geonode.com/api/proxy-list?protocols=http&limit=500"
    ],
    "socks4": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all",
        "https://www.proxy-list.download/api/v1/get?type=socks4",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://proxylist.geonode.com/api/proxy-list?protocols=socks4&limit=500"
    ],
    "socks5": [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://proxylist.geonode.com/api/proxy-list?protocols=socks5&limit=500"
    ]
}

def fetch_proxies(urls: List[str], timeout: int = 10) -> List[str]:
    """Descarga proxies con rotación de User-Agent y filtrado de puertos."""
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            new_proxies = response.text.strip().splitlines()
            
            # Filtra proxies con formato IP:PUERTO válido
            valid_proxies = [
                p.strip() for p in new_proxies 
                if len(p.split(":")) == 2 and p.split(":")[1].isdigit()
            ]
            
            proxies.update(valid_proxies)
            logger.info(f"✅ Descargados {len(valid_proxies)} proxies desde {url}")
        except Exception as e:
            logger.error(f"❌ Error en {url}: {str(e)}")
        time.sleep(1)  # Evita rate limits
        
    return list(proxies)

def check_proxy(proxy: str, proxy_type: str, timeout: int = 3) -> Optional[str]:
    """Verifica conectividad TCP y (opcionalmente) protocolo específico."""
    try:
        ip, port = proxy.split(":")
        with socket.create_connection((ip, int(port)), timeout=timeout):
            # Verificación adicional para SOCKS (opcional)
            if proxy_type != "http":
                try:
                    socks_proxy = {
                        "http": f"socks5://{proxy}",
                        "https": f"socks5://{proxy}"
                    }
                    test_url = "https://www.google.com"
                    response = requests.get(test_url, proxies=socks_proxy, timeout=timeout)
                    if response.status_code != 200:
                        raise ConnectionError("SOCKS test failed")
                except:
                    return None
            
            logger.debug(f"🟢 Proxy válido: {proxy} ({proxy_type})")
            return proxy
    except (socket.timeout, socket.error, ValueError) as e:
        logger.debug(f"🔴 Proxy inválido: {proxy} ({e})")
        return None

def save_proxies(output_dir: str, proxy_type: str, proxies: List[str]):
    """Guarda proxies eliminando duplicados y ordenándolos."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{proxy_type}.txt")
    
    # Elimina duplicados y ordena
    unique_proxies = sorted(list(set(proxies)))
    
    with open(output_path, "w") as f:
        f.write("\n".join(unique_proxies))
    logger.info(f"💾 Guardados {len(unique_proxies)} proxies en {output_path}")

def main(proxy_types: List[str], output_dir: str, max_workers: int, timeout_check: int):
    """Flujo principal con manejo de errores por tipo de proxy."""
    for proxy_type in proxy_types:
        if proxy_type not in SOURCES:
            logger.warning(f"⚠️ Tipo no soportado: {proxy_type}")
            continue

        try:
            logger.info(f"🔎 Buscando {proxy_type.upper()}...")
            raw_proxies = fetch_proxies(SOURCES[proxy_type])
            
            if not raw_proxies:
                logger.warning(f"⛔ No se obtuvieron proxies de {proxy_type}")
                continue

            logger.info(f"🧪 Verificando {len(raw_proxies)} proxies...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                valid_proxies = list(filter(None, executor.map(
                    lambda p: check_proxy(p, proxy_type, timeout_check),
                    raw_proxies
                )))

            if valid_proxies:
                save_proxies(output_dir, proxy_type, valid_proxies)
            else:
                logger.warning(f"⚠️ 0 proxies válidos para {proxy_type}")

        except Exception as e:
            logger.error(f"🔥 Error crítico en {proxy_type}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔄 ProxyUpdater v2 - Descarga/Verifica HTTP/SOCKS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["http", "socks4", "socks5"],
        choices=["http", "socks4", "socks5"],
        help="Protocolos de proxies a descargar"
    )
    parser.add_argument(
        "--output",
        default="proxies",
        help="Directorio de salida (se creará si no existe)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=100,
        help="Hilos concurrentes para verificación"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Timeout (segundos) para verificación"
    )
    args = parser.parse_args()

    main(args.types, args.output, args.workers, args.timeout)
