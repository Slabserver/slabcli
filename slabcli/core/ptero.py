import time
from slabcli import config
from slabcli.common.utils import http_request
import json

START_SIGNAL = "start"
STOP_SIGNAL = "stop"
KILL_SIGNAL = "kill"
RESTART_SIGNAL = "restart"

ONLINE_STATE = "running"
OFFLINE_STATE = "offline"

QUERY_INTERVAL = 5   # seconds between checks
QUERY_TIMEOUT = 150  # total seconds

def get_api_cfg():
    cfg = config.load_config()
    api_url = cfg["pterodactyl"].get("api_url", "") # Base API URL (e.g., "https://panel.slabserver.org/")
    api_token = cfg["pterodactyl"].get("api_token", "")
    return api_token, api_url

def build_header(token: str) -> dict:
    """
    Builds standard header for Pterodactyl JSON API requests with Bearer authentication.

    :param token: The authentication token
    :return: A dictionary of headers
    """
    return {
    'Authorization': f'Bearer {token}',
    'Accept': 'Application/vnd.pterodactyl.v1+json',
    'Content-Type': 'application/json'
    }

def get_server_status(server_id: str):

    api_token, api_url = get_api_cfg()

    # Only use up to first hyphen in UUID
    short_server_id = server_id.split("-", 1)[0]

    header = build_header(api_token)
    url = f"{api_url}{short_server_id}/resources"
    response = http_request("GET", url, header)

    if response.status_code == 200:
        data = response.json()
        return data['attributes']['current_state']
    else:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")


def send_power_signal(server_id, signal):
    """
    Sends a power signal operation to a Pterodactyl server via API.
    
    :param server: Shorthand server unique identifier
    :param signal: Power management signal to send
    :return: None
    :raises: RuntimeError if the request fails or status is unexpected
    """

    api_token, api_url = get_api_cfg()

    # Only use up to first hyphen in UUID
    short_server_id = server_id.split("-", 1)[0]

    url = f"{api_url}{short_server_id}/power"
    header = build_header(api_token)
    body = json.dumps({'signal': signal})

    response = http_request("POST", url, header, body)

    if response.status_code == 204:  # 204 == HTTP No Content
        print(f'Server {signal} initiated')
    else:
        raise RuntimeError(f"Unexpected status code: {response.status_code}")

def are_servers_at_state(servers, desired_state):
    elapsed = 0
    while elapsed < QUERY_TIMEOUT:
        for s in servers:
            status = get_server_status(servers[s])
            print("status is:"+status)
            if status != desired_state:
                time.sleep(QUERY_INTERVAL)
                elapsed += QUERY_INTERVAL
        print(f"✅ All servers successfully {desired_state}.")
        return True
    print(f"❌ Servers were not successfully {desired_state} within 150 seconds")
    return False

def stop_servers(servers) -> bool:
    for s in servers:
        send_power_signal(servers[s], STOP_SIGNAL)
    are_servers_at_state(servers, OFFLINE_STATE)

def start_servers(servers):
    for s in servers:
        send_power_signal(servers[s], START_SIGNAL)
    are_servers_at_state(servers, ONLINE_STATE)

def restart_servers(servers):
    for s in servers:
        send_power_signal(servers[s], RESTART_SIGNAL)
    are_servers_at_state(servers, ONLINE_STATE)