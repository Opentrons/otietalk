import asyncio

from clients.robot_client import RobotClient
from clients.robot_interactions import RobotInteractions
from rich.console import Console
from rich.theme import Theme
from util.util import log_response
from wizard.wizard import Wizard


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
        if cr:
            await robot_interactions.un_current_run(cr)
        # console.print(cr)
        # all_analyses_complete = await robot_interactions.all_analyses_are_complete()
        # console.print(f"analyses complete? {all_analyses_complete}")
        # protocol = await robot_client.get_protocol("1e858432-d8e0-4daf-94e5-6af848fd0349")
        # await log_response(protocol, console=console)
        # run = await robot_client.get_run("ed5991d5-6a3d-477b-9a2f-ad6e61b1fb17")
        # await log_response(run, console=console)
        # analyses = await robot_client.get_analyses("1e858432-d8e0-4daf-94e5-6af848fd0349")
        # await log_response(analyses, console=console)
        # analysis = await robot_client.get_analysis("1e858432-d8e0-4daf-94e5-6af848fd0349", "31abe15c-fefb-4a13-9ed8-3674783d356c")
        # await log_response(analysis, console=console)
        # ur = await robot_interactions.un_current_run(cr)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
