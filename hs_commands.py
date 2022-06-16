import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from commands import (
    close_latch_command,
    deactivate_heater_command,
    open_latch_command,
    set_target_shake_speed_command,
    set_target_temp_command,
    stop_shake_command,
    wait_for_temp_command,
)
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard

HS_SLOT = "1"


async def hs_commands(robot_ip: str, robot_port: str) -> None:
    """Run the series of commands necessary to evaluate tip height against labware on the Heater Shaker."""  # noqa: E501
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
        hs_id = await robot_interactions.get_module_id(module_model="heaterShakerModuleV1")
        run = await robot_client.post_run(req_body={"data": {}})
        await log_response(run)
        run_id = run.json()["data"]["id"]
        load_module_command = {
            "data": {
                "commandType": "loadModule",
                "params": {
                    "model": "heaterShakerModuleV1",
                    "location": {"slotName": HS_SLOT},
                    "moduleId": hs_id,
                },
            }
        }
        await robot_interactions.execute_command(run_id=run_id, req_body=load_module_command)

        _open_latch_command = open_latch_command(hs_id)
        _close_latch_command = close_latch_command(hs_id)
        _set_target_shake_speed_command = set_target_shake_speed_command(hs_id, 300)

        _stop_shake_command = stop_shake_command(hs_id)

        _set_target_temp_command = set_target_temp_command(hs_id, 37.00)
        _wait_for_temp_command = wait_for_temp_command(hs_id, 37.00)

        _deactivate_heater_command = deactivate_heater_command(hs_id)

        commands = [
            _open_latch_command,
            _close_latch_command,
            _set_target_shake_speed_command,
            _stop_shake_command,
            _set_target_temp_command,
            _wait_for_temp_command,
            _deactivate_heater_command,
        ]

        for command in commands:
            await robot_interactions.execute_command(run_id=run_id, req_body=command, print_timing=True)
            if command["data"]["commandType"] in ["heaterShaker/deactivateHeater"]:
                console.print(Panel(f"Wait 3 seconds to see if deactivate works.", style="bold blue"))
                await asyncio.sleep(3)
            hs_module_data = await robot_interactions.get_module_data_by_id(hs_id)
            console.print(f"Module data after the {command['data']['commandType']} completes")
            console.print(hs_module_data)
            if command["data"]["commandType"] in ["heaterShaker/setAndWaitForShakeSpeed"]:
                shake_watch_seconds = 10
                console.print(
                    Panel(f"Take a look I should be shaking!!! For {shake_watch_seconds} seconds.", style="bold blue")
                )
                await asyncio.sleep(shake_watch_seconds)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    console.print(
        Panel(
            """
Check HS Commands Live
Hello, let us send commands to a Heater Shaker :smiley:
1. Have a heater shaker connected via USB and powered on.
2. Have your heater shaker secured in a slot and the deck clear (just in case).
3. Note that all commands are being sent with waitUntilComplete=true & timeout=59000
""",
            style="bold magenta",
        )
    )
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(hs_commands(robot_ip=robot_ip, robot_port=robot_port))
