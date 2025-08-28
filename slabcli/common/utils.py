import os
import requests


def http_request(http_method: str, url: str, headers: dict = None, body: str = None, timeout: int = 10):
    """
    Performs a simple HTTP request
    
    :param http_method: HTTP method (GET, POST, PUT, DELETE, etc.)
    :param url: The URL for the request
    :param headers: Dictionary of HTTP headers
    :param body: Request body (string or bytes)
    :param timeout: Timeout in seconds (default: 10)
    :return: requests.Response object
    :raises: requests.RequestException if the request fails
    """
    try:
        response = requests.request(
            method=http_method,
            url=url,
            headers=headers,
            data=body,
            timeout=timeout
        )
        response.raise_for_status()  # Raise an error for HTTP 4xx/5xx
        return response
    except requests.RequestException as e:
        raise RuntimeError(f"Request failed: {e}") from e

def file_has_extension(filename, extensions):
    """Return True if filename ends with one of the given extensions."""
    return filename.lower().endswith(tuple(ext.lower() for ext in extensions))

def file_newer_than(file, timestamp):
    """Return True if file was modified more recently than the provided timestamp."""

    try:
        mtime = os.path.getmtime(file)
    except OSError:
        return False
    if mtime > timestamp:
        return True
    return False

def print_directory_contents(base_dir):
    parent_dir = os.path.dirname(base_dir)
    for item in os.listdir(base_dir):
        full_path = os.path.join(base_dir, item)
        rel_path = os.path.relpath(full_path, parent_dir)
        suffix = "/..." if os.path.isdir(full_path) else ""
        print(f"  {rel_path}{suffix}")

def substring_in_string(substrings, string):
    """Loop through a list of substrings to determine if any substring is found within a string"""

    substrings_to_check = substrings or []  # empty list to avoid errors
    for substring in substrings_to_check:
        if substring in string:
            return True
    return False

