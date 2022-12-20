import requests


def request_url(
    url: str,
    username: str,
    password: str,
    timeout: int = 10,
) -> str:
    """Sends a request and returns the content of the response, in unicode."""
    response = requests.get(url, auth=(username, password), timeout=timeout)
    response.raise_for_status()
    return response.text
