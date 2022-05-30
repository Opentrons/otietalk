import ipaddress
import json
import sys

from anyio import to_thread
from httpx import Response


async def prompt(message: str) -> str:
    def _prompt() -> str:
        print(message)
        return sys.stdin.readline()

    return await to_thread.run_sync(_prompt)


async def log_response(response: Response, print_timing: bool = False) -> None:
    """Log the response status, url, timing, and json response."""
    endpoint = f"\nstatus_code = {response.status_code}\n{response.request.method} {response.url}"  # noqa: E501
    formatted_response_body = json.dumps(response.json(), indent=4)
    elapsed = response.elapsed.total_seconds()
    elapsed_output = str(elapsed)
    if elapsed > 1:
        elapsed_output = f"{str(elapsed)} *LONG*"
    if print_timing:
        print(endpoint)
        print("\n")
        print(elapsed_output)
    # print(formatted_response_body) # too big to do in console usefully
    with open("responses.log", "a") as log:
        log.write(endpoint)
        log.write("\n")
        log.write(elapsed_output)
        log.write(formatted_response_body)


def is_valid_IPAddress(sample_str):
    """Returns True if given string is a
    valid IP Address, else returns False"""
    result = True
    try:
        ipaddress.ip_network(sample_str)
    except:
        result = False
    return result

def is_valid_port(port: str|int) -> str:
    """Returns True if given string is a
    valid IP Address, else returns False"""
    if isinstance(port, str):
        port = int(port.strip(" "))
    if 1 <= port <= 65535:
        return True
    return False