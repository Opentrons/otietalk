from __future__ import annotations

import asyncio

import pytest
from commands import (
    close_latch_command,
    deactivate_heater_command,
    load_module_command,
    open_latch_command,
    set_target_shake_speed_command,
    set_target_temp_command,
    stop_shake_command,
    wait_for_temp_command,
)
from httpcore import Response
from rich.console import Console
from robot_client import RobotClient
from robot_interactions import RobotInteractions

HS_SLOT = "1"
HS_SHAKE_SPEED_RANGE = 40
HS_TEMP_RANGE = 2
VALID_HEAT_TARGET = 38
VALID_HEAT_TARGET_PLUS_2 = 40


def shake_speed_in_range(actual: float, target: float, range: float = HS_SHAKE_SPEED_RANGE) -> bool:
    if target - range / 2 <= actual <= target + range / 2:
        return True
    return False


def temp_in_range(actual: float, target: float, range: float = HS_TEMP_RANGE) -> bool:
    if target - range / 2 <= actual <= target + range / 2:
        return True
    return False


class HSTestRun:
    run_id: str
    hs_id: str
    robot_client: RobotClient
    robot_interactions: RobotInteractions
    console: Console

    @classmethod
    async def create(cls, robot_client, robot_interactions, console) -> HSTestRun:
        self: HSTestRun = HSTestRun()
        self.robot_client: RobotClient = robot_client
        self.robot_interactions: RobotInteractions = robot_interactions
        self.console = console
        self.hs_id = await robot_interactions.get_module_id(module_model="heaterShakerModuleV1")
        self.run_id = await self.robot_interactions.force_create_new_run()
        await robot_interactions.execute_command(
            run_id=self.run_id,
            req_body=load_module_command(model="heaterShakerModuleV1", slot_name=HS_SLOT, module_id=self.hs_id),
        )
        return self


async def ensure_latch_closed_not_heating_or_shaking(hs_run) -> None:
    # make sure not heating
    deactivate_heater = await hs_run.robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=deactivate_heater_command(hs_id=hs_run.hs_id)
    )
    assert deactivate_heater.status_code == 201
    assert deactivate_heater.json()["data"]["status"] == "succeeded"

    # make sure latch is closed
    close_latch: Response = await hs_run.robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=close_latch_command(hs_id=hs_run.hs_id)
    )
    assert close_latch.status_code == 201
    assert close_latch.json()["data"]["status"] == "succeeded"

    # make sure not shaking
    stop_shake = await hs_run.robot_interactions.execute_command(run_id=hs_run.run_id, req_body=stop_shake_command(hs_id=hs_run.hs_id))
    assert stop_shake.status_code == 201
    assert close_latch.json()["data"]["status"] == "succeeded"

    # wait then make sure shake speed is zero
    await asyncio.sleep(2)
    hs_module_data = await hs_run.robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], 0)
    # We are now in a known state, no heating, no shaking, latch closed


@pytest.mark.asyncio
async def test_shake_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send a shake command to HS that has a latch closed.  HS should shake."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 400.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    await asyncio.sleep(5)  # see with eyeballs the shake
    # stop the shaking
    stop_shake = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=stop_shake_command(hs_id=hs_run.hs_id))
    assert stop_shake.status_code == 201
    assert stop_shake.json()["data"]["status"] == "succeeded"

    # wait then make sure shake speed is zero
    await asyncio.sleep(2)
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], 0)


@pytest.mark.asyncio
async def test_temp_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send a temp command to HS."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to heat
    celsius: float = 38
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id,
        req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius),
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


@pytest.mark.asyncio
async def test_heat_and_shake_happy_path(robot_client: RobotClient, console: Console) -> None:
    """Send a temp command to HS."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 333.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # try to heat
    celsius: float = VALID_HEAT_TARGET
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius), timeout_sec=120
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


@pytest.mark.asyncio
async def test_shake_blocked_by_open_latch(robot_client: RobotClient, console: Console) -> None:
    """Send a shake command to HS that has a latch not closed.  HS should not shake."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # make sure latch is open
    open_latch: Response = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=open_latch_command(hs_id=hs_run.hs_id))
    assert open_latch.status_code == 201
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["labwareLatchStatus"] == "idle_open"

    # try to shake
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=400)
    )
    console.print(shake.json())
    assert shake.json()["data"]["status"] == "failed"
    assert shake.json()["data"]["error"]["detail"] == "Heater-Shaker cannot start shaking while the labware latch is open."


@pytest.mark.asyncio
async def test_open_latch_while_shaking(robot_client: RobotClient, console: Console) -> None:
    """Send an open latch command to HS that is shaking.  HS should not allow the latch to open."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 400.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # try to open the latch
    open_latch: Response = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=open_latch_command(hs_id=hs_run.hs_id))
    console.print(open_latch.json())
    assert open_latch.json()["data"]["status"] == "failed"
    assert open_latch.json()["data"]["error"]["detail"] == "Heater-Shaker cannot open its labware latch while it is shaking."


@pytest.mark.asyncio
async def test_open_latch_while_latch_already_open(robot_client: RobotClient, console: Console) -> None:
    """Send an open latch command to HS that has an open latch. Should cause no issue."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to open the latch
    open_latch: Response = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=open_latch_command(hs_id=hs_run.hs_id))
    assert open_latch.status_code == 201
    assert open_latch.json()["data"]["status"] == "succeeded"

    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["labwareLatchStatus"] == "idle_open"

    # try to open the latch again
    open_latch: Response = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=open_latch_command(hs_id=hs_run.hs_id))
    assert open_latch.status_code == 201
    assert open_latch.json()["data"]["status"] == "succeeded"

    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["labwareLatchStatus"] == "idle_open"


@pytest.mark.asyncio
async def test_close_latch_while_latch_already_closed(robot_client: RobotClient, console: Console) -> None:
    """Send a close latch command to HS that has a closed latch. Should cause no issue."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to close the already closed latch
    close_latch: Response = await robot_interactions.execute_command(run_id=hs_run.run_id, req_body=close_latch_command(hs_id=hs_run.hs_id))
    assert close_latch.status_code == 201
    assert close_latch.json()["data"]["status"] == "succeeded"
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["labwareLatchStatus"] == "idle_closed"


@pytest.mark.asyncio
async def test_increase_shake_rate_while_shaking(robot_client: RobotClient, console: Console) -> None:
    """Increase the shake rate while already shaking. Should cause no issue."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 400.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # increase the shake rate
    rpm = 800.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # intentionally no teardown.  We do setup, not teardown.
    # HS should be shaking at 800 rpm


@pytest.mark.asyncio
async def test_decrease_shake_rate_while_shaking(robot_client: RobotClient, console: Console) -> None:
    """Decrease the shake rate while already shaking. Should cause no issue."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 555.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # decrease the shake rate
    rpm = 444
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # intentionally no teardown.  We do setup, not teardown.
    # HS should be shaking at 444 rpm


@pytest.mark.parametrize(
    "rpm",
    [(199.99), (0.0), (-5.6), (3000.1), (10000.0)],
)
@pytest.mark.asyncio
async def test_invalid_shake_speed(robot_client: RobotClient, console: Console, rpm: float) -> None:
    """Receive proper error responses when setting shake to invalid rpm."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "failed"
    assert shake.json()["data"]["error"]["errorType"] == "InvalidTargetSpeedError"
    assert (
        shake.json()["data"]["error"]["detail"]
        == f"Cannot set Heater-Shaker to shake at {rpm} rpm. Valid speed range is SpeedRange(min=200, max=3000) rpm."
    )


@pytest.mark.parametrize(
    "rpm",
    [
        (200.0),
        # (3000.0),
    ],
)
@pytest.mark.asyncio
async def test_boundary_shake_speed(robot_client: RobotClient, console: Console, rpm: float) -> None:
    """Setting shake rpm to boundary is valid."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    if rpm > 200:
        # TODO it seems heaterShaker/setAndWaitForShakeSpeed is not waiting?
        await asyncio.sleep(3)

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm, 100)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # intentionally no teardown.  We do setup, not teardown.
    # HS should be shaking at 200 or 3000 rpm


@pytest.mark.parametrize(
    "celsius",
    [(36.99), (0.0), (96.1), (1000.0), (-1.0)],
)
@pytest.mark.asyncio
async def test_out_of_range_temp(robot_client: RobotClient, console: Console, celsius: float) -> None:
    """Setting temperature to out of range temps throws appropriate error."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to set temp
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "failed"
    assert temp.json()["data"]["error"]["errorType"] == "InvalidTargetTemperatureError"
    assert (
        temp.json()["data"]["error"]["detail"]
        == f"Cannot set Heater-Shaker to {celsius} °C. Valid range is TemperatureRange(min=37, max=95) °C."
    )

    # is temp state idle?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "idle"


@pytest.mark.asyncio
async def test_increase_temp_while_heating(robot_client: RobotClient, console: Console) -> None:
    """While the HS is already heating, set to a new higher temp."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to heat
    celsius: float = VALID_HEAT_TARGET
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    # try to heat to a new higher temp
    celsius: float = VALID_HEAT_TARGET_PLUS_2
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius), timeout_sec=180
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


@pytest.mark.asyncio
async def test_decrease_temp_while_heating(robot_client: RobotClient, console: Console) -> None:
    """While the HS is already heating, set to a new lower temp."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to heat
    celsius: float = 40
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    # try to cool (passive) to a new lower temp
    # cooling takes a while since it is not active
    # I put my hand on it as a heat sink
    celsius: float = 37
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius), timeout_sec=300
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


@pytest.mark.parametrize(
    "target_rpm",
    [(199.99), (3000.1)],
)
@pytest.mark.asyncio
async def test_shake_rate_invalid_while_shaking(robot_client: RobotClient, console: Console, target_rpm: float) -> None:
    """Decrease the shake rate while already shaking. Should cause no issue."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to shake
    rpm: float = 555.00
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "succeeded"

    # is shaking at desired rpm?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # shake at invalid rpm
    shake = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_shake_speed_command(hs_id=hs_run.hs_id, rpm=target_rpm)
    )
    assert shake.status_code == 201
    assert shake.json()["data"]["status"] == "failed"
    assert shake.json()["data"]["error"]["errorType"] == "InvalidTargetSpeedError"
    assert (
        shake.json()["data"]["error"]["detail"]
        == f"Cannot set Heater-Shaker to shake at {target_rpm} rpm. Valid speed range is SpeedRange(min=200, max=3000) rpm."
    )

    # is shaking at desired rpm? - just like above
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert shake_speed_in_range(hs_module_data["data"]["currentSpeed"], rpm)
    assert hs_module_data["data"]["speedStatus"] == "holding at target"

    # intentionally no teardown.  We do setup, not teardown.
    # HS should be shaking at 555 rpm


@pytest.mark.parametrize(
    "celsius_target",
    [(36.99), (96.1)],
)
@pytest.mark.asyncio
async def test_invalid_temp_while_heating(robot_client: RobotClient, console: Console, celsius_target: float) -> None:
    """While the HS is already heating, set to a invalid temp."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to heat
    celsius: float = 38
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius_target)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "failed"
    assert temp.json()["data"]["error"]["errorType"] == "InvalidTargetTemperatureError"
    assert (
        temp.json()["data"]["error"]["detail"]
        == f"Cannot set Heater-Shaker to {celsius_target} °C. Valid range is TemperatureRange(min=37, max=95) °C."
    )

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius), timeout_sec=300
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


# at the end, takes the longest.
@pytest.mark.parametrize(
    "celsius",
    [
        (37.0),
        # (95.0),
    ],
)
@pytest.mark.asyncio
async def test_boundary_temp(robot_client: RobotClient, console: Console, celsius: float) -> None:
    """Setting temperature to boundary is valid."""
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    # create a new run and load the HS module into that run
    hs_run: HSTestRun = await HSTestRun.create(robot_client=robot_client, robot_interactions=robot_interactions, console=console)

    await ensure_latch_closed_not_heating_or_shaking(hs_run=hs_run)

    # try to heat
    temp = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=set_target_temp_command(hs_id=hs_run.hs_id, celsius=celsius)
    )
    assert temp.status_code == 201
    assert temp.json()["data"]["status"] == "succeeded"

    wait = await robot_interactions.execute_command(
        run_id=hs_run.run_id, req_body=wait_for_temp_command(hs_id=hs_run.hs_id, celsius=celsius), timeout_sec=300
    )
    assert wait.status_code == 201
    assert wait.json()["data"]["status"] == "succeeded"

    # is temp at desired state?
    hs_module_data = await robot_interactions.get_module_data_by_id(hs_run.hs_id)
    assert hs_module_data["data"]["temperatureStatus"] == "holding at target"
    assert temp_in_range(hs_module_data["data"]["currentTemperature"], celsius)


@pytest.mark.asyncio
async def test_hmm(robot_client: RobotClient, console: Console) -> None:
    robot_interactions: RobotInteractions = RobotInteractions(robot_client=robot_client)
    for _ in range(1):
        await robot_interactions.hmm()
