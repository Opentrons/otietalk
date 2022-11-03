from __future__ import annotations

import asyncio
from typing import Any, Dict, cast

import anyio
import pytest
from httpcore import Response
from rich.console import Console
from rich.panel import Panel

from commands import (
    close_latch_command,
    close_lid,
    deactivate_heater_command,
    load_module_command,
    open_latch_command,
    open_lid,
    set_target_shake_speed_command,
    set_target_temp_command,
    stop_shake_command,
    wait_for_temp_command,
    set_block_temp,
    wait_block_temp,
    deactivate_block,
    deactivate_lid,
    set_lid_temp,
    wait_lid_temp,
)
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response

TC_SLOT = "7"

TEMP_RANGE = 2


def temp_in_range(actual: float, target: float, range: float = TEMP_RANGE) -> bool:
    if target - range / 2 <= actual <= target + range / 2:
        return True
    return False


class TCTestRun:
    run_id: str
    tc_id: str
    robot_client: RobotClient
    robot_interactions: RobotInteractions
    console: Console

    @classmethod
    async def create(cls, robot_client, robot_interactions, console) -> TCTestRun:
        self: TCTestRun = TCTestRun()
        self.robot_client: RobotClient = robot_client
        self.robot_interactions: RobotInteractions = robot_interactions
        self.console = console
        self.tc_id = await robot_interactions.get_module_id(module_model="thermocyclerModuleV1")
        self.run_id = await self.robot_interactions.force_create_new_run()
        await robot_interactions.execute_command(
            run_id=self.run_id,
            req_body=load_module_command(model="thermocyclerModuleV1", slot_name=TC_SLOT, module_id=self.tc_id),
        )
        return self


async def starting_state(tc_run):
    # open the lid
    tc_module_data = await tc_run.robot_interactions.get_module_data_by_id(tc_run.tc_id)
    if tc_module_data["data"]["lidStatus"] != "open":
        lid = await tc_run.robot_interactions.execute_command(
            run_id=tc_run.run_id, req_body=open_lid(tc_id=tc_run.tc_id)
        )
        assert lid.status_code == 201
        assert lid.json()["data"]["status"] == "succeeded"
    # deactivate block
    if tc_module_data["data"]["status"] != "idle":
        block = await tc_run.robot_interactions.execute_command(
            run_id=tc_run.run_id, req_body=deactivate_block(tc_id=tc_run.tc_id)
        )
        assert block.status_code == 201
        assert block.json()["data"]["status"] == "succeeded"
    # deactivate lid
    if tc_module_data["data"]["lidTemperatureStatus"] != "idle":
        lid = await tc_run.robot_interactions.execute_command(
            run_id=tc_run.run_id, req_body=deactivate_lid(tc_id=tc_run.tc_id)
        )
        assert lid.status_code == 201
        assert lid.json()["data"]["status"] == "succeeded"
    # is lid open, lid deactivated and block deactivated?
    tc_module_data = await tc_run.robot_interactions.get_module_data_by_id(tc_run.tc_id)
    assert tc_module_data["data"]["lidStatus"] == "open"
    assert tc_module_data["data"]["lidTemperatureStatus"] == "idle"
    assert tc_module_data["data"]["status"] == "idle"
    tc_run.console.print(
        Panel(
            "Thermocycler lid open, block deactivated, and lid deactivated.",
            style="bold dark_orange",
        )
    )


@pytest.mark.asyncio
async def test_close_lid_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send an close lid command to TC.  Command should succeed and module data should report it is closed."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the TC module into that run
    tc_run: TCTestRun = await TCTestRun.create(
        robot_client=robot_client, robot_interactions=robot_interactions, console=console
    )
    await starting_state(tc_run=tc_run)
    lid = await robot_interactions.execute_command(run_id=tc_run.run_id, req_body=close_lid(tc_id=tc_run.tc_id))
    assert lid.status_code == 201
    assert lid.json()["data"]["status"] == "succeeded"

    # is lid closed?
    tc_module_data = await robot_interactions.get_module_data_by_id(tc_run.tc_id)
    assert tc_module_data["data"]["lidStatus"] == "closed"


@pytest.mark.asyncio
async def test_set_block_temp_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send an close lid command to TC.  Command should succeed and module data should report it is closed."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the TC module into that run
    tc_run: TCTestRun = await TCTestRun.create(
        robot_client=robot_client, robot_interactions=robot_interactions, console=console
    )
    target_temp = 27
    await starting_state(tc_run=tc_run)
    block = await robot_interactions.execute_command(
        run_id=tc_run.run_id, req_body=set_block_temp(tc_id=tc_run.tc_id, celsius=target_temp, block_max_volume_ul=10)
    )
    assert block.status_code == 201
    assert block.json()["data"]["status"] == "succeeded"

    wait_block = await robot_interactions.execute_command(
        run_id=tc_run.run_id, req_body=wait_block_temp(tc_id=tc_run.tc_id)
    )
    assert wait_block.status_code == 201
    assert wait_block.json()["data"]["status"] == "succeeded"

    # is temp reached?
    tc_module_data = await robot_interactions.get_module_data_by_id(tc_run.tc_id)
    actual_temp = tc_module_data["data"]["currentTemperature"]
    assert temp_in_range(actual_temp, target_temp)

@pytest.mark.asyncio
async def test_set_lid_temp_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send an close lid command to TC.  Command should succeed and module data should report it is closed."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the TC module into that run
    tc_run: TCTestRun = await TCTestRun.create(
        robot_client=robot_client, robot_interactions=robot_interactions, console=console
    )
    target_temp = 37
    await starting_state(tc_run=tc_run)
    lid = await robot_interactions.execute_command(
        run_id=tc_run.run_id, req_body=set_lid_temp(tc_id=tc_run.tc_id, celsius=target_temp)
    )
    assert lid.status_code == 201
    assert lid.json()["data"]["status"] == "succeeded"

    wait_lid = await robot_interactions.execute_command(
        run_id=tc_run.run_id, req_body=wait_lid_temp(tc_id=tc_run.tc_id)
    )
    assert wait_lid.status_code == 201
    assert wait_lid.json()["data"]["status"] == "succeeded"

    # is temp reached?
    tc_module_data = await robot_interactions.get_module_data_by_id(tc_run.tc_id)
    actual_temp = tc_module_data["data"]["lidTemperature"]
    assert temp_in_range(actual_temp, target_temp)

#

"thermocycler/runProfile"

