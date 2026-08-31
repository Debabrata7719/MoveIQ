import requests
from src.logger import get_logger

logger = get_logger("geo_utils")

def get_country_from_ip(ip: str) -> str:
    """
    Resolves the country code of the client IP address.
    Falls back to 'IN' (India) for local, private, or failed requests.
    """
    # 1. Handle local loopback and private subnets
    if not ip or ip in ("127.0.0.1", "::1", "localhost") or ip.startswith(("10.", "192.168.", "172.16.", "172.31.")):
        return "IN"
        
    # 2. Query IP-API geolocation service
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("countryCode"):
                return str(data.get("countryCode")).upper()
        logger.warning(f"Failed to geolocate IP {ip}. Response: {response.text}")
    except Exception as e:
        logger.error(f"Error querying geolocation service for IP {ip}: {e}")
        
    # Fallback default
    return "IN"
