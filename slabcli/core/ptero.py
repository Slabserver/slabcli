from slabcli import config
from slabcli.common.utils import http_request
import json

START_SIGNAL = "'start'"
STOP_SIGNAL = "'stop'"
KILL_SIGNAL = "'kill'"
RESTART_SIGNAL = "'restart'"


def build_header(token: str) -> dict:
    """
    Builds standard header for Pterodactyl JSON API requests with Bearer authentication.

    :param token: The authentication token
    :return: A dictionary of headers
    """
    return {
    'Authorization': f'Bearer ptlc_{token}',
    'Accept': 'Application/vnd.pterodactyl.v1+json',
    'Content-Type': 'application/json'
    }

def send_power_signal(server_id, signal):
    """
    Sends a power signal operation to a Pterodactyl server via API.
    
    :param server: Shorthand server unique identifier
    :param signal: Power management signal to send
    :return: None
    :raises: RuntimeError if the request fails or status is unexpected
    """
    cfg = config.load_config()
    api_url = cfg["pterodactyl"].get("api_url", "") # Base API URL (e.g., "https://panel.slabserver.org/")
    api_token = cfg["pterodactyl"].get("api_token", "")

    url = f"{api_url}{server_id}/power"
    header = build_header(api_token)
    body = json.dumps({'signal': signal})

    response = http_request("POST", url, header=header, body=body)

    if response.status_code == 204:  # 204 == HTTP No Content
        print(f'Server {signal} initiated')
    else:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")
    
def stop_servers(servers):
    for s in servers:
        send_power_signal(servers[s], STOP_SIGNAL)

def start_servers(servers):
    for s in servers:
        send_power_signal(servers[s], START_SIGNAL)

def restart_servers(servers):
    for s in servers:
        send_power_signal(servers[s], RESTART_SIGNAL)