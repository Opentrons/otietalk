import asyncio
import json
import textwrap

from httpx import Response
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme

from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Retrieve format and output the labwareOffsets from runs."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
        resp = await robot_client.get_runs()
        await log_response(response=resp)
        runs = resp.json()["data"]

        # The list comprehension for the below overwhelmed me.
        # It is more readable in two parts.
        # get all the lists of labware offsets
        # must have empty [] check
        labware_offsets_groups = [run["labwareOffsets"] for run in runs if run["labwareOffsets"] != []]
        offsets = []
        # make a list of just the offset objects
        for group in labware_offsets_groups:
            for offset in group:
                # empty check but I don't think these are ever []
                if offset != []:
                    offsets.append(offset)
        console.print(offsets)
        with open("offsets.json", "w") as outfile:
            json.dump(offsets, outfile)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    markdown_text = textwrap.dedent(
        f"""\
        # Get get all the offsets that were used in runs on the robot.

        > Notes:
        - No filtering is done on the runs.
        - Look in responses.log for the full /runs response
        """
    )
    console.print(
        Panel(
            Markdown(markdown_text),
            style="bold magenta",
        )
    )
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
