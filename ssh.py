import time
from pathlib import Path

import paramiko
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.theme import Theme
from scp import SCPClient
from wizard import Wizard


class Action:
    GET = "data.get"
    PUT = "data.put"
    PUT_DB = "data.put.db"
    DELETE = "data.delete"
    CHOICES = [GET, PUT, PUT_DB, DELETE]


custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
console = Console(theme=custom_theme)


def ssh(_robot_ip: str, action: str):
    """Do the work."""

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # https://medium.com/@michal_73101/paramiko-and-openssh-generated-keys-26524dccb259
    # ssh-keygen -m PEM -t rsa -b 2048 -f id_paramiko
    # https://support.opentrons.com/en/articles/3203681-setting-up-ssh-access-to-your-ot-2
    # connect robot via usb and get ip
    # from ~/.ssh
    # curl \
    # -H 'Content-Type: application/json' \
    # -d "{\"key\":\"$(cat id_paramiko.pub)\"}" \
    # $ROBOT_IP:31950/server/ssh_keys

    # local
    key_file: Path = Path("results/key")
    pkey = paramiko.RSAKey.from_private_key_file(str(key_file.resolve()))
    assert key_file.is_file()
    disabled_algorithms = {"pubkeys": ["rsa-sha2-512", "rsa-sha2-256"]}
    # must have disabled_algorithms so it uses the 2048?
    ssh_client.connect(hostname=_robot_ip, username="root", pkey=pkey, disabled_algorithms=disabled_algorithms)
    text_column = TextColumn("{task.description}")
    bar_column = BarColumn()
    with Progress(text_column, bar_column, console=console) as progresso:

        def progress(filename, size, sent, address):
            """Print progress."""
            if isinstance(filename, bytes):
                filename = filename.decode()
            percent_done = float(sent) / float(size) * 100
            progresso.update(task1, total=size, advance=sent, refresh=True)
            if percent_done >= 100:
                progresso.console.print(f"[bold purple]({address[0]}) {filename} downloaded")

        match action:  # noqa: E999 https://github.com/charliermarsh/ruff/issues/282
            case Action.GET:
                console.print(
                    Panel(
                        "[bold green] Compressing and downloading the /data directory.[/]",
                        style="bold magenta",
                    )
                )
                task2 = progresso.add_task("[sky_blue3]Compressing...")
                stdin, stdout, stderr = ssh_client.exec_command("cd /data && tar -zcvf data.tar.gz .")
                exit_status = stdout.channel.recv_exit_status()  # Blocking call
                if exit_status == 0:
                    progresso.update(task2, completed=100, refresh=True)
                    progresso.console.print("[sky_blue3]data directory compressed")
                else:
                    progresso.console.print("Error", exit_status)
                stdin.close()
                task1 = progresso.add_task("[red]Downloading...")
                with SCPClient(ssh_client.get_transport(), progress4=progress) as scp:
                    scp.get("/data/data.tar.gz", local_path=f"{str(time.time_ns())}data.tar.gz")
            case Action.PUT_DB:
                task1 = progresso.add_task("[red]Uploading...", start=False)
                # stop the robot-server
                stdin, stdout, stderr = ssh_client.exec_command("systemctl stop opentrons-robot-server")
                exit_status = stdout.channel.recv_exit_status()  # Blocking call
                # delete the database dir
                stdin, stdout, stderr = ssh_client.exec_command("rm -rf /data/opentrons_robot_server")
                exit_status = stdout.channel.recv_exit_status()  # Blocking call
                # push the new dir
                with SCPClient(ssh_client.get_transport(), progress4=progress) as scp:
                    scp.put("results/opentrons_robot_server", "/data/opentrons_robot_server", recursive=True)
                # stdin, stdout, stderr = ssh_client.exec_command("cd /data && tar -xf data.tar.gz")
                # exit_status = stdout.channel.recv_exit_status()  # Blocking call
                # if exit_status == 0:
                #     console.print("File Put")
                # else:
                #     console.print("Error", exit_status)
                # stdin, stdout, stderr = ssh_client.exec_command("rm /data/data.tar.gz")
                # exit_status = stdout.channel.recv_exit_status()  # Blocking call
                # if exit_status == 0:
                #     console.print("File Put")
                # else:
                #     console.print("Error", exit_status)
                # stdin, stdout, stderr = ssh_client.exec_command("systemctl restart opentrons-robot-server")
                # exit_status = stdout.channel.recv_exit_status()  # Blocking call
                # if exit_status == 0:
                #     console.print("File Put")
                # else:
                #     console.print("Error", exit_status)
                # # requests.post(f"http://{robot_ip}}:31950/server/restart")
                # # restart robot server `systemctl restart opentrons-robot-server`
            case Action.DELETE:
                console.print(
                    Panel(
                        "[bold green] deleting data/opentrons_robot_server[/]",
                        style="bold magenta",
                    )
                )
                stdin, stdout, stderr = ssh_client.exec_command("rm -rf /data/opentrons_robot_server")
    ssh_client.close()


if __name__ == "__main__":
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    action = wizard.choices(question="What action to take?", choices=Action.CHOICES, default=Action.GET)
    ssh(_robot_ip=robot_ip, action=action)
