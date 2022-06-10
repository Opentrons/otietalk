from typing import Dict, List, Optional

import anyio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.theme import Theme

from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import is_valid_IPAddress, is_valid_port, log_response, prompt

custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})

console = Console(theme=custom_theme)


def validate_ip(ip: Optional[str] = None) -> str:
    if ip == "" or ip is None:
        ip = Prompt.ask(
            "Greetings what is [i]your[/i] [bold red]robot ip address[/] (like 192.168.50.89) ? ",
            default="192.168.50.89",
            show_default=False,
        )
    elif not is_valid_IPAddress(ip):
        ip = Prompt.ask(
            f"ip address [bold red]{ip}[/] is not valid, try again (like 192.168.50.89)",
            default="192.168.50.89",
            show_default=False,
        )
    if is_valid_IPAddress(ip):
        console.print(
            Panel(
                f"Great, that checks out as a valid ip, robot ip set to [bold green]{ip}[/]",
                style="bold magenta",
            )
        )
        return ip
    else:
        validate_ip(ip)


def validate_port(port: Optional[int | str] = None) -> str:
    if port == "" or port is None:
        port = Prompt.ask(
            "Greetings what is [i]your[/i] [bold red]robot port[/] (most likely it is 31950 and you can just hit"
            " enter) ?",
            console=console,
            default="31950",
            show_default=False,
        )
    elif not is_valid_port(port):
        port = Prompt.ask(
            f"[bold red]{port}[/] is not valid, enter a different value. (most likely it is 31950 and you can just hit"
            " enter) ",
            console=console,
            default="31950",
            show_default=False,
        )
    if is_valid_port(port):
        console.print(
            Panel(
                f"Great, that checks out as a valid port, robot port set to [bold green]{port}[/]",
                style="bold magenta",
            )
        )
        return port
    else:
        validate_port(port)


async def app():
    console.print(
        Panel(
            "Hello, let us measure some new Heater Shaker labware definitions! :smiley: ",
            style="bold magenta",
        )
    )
    ip = validate_ip()
    port = validate_port()
    async with RobotClient.make(host=f"http://{ip}", port=port, version="*") as robot_client:
        try:
            console.print("Let us make sure your robot is reachable.")
            await robot_client.wait_until_alive()
            health = await robot_client.get_health()
            console.print(f"Robot is reachable. Here is the {health.request.url} response")
            console.print(health.json())
            console.print(
                Panel(
                    "Now we will see what pipettes are attached.",
                    style="bold magenta",
                )
            )
            ri = RobotInteractions(robot_client=robot_client)
            pipettes = await robot_client.get_pipettes()
            console.print(pipettes.json())
            pipettes_json = pipettes.json()
            choices = []
            if not ((pipettes_json["left"]["name"] is None) or (pipettes_json["left"]["name"] == "none")):
                choices.append(pipettes_json["left"]["name"])
            if not ((pipettes_json["right"]["name"] is None) or (pipettes_json["right"]["name"] == "none")):
                choices.append(pipettes_json["right"]["name"])
            if len(choices) == 0:
                console.print(
                    "Looks like you have no pipettes attached.  Please attach a pipette and start over.",
                    style="danger",
                )
                raise RuntimeError("No pipettes attached.")
            default = None
            if len(choices) == 2:  # probably on Kansas robot select the right pipette
                default = choices[1]
            pipette = Prompt.ask(
                "Which pipette do you want to use?",
                choices=choices,
                default=default,
                show_default=False,
            )
            # this is necessary because you could have the same pipette on both sides.
            pipette_mount = Prompt.ask(
                "Which side is the pipette you chose on ?",
                choices=["left", "right"],
                default="right",
                show_default=False,
            )
            console.print(
                Panel(
                    f"Great, we will use pipette [bold green]{pipette}[/] on the [bold green]{pipette_mount}[/]",
                    style="bold magenta",
                )
            )
            use_tiprack = Confirm.ask("Will you be using a tiprack and picking up a tip?")
            tiprack_name = None
            tiprack_slot = None
            #############################
            if use_tiprack:
                tiprack_name = Prompt.ask(
                    """
What is the name of the tiprack you will use?
Some common ones are:
opentrons_96_tiprack_10ul
opentrons_96_tiprack_20ul
opentrons_96_tiprack_300ul
opentrons_96_tiprack_1000ul
"""
                )
                console.print(
                    Panel(
                        f"Great, we will use tiprack [bold green]{tiprack_name}[/]",
                        style="bold magenta",
                    )
                )
                tiprack_slot = str(IntPrompt.ask("What slot will the tiprack be in (1-11)?", console=console))
            ##############################
            hs_id = await ri.get_module_id(module_model="heaterShakerModuleV1")
            # what location for the HS?
            choices = ["1", "3", "4", "6"]
            if tiprack_slot:
                if tiprack_slot in choices:
                    choices.remove(tiprack_slot)
            hs_slot = str(
                IntPrompt.ask(
                    f"What slot will the Heater Shaker be in {choices} ?",
                    console=console,
                    choices=choices,
                )
            )
            hs_labware = [
                "opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat",
                "opentrons_96_pcr_plate_adapter_nest_wellplate_100ul_pcr_full_skirt",
                "opentrons_96_deepwell_adapter_nest_wellplate_2ml_deep",
                "opentrons_flat_plate_adapter_corning_384_wellplate_112ul_flat",
            ]
            labware = Prompt.ask("Which labware are you testing?", choices=hs_labware)
            console.print(
                Panel(
                    f"""
Now we are ready to do work and move the pipette.
Please set up your robot.
{f'Place [bold green]{tiprack_name}[/] tiprack in slot [bold green]{tiprack_slot}[/]' if use_tiprack  else ''}
Place the [bold green]Heater Shaker[/] in slot [bold green]{hs_slot}[/]
With its [bold green]{labware}[/] on top.
Clear the rest of the deck so there are no collisions.
""",
                    style="bold magenta",
                )
            )
            run = await robot_client.post_run(req_body={"data": {}})
            await log_response(run)
            run_id = run.json()["data"]["id"]
            load_module_command = {
                "data": {
                    "commandType": "loadModule",
                    "params": {
                        "model": "heaterShakerModuleV1",
                        "location": {"slotName": hs_slot},
                        "moduleId": hs_id,
                    },
                }
            }
            await ri.execute_command(run_id=run_id, req_body=load_module_command)

            load_labware_command = {
                "data": {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"moduleId": hs_id},
                        "loadName": labware,
                        "namespace": "opentrons",
                        "version": 1,
                        "labwareId": "target",
                    },
                }
            }
            await ri.execute_command(run_id=run_id, req_body=load_labware_command)

            load_pipette_command = {
                "data": {
                    "commandType": "loadPipette",
                    "params": {
                        "pipetteName": pipette,
                        "mount": pipette_mount,
                        "pipetteId": "pipette",
                    },
                }
            }
            await ri.execute_command(run_id=run_id, req_body=load_pipette_command)
            ########################
            if use_tiprack:
                load_tiprack_command = {
                    "data": {
                        "commandType": "loadLabware",
                        "params": {
                            "location": {"slotName": tiprack_slot},
                            "loadName": tiprack_name,
                            "namespace": "opentrons",
                            "version": 1,
                            "labwareId": "tips",
                        },
                    }
                }
                await ri.execute_command(run_id=run_id, req_body=load_tiprack_command)

                pickup_tip_command = {
                    "data": {
                        "commandType": "pickUpTip",
                        "params": {
                            "pipetteId": "pipette",
                            "labwareId": "tips",
                            "wellName": "A1",
                        },
                    }
                }
                await prompt("When you are ready to pick up the tip hit enter.")
                console.print("Picking up tip.")
                await ri.execute_command(run_id=run_id, req_body=pickup_tip_command)
            #########################
            await prompt("When you are ready to move to pipette to the Heater Shaker press enter.")
            mapping: Dict[str, List[str]] = {
                "opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat": [
                    "A1",
                    "A12",
                    "H1",
                    "H12",
                    "D6",
                ],
                "opentrons_96_pcr_plate_adapter_nest_wellplate_100ul_pcr_full_skirt": [
                    "A1",
                    "A12",
                    "H1",
                    "H12",
                    "D6",
                ],
                "opentrons_96_deepwell_adapter_nest_wellplate_2ml_deep": [
                    "A1",
                    "A12",
                    "H1",
                    "H12",
                    "D6",
                ],
                "opentrons_flat_plate_adapter_corning_384_wellplate_112ul_flat": [
                    "A1",
                    "A24",
                    "P1",
                    "P24",
                    "H12",
                ],
            }
            wells_on_hs = mapping[labware]
            for well in wells_on_hs:
                move_to_well_command = {
                    "data": {
                        "commandType": "moveToWell",
                        "params": {
                            "pipetteId": "pipette",
                            "labwareId": "target",
                            "wellName": well,
                        },
                    }
                }
                await ri.execute_command(run_id=run_id, req_body=move_to_well_command)
                await prompt(f"At well {well} press Enter to move to the next well.")
            if use_tiprack:
                drop_tip_command = {
                    "data": {
                        "commandType": "dropTip",
                        "params": {
                            "pipetteId": "pipette",
                            "labwareId": "tips",
                            "wellName": "A1",
                        },
                    }
                }
                await prompt("When you are ready to drop the tip hit enter")
                print("Dropping tip.")
                await ri.execute_command(run_id=run_id, req_body=drop_tip_command)
            await prompt("When you are ready to home hit enter")
            home_command = {
                "data": {
                    "commandType": "home",
                    "params": {},
                }
            }
            console.print("Homing.", style="info")
            await ri.execute_command(run_id=run_id, req_body=home_command)
        except Exception:
            console.print_exception()


if __name__ == "__main__":
    anyio.run(app)
