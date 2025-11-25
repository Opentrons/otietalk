# TODO(mm, 2022-06-21): Port this to a fully automated G-code snapshot test
# once we figure out how to get JSONv6 and PAPIv3 protocols running in the
# g-code-testing project.

import asyncio
import textwrap

import interactions.commands as commands
from clients.robot_client import RobotClient
from clients.robot_interactions import RobotInteractions
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from wizard.wizard import Wizard

PIPETTE = "p20_single_gen2"
MOUNT = "right"
TIP_RACK = "opentrons_96_tiprack_20ul"
TIP_RACK_SLOT = "1"

# Deck coordinates of the cross in the top-left of slot 7.
# Numbers copied from the ot2_standard.json deck definition.
CROSS_X = 12.13
CROSS_Y = 258.0
CROSS_Z = 0.0

# How high above the cross to put the nozzle of the pipette when there's no tip attached.
# We can't go all the way down to the cross because the pipette can't go that low.
# This value chosen to match the height of an opentrons_96_tiprack_20ul, for easy eyeballing.
NO_TIP_HEIGHT = 64.69

SLEEP_TIME = 1.0


async def main(robot_ip: str, robot_port: str) -> None:
    """Run the series of commands necessary to evaluate tip height against labware on the Heater Shaker."""  # noqa: E501
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)

        run_id = await robot_interactions.force_create_new_run()

        commands_to_run = [
            commands.load_labware_command(
                deck_slot_name=TIP_RACK_SLOT,
                load_name=TIP_RACK,
                namespace="opentrons",
                version=1,
                labware_id="tip_rack",
            ),
            commands.load_pipette_command(pipette_name=PIPETTE, mount=MOUNT, pipette_id="pipette"),
            commands.home_command(),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X,
                y=CROSS_Y,
                z=CROSS_Z + NO_TIP_HEIGHT,
            ),
            commands.pick_up_tip_command(
                pipette_id="pipette",
                labware_id="tip_rack",
                well_name="A1",
            ),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X,
                y=CROSS_Y,
                z=CROSS_Z,
            ),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X + 10,
                y=CROSS_Y,
                z=CROSS_Z,
            ),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X + 20,
                y=CROSS_Y,
                z=CROSS_Z,
                minimum_z_height=1,  # Lower than default, so shouldn't have any effect.
            ),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X + 30,
                y=CROSS_Y,
                z=CROSS_Z,
                # Should arc a bit higher than the default.
                # Tallest Opentrons tip rack is ~100 mm.
                minimum_z_height=130,
            ),
            commands.move_to_coordinates_command(
                pipette_id="pipette",
                x=CROSS_X + 40,
                y=CROSS_Y,
                z=CROSS_Z,
                force_direct=True,
            ),
            # This drop-tip serves two purposes:
            # 1. It returns the tip, for convenience.
            # 2. It tests that the robot correctly plans an arc when it moves from
            #    a coordinate location to a well location. This specific case of
            #    returning to the last well location before the moveToCoordinates
            #    is especially important to test because one possible bug is that
            #    the robot still thinks it's in the same well and moves directly instead
            #    of moving in an arc.
            commands.drop_tip_command(pipette_id="pipette", labware_id="tip_rack", well_name="A1"),
        ]

        for command in commands_to_run:
            await robot_interactions.execute_command(run_id=run_id, req_body=command, print_timing=True)
            await asyncio.sleep(SLEEP_TIME)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    markdown_text = textwrap.dedent(
        f"""\
        # Live Check of Moving To Coordinates

        Please load:

        * A {PIPETTE} on the {MOUNT} mount.
        * A {TIP_RACK} in slot {TIP_RACK_SLOT}.

        The pipette should make the following movements:

        1. Move {NO_TIP_HEIGHT} mm above the cross in slot 7, without a tip.
        2. Pick up a tip.
        3. With a default arc height, touch the cross in slot 7.
        4. With a default arc height again, move 1 cm right.
        5. With higher arc height, move 1 cm right.
        6. Without any arc (dragging across the deck), move 1 cm right.
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
    asyncio.run(main(robot_ip=robot_ip, robot_port=robot_port))
