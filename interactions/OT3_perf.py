# upload protocol
# wait for analysis good
# start run
# wait for run to finish
# repeat

import asyncio
from dataclasses import dataclass
from pathlib import Path

import pandas
from clients.robot_client import RobotClient
from clients.robot_interactions import RobotInteractions
from httpx import Response
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from util.util import log_response
from wizard.wizard import Wizard


@dataclass
class Timing:
    endpoint: str
    verb: str
    elapsed: float


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        baseline = False
        robot_interactions = RobotInteractions(robot_client=robot_client)
        responses: list[Response] = []

        async def stressor() -> tuple[Response, Response]:
            tasks = await asyncio.gather(robot_client.get_health(), robot_client.get_protocols())
            await asyncio.sleep(5)
            return tasks

        if not baseline:
            enn = 5
            protocols = []
            for _ in range(enn):
                protocols.append(robot_client.post_protocol([Path("loooong.json")]))
            console.print(Panel(f"Analyze N = {enn}", style="bold dodger_blue1"))
            posts = await asyncio.gather(*protocols)
            for p in posts:
                await log_response(p)
            while not await robot_interactions.all_analyses_are_complete():
                responses.extend(await stressor())
        else:
            console.print(Panel("Baseline", style="bold dodger_blue1"))
            for _ in range(10):
                responses.extend(await stressor())
        # run the tasks
        timings: list[Timing] = []
        for resp in responses:
            timings.append(Timing(endpoint=str(resp.url), verb=resp.request.method, elapsed=resp.elapsed.total_seconds()))
            await log_response(resp)
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
        # # create many tasks
        # tasks = [task_coro(i) for i in range(10)]
        # # run the tasks
        # values = await asyncio.gather(*tasks)
        # for resp in values:
        #     console.print(post_protocol.text)
        # protocol_id = post_protocol.json()["data"]["id"]
        # post_protocol.json()["data"]["analysisSummaries"][0]["id"]
        # console.print(protocol_id)
        # await robot_interactions.wait_for_all_analyses_to_complete()
        # # analysis_resp = await robot_client.get_analysis(protocol_id=protocol_id, analysis_id=analysis_id)
        # # await log_response(analysis_resp)
        # # #assert analysis_resp.json()["data"]["status"] == "completed"
        # # assert analysis_resp.json()["data"]["result"] == "ok"
        # # run_resp = await robot_client.post_run(req_body={"data": {"protocolId": protocol_id}})
        # # await log_response(run_resp)
        # # run_id = run_resp.json()["data"]["id"]
        # # run_start_resp = await robot_client.post_run_action(run_id=run_id, req_body={"data": {"actionType": "play"}})
        # # await log_response(run_start_resp, print_timing=True)
        # # await robot_interactions.wait_until_run_status(run_id=run_id, expected_status="succeeded", timeout_sec=180, polling_interval_sec=3)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port(31950)
    wizard.reset_log(override=True)
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
