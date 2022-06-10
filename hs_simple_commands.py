import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from robot_client import RobotClient
from robot_interactions import RobotInteractions
from wizard import Wizard

HS_SLOT = "1"


async def hs_commands(robot_ip: str, robot_port: str) -> None:
    """Run the series of commands necessary to evaluate tip height against labware on the Heater Shaker."""  # noqa: E501
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
        hs_id = await robot_interactions.get_module_id(module_model="heaterShakerModuleV1")

        open_latch_command = {
            "data": {
                "commandType": "heaterShakerModule/openLatch",
                "params": {
                    "moduleId": hs_id,
                },
            }
        }

        close_latch_command = {
            "data": {
                "commandType": "heaterShakerModule/closeLatch",
                "params": {
                    "moduleId": hs_id,
                },
            }
        }

        set_target_shake_speed_command = {
            "data": {
                "commandType": "heaterShakerModule/setTargetShakeSpeed",
                "params": {
                    "moduleId": hs_id,
                    "rpm": 300,
                },
            }
        }

        stop_shake_command = {
            "data": {
                "commandType": "heaterShakerModule/stopShake",
                "params": {
                    "moduleId": hs_id,
                },
            }
        }

        set_target_temp_command = {
            "data": {
                "commandType": "heaterShakerModule/startSetTargetTemperature",
                "params": {
                    "moduleId": hs_id,
                    "temperature": 37,
                },
            }
        }

        deactivate_heater_command = {
            "data": {
                "commandType": "heaterShakerModule/deactivateHeater",
                "params": {
                    "moduleId": hs_id,
                },
            }
        }

        commands = [
            open_latch_command,
            close_latch_command,
            set_target_shake_speed_command,
            stop_shake_command,
            set_target_temp_command,
            deactivate_heater_command,
        ]

        for command in commands:
            console.print(
                Panel(
                    f"[bold green]Sending Command[/]",
                    style="bold magenta",
                )
            )
            console.print(command)
            await robot_interactions.execute_simple_command(req_body=command, print_timing=True)
            if command["data"]["commandType"] in ["heaterShakerModule/deactivateHeater"]:
                console.print(Panel(f"Wait 3 seconds to see if deactivate works.", style="bold blue"))
                await asyncio.sleep(3)
            hs_module_data = await robot_interactions.get_module_data_by_id(hs_id)
            console.print("Module data after the command completes")
            console.print(hs_module_data)
            if command["data"]["commandType"] in ["heaterShakerModule/setTargetShakeSpeed"]:
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
            f"""
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
