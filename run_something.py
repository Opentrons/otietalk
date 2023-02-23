import asyncio

from rich.console import Console
from rich.theme import Theme
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions = RobotInteractions(robot_client=robot_client)
        result = await robot_client.get_health()
        await log_response(result, print_timing=True, console=console)
        pipettes = await robot_client.get_pipettes()
        await log_response(pipettes)
        pipettes_offset = await robot_client.get_pipette_offset()
        await log_response(pipettes_offset)
        instruments = await robot_client.get_instruments(False)
        await log_response(instruments)
        cr = await robot_interactions.get_current_run()
        console.print(cr)
        all_analyses_complete = await robot_interactions.all_analyses_are_complete()
        console.print(f"analyses complete? {all_analyses_complete}")
        # ur = await robot_interactions.un_current_run(cr)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
