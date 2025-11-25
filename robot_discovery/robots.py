# /// script
# requires-python = ">=3.13.*"
# dependencies = [
#     "zeroconf",
#     "rich",
#     "httpx"
# ]
# ///

import asyncio
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any, List

import httpx
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

# ---------------- Data Classes ----------------


@dataclass
class InterfaceInfo:
    name: str
    gateway: str
    mac: str
    iface_type: str


@dataclass
class Device:
    instance: str
    ip: str
    last_seen: str
    interfaces: List[InterfaceInfo] = field(default_factory=list)
    status_raw: dict[str, Any] = field(default_factory=dict)


# Global dictionary of discovered devices.
discovered: dict[str, Device] = {}

# ---------------- Zeroconf Listener ----------------


class MyListener(ServiceListener):
    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            instance = name.split(".")[0]
            ip = (
                socket.inet_ntoa(info.addresses[0])
                if info.addresses
                else "[unresolved]"
            )
            discovered[instance] = Device(
                instance=instance, ip=ip, last_seen=time.strftime("%H:%M:%S")
            )

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self.add_service(zeroconf, service_type, name)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        instance = name.split(".")[0]
        discovered.pop(instance, None)


# ---------------- Async Polling ----------------


async def fetch_and_update_status(device: Device, client: httpx.AsyncClient) -> None:
    url = f"http://{device.ip}:31950/networking/status"
    try:
        response = await client.get(
            url, headers={"opentrons-version": "*"}, timeout=3.0
        )
        data = response.json()
        device.status_raw = data
        interfaces = []
        for iface_name, details in data.get("interfaces", {}).items():
            interfaces.append(
                InterfaceInfo(
                    name=iface_name,
                    gateway=details.get("gatewayAddress", "N/A"),
                    mac=details.get("macAddress", "N/A"),
                    iface_type=details.get("type", "N/A"),
                )
            )
        device.interfaces = interfaces
        device.last_seen = time.strftime("%H:%M:%S")
    except Exception as e:
        device.status_raw = {"error": str(e)}
        device.interfaces = []
        device.last_seen = time.strftime("%H:%M:%S")


async def poll_status_async() -> None:
    """
    For the first 15 seconds, poll with a very short sleep interval (0.5 sec).
    Then change the polling interval to every 5 minutes.
    """
    poll_start = time.monotonic()
    async with httpx.AsyncClient() as client:
        while True:
            tasks = []
            for device in list(discovered.values()):
                if device.ip and "unresolved" not in device.ip:
                    tasks.append(fetch_and_update_status(device, client))
            if tasks:
                await asyncio.gather(*tasks)
            elapsed = time.monotonic() - poll_start
            if elapsed < 15:
                sleep_duration = 0.5
            else:
                sleep_duration = 300  # 5 minutes
            await asyncio.sleep(sleep_duration)


def start_async_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(poll_status_async())


# ---------------- Live View Generation ----------------


def generate_spinner_line() -> str:
    spinner_frames = ["|", "/", "-", "\\"]  # spinner frames
    frame = spinner_frames[int(time.time() * 2) % len(spinner_frames)]
    if discovered:
        names = ", ".join(sorted(discovered.keys()))
        return f"{frame} Discovered: {names}"
    else:
        return f"{frame} No devices discovered yet."


def generate_table() -> Table:
    table = Table(title="Device Details", expand=True)
    table.add_column("Instance", style="cyan", no_wrap=True)
    table.add_column("IP", style="green")
    table.add_column("Last Seen", style="dim")
    table.add_column("Interfaces", style="magenta")

    for device in sorted(discovered.values(), key=lambda d: d.instance):
        if device.interfaces:
            iface_lines = "\n".join(
                f"{iface.name}: gateway={iface.gateway}, mac={iface.mac}, type={iface.iface_type}"
                for iface in device.interfaces
            )
        else:
            iface_lines = "[pending]"
        table.add_row(device.instance, device.ip, device.last_seen, iface_lines)
    return table


def generate_live_group() -> Group:
    spinner_line = generate_spinner_line()
    table = generate_table()
    return Group(Align.center(spinner_line), table)


# ---------------- Main ----------------


def main() -> None:
    console = Console()
    # Start Zeroconf discovery.
    zeroconf = Zeroconf()
    listener = MyListener()
    ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    # Start the async polling loop in a separate thread.
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_async_loop, args=(loop,), daemon=True).start()

    try:
        with Live(
            generate_live_group(), console=console, refresh_per_second=4, screen=True
        ) as live:
            while True:
                live.update(generate_live_group())
                time.sleep(0.25)
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/bold red]")
    finally:
        zeroconf.close()
        loop.stop()


if __name__ == "__main__":
    main()
