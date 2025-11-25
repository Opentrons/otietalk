# upload protocol
# wait for analysis good
# start run
# wait for run to finish
# repeat

import asyncio
from pathlib import Path

from clients.robot_client import RobotClient
from clients.robot_interactions import RobotInteractions
from rich.console import Console
from rich.theme import Theme
from util.util import log_response
from wizard.wizard import Wizard


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
        post_protocol = await robot_client.post_protocol([Path("basic.json")])
        await log_response(post_protocol, True, console)
        console.print(post_protocol.text)
        protocol_id = post_protocol.json()["data"]["id"]
        post_protocol.json()["data"]["analysisSummaries"][0]["id"]
        console.print(protocol_id)
        await robot_interactions.wait_for_all_analyses_to_complete()
        # analysis_resp = await robot_client.get_analysis(protocol_id=protocol_id, analysis_id=analysis_id)
        # await log_response(analysis_resp)
        # #assert analysis_resp.json()["data"]["status"] == "completed"
        # assert analysis_resp.json()["data"]["result"] == "ok"
        # run_resp = await robot_client.post_run(req_body={"data": {"protocolId": protocol_id}})
        # await log_response(run_resp)
        # run_id = run_resp.json()["data"]["id"]
        # run_start_resp = await robot_client.post_run_action(run_id=run_id, req_body={"data": {"actionType": "play"}})
        # await log_response(run_start_resp, print_timing=True)
        # await robot_interactions.wait_until_run_status(run_id=run_id, expected_status="succeeded", timeout_sec=180, polling_interval_sec=3)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
