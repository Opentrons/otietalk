import os
from typing import Dict, List, Optional

import anyio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.theme import Theme

from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import is_valid_IPAddress, is_valid_port, LOG_FILE_PATH


class Wizard:
    """reusable interactions of"""

    def __init__(self, console: Optional[Console]) -> None:
        if console:
            self.console = console
        else:
            self.console = Console()

    def validate_ip(self, ip: Optional[str] = None) -> str:
        if ip == "" or ip is None:
            ip = Prompt.ask(
                "What is [i]your[/i] [bold red]robot ip address[/] (like 192.168.50.89) ? ",
                console=self.console,
                default="192.168.50.89",
                show_default=False,
            )
        elif not is_valid_IPAddress(ip):
            ip = Prompt.ask(
                f"ip address [bold red]{ip}[/] is not valid, try again (like 192.168.50.89)",
                console=self.console,
                default="192.168.50.89",
                show_default=False,
            )
        if is_valid_IPAddress(ip):
            self.console.print(
                Panel(
                    f"Great, that checks out as a valid ip, robot ip set to [bold green]{ip}[/]",
                    style="bold magenta",
                )
            )
            return ip
        else:
            self.validate_ip(ip)

    def validate_port(self, port: Optional[int | str] = None) -> str:
        if port == "" or port is None:
            port = Prompt.ask(
                "What is [i]your[/i] [bold red]robot port[/] (most likely it is 31950 and you can just hit enter) ?",
                console=self.console,
                default="31950",
                show_default=False,
            )
        elif not is_valid_port(port):
            port = Prompt.ask(
                f"[bold red]{port}[/] is not valid, enter a different value. (most likely it is 31950 and you can just hit enter) ",
                console=self.console,
                default="31950",
                show_default=False,
            )
        if is_valid_port(port):
            self.console.print(
                Panel(
                    f"That checks out as a valid port, robot port set to [bold green]{port}[/]",
                    style="bold magenta",
                )
            )
            return port
        else:
            self.validate_port(port)

    def reset_log(self) -> bool:
        response = Confirm.ask(f"Would you like to reset the log file {LOG_FILE_PATH}?")
        if response:
            os.remove(LOG_FILE_PATH)
            self.console.print(
                Panel(
                    f"Removed log file {LOG_FILE_PATH}",
                    style="bold magenta",
                )
            )
            return True
        return False
