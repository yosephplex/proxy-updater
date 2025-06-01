import requests
import socket
from concurrent.futures import ThreadPoolExecutor
import os
import argparse
import logging
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

# Fuentes de proxies (configurables desde CLI)
SOURCES = {
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

def fetch_proxies(urls: List[str], timeout: int = 10) -> List[str]:
    """Descarga proxies desde URLs y retorna una lista limpia."""
    proxies = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            proxies.update(filter(None, response.text.strip().splitlines()))
            logger.info(f"✅ Descargados {len(proxies)} proxies desde {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al descargar {url}: {str(e)}")
    return list(proxies)

def check_proxy(proxy: str, proxy_type: str, timeout: int = 3) -> Optional[str]:
    """Verifica si un proxy es funcional mediante conexión TCP."""
    try:
        ip, port = proxy.split(":")
        with socket.create_connection((ip, int(port)), timeout=timeout):
            logger.debug(f"🟢 Proxy válido: {proxy} ({proxy_type})")
            return proxy
    except (socket.timeout, socket.error, ValueError) as e:
        logger.debug(f"🔴 Proxy inválido: {proxy} ({proxy_type}): {str(e)}")
        return None

def save_proxies(output_dir: str, proxy_type: str, proxies: List[str]):
    """Guarda proxies en un archivo dentro del directorio especificado."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{proxy_type}.txt")
    with open(output_path, "w") as f:
        f.write("\n".join(proxies))
    logger.info(f"💾 Guardados {len(proxies)} proxies en {output_path}")

def main(proxy_types: List[str], output_dir: str, max_workers: int, timeout_check: int):
    """Función principal que coordina la descarga, verificación y guardado."""
    for proxy_type in proxy_types:
        if proxy_type not in SOURCES:
            logger.warning(f"⚠️ Tipo de proxy no soportado: {proxy_type}")
            continue

        logger.info(f"🔎 Buscando proxies {proxy_type.upper()}...")
        raw_proxies = fetch_proxies(SOURCES[proxy_type])

        logger.info(f"🧪 Verificando {len(raw_proxies)} proxies...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            valid_proxies = list(filter(None, executor.map(
                lambda p: check_proxy(p, proxy_type, timeout_check),
                raw_proxies
            )))

        if valid_proxies:
            save_proxies(output_dir, proxy_type, valid_proxies)
        else:
            logger.warning(f"⚠️ No se encontraron proxies válidos para {proxy_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔄 Actualizador de proxies HTTP/SOCKS4/SOCKS5",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["http", "socks4", "socks5"],
        choices=["http", "socks4", "socks5"],
        help="Tipos de proxies a descargar"
    )
    parser.add_argument(
        "--output",
        default="proxies",
        help="Directorio de salida para los archivos"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=100,
        help="Número de hilos para verificación concurrente"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Timeout en segundos para verificación de proxies"
    )
    args = parser.parse_args()

    main(args.types, args.output, args.workers, args.timeout)
