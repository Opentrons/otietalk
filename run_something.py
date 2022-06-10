import asyncio

from rich.console import Console
from rich.theme import Theme

from robot_client import RobotClient
from robot_interactions import RobotInteractions
from wizard import Wizard


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Run the series of commands necessary to evaluate tip height against labware on the Heater Shaker."""  # noqa: E501
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
        resp = await robot_client.get_modules()
        console.print(resp.json())


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))