""""""

import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from util.util import LOG_FILE_PATH, is_valid_IPAddress, is_valid_port


class Wizard:
    """Reusable CLI interactions"""

    def __init__(self, console: Optional[Console]) -> None:
        if console:
            self.console = console
        else:
            self.console = Console()

    def validate_ip(self, ip: Optional[str] = None) -> str:
        """Recursive method to prompt the user to input or confirm robot ip address."""
        env_robot_ip = os.getenv("ROBOT_IP")
        if env_robot_ip:
            ip = Prompt.ask(
                f"The [i]ROBOT_IP[/i] [bold red] environment variable is set and valid.[/] {env_robot_ip} Hit enter to use it.",
                console=self.console,
                default=env_robot_ip,
                show_default=False,
            )
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
        return self.validate_ip(ip)

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
                f"[bold red]{port}[/] is not valid, enter a different value. (most likely it is 31950 and you can just" " hit enter) ",
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
            return str(port)
        return self.validate_port(port)

    def reset(self) -> None:
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
            self.console.print(
                Panel(
                    f"Removed log file {LOG_FILE_PATH}",
                    style="bold magenta",
                )
            )

    def reset_log(self, override: bool = False) -> bool:
        """Reset the log file."""
        if override:
            self.reset()
            return True
        response = Confirm.ask(f"Would you like to reset the log file {LOG_FILE_PATH}?")
        if response:
            self.reset()
            return True
        return False

    def choices(self, question: str, choices: list[str], default: str) -> str:
        """Pick a choice."""
        return Prompt.ask(prompt=question, choices=choices, default=default)
