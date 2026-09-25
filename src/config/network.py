import socket
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def get_network_endpoints(port: int = 8000) -> Dict[str, Any]:
    """
    Discovers all local network, Wi-Fi, and Tailscale tailnet IPv4 addresses
    for seamless remote access across all connected devices.
    """
    endpoints: Dict[str, Any] = {
        "local": f"http://localhost:{port}",
        "network": [],
        "tailscale": [],
        "hostname": None,
    }

    try:
        hostname = socket.gethostname()
        endpoints["hostname"] = f"http://{hostname.lower()}:{port}"
        
        # Resolve all IPv4 addresses
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            elif ip.startswith("100."):
                # Standard Tailscale CGNAT address range 100.64.0.0/10
                endpoints["tailscale"].append(f"http://{ip}:{port}")
            else:
                endpoints["network"].append(f"http://{ip}:{port}")
    except Exception as e:
        logger.debug(f"Notice during network address discovery: {e}")

    return endpoints
