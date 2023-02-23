# put a specific build on a robot
# put a specific DB on a robot, or ensure empty
# attach Thermocycler gen2, HS, temperature module gen2
# attach P300 8 channel left
# attach P20 single right

import asyncio
from dataclasses import dataclass

import pandas
from httpx import Response
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard

OT2 = "OT2"
FLEX = "Flex"
ROBOTS = [OT2, FLEX]

# https://github.com/Opentrons/opentrons/blob/edge/robot-server/tests/integration/persistence_snapshots
EMPTY = "Empty"


@dataclass
class Timing:
    endpoint: str
    verb: str
    elapsed: float
    robot: str
    build: str
    db: str


async def stuff(robot_ip: str, robot_port: str, robot: str, baseline: str, build: str, db: str) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        baseline = baseline
        RobotInteractions(robot_client=robot_client)
        responses: list[Response] = []

        async def test() -> list[Response]:
            """The sequential calls to make."""
            holder: list[Response] = []
            holder.append(await robot_client.get_health())
            holder.append(await robot_client.get_openapi())
            holder.append(await robot_client.get_runs())
            holder.append(await robot_client.get_protocols())
            holder.append(await robot_client.get_modules())
            holder.append(await robot_client.get_pipettes(refresh=False))
            holder.append(await robot_client.get_pipettes(refresh=True))
            holder.append(await robot_client.get_calibration_status())
            holder.append(await robot_client.get_pipette_offset())
            holder.append(await robot_client.get_tip_length())
            # lights
            # time
            # sessions
            # wifi/list
            # networking/status
            return holder

        async def test_analyses():
            """sequentially upload and await analysis complete on the battery"""
            pass

        enn = 5
        for _ in range(enn):
            responses.extend(await test())
        timings: list[Timing] = []
        for resp in responses:
            timings.append(
                Timing(
                    endpoint=str(resp.url).split(robot_client.base_url, 1)[1],
                    verb=resp.request.method,
                    elapsed=resp.elapsed.total_seconds(),
                    robot=robot,
                    build=build,
                    db=db,
                )
            )
       # await log_response(resp)
        df = pandas.DataFrame(timings)
        # console.print(df)
        console.print(Panel("Endpoints", style="bold dodger_blue1"))
        endpoints = set(df["endpoint"].values)
        console.print(endpoints)
        for route in endpoints:
            console.print(Panel(route, style="bold yellow"))
            filtered_df = df[df["endpoint"] == route]
            # console.print(filtered_df)
            console.print(
                filtered_df.describe(),
                style="bold magenta",
            )
        df.to_csv("try.csv", mode="a", index=False, header=False)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port(31950)
    wizard.reset_log(override=True)
    robot = wizard.choices("What robot to test?", choices=ROBOTS, default=OT2)
    baseline = wizard.confirm(question="Is this a baseline?")
    build = "6.2.1"
    db = EMPTY
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port, robot=robot, baseline=baseline, build=build, db=db))
