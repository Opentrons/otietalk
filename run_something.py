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
        RobotInteractions(robot_client=robot_client)
        # all_analyses = []
        # for protocol in (await robot_client.get_protocols()).json()["data"]:
        #     for summary in protocol["analysisSummaries"]:
        #         all_analyses.append({"protocol_id": protocol["id"], "analysis_id":summary["id"]})
        # console.print(all_analyses)
        # for analysis in all_analyses:
        #     console.print(f"getting {analysis}")
        #     result = await robot_client.get_analysis(
        #             protocol_id=analysis["protocol_id"], analysis_id=analysis["analysis_id"]
        #         )
        #     print(f"result = {result.json()['data']['result']}")
        #     await log_response(result, print_timing=True, console=console)

        result = await robot_client.get_health()
        await log_response(result, print_timing=True, console=console)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
