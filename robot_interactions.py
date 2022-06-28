import random
from typing import Any, Dict, List, Optional, cast

import anyio
from anyio import create_task_group
from httpcore import Response
from rich.console import Console
from rich.panel import Panel

from robot_client import RobotClient
from util import log_response


class RobotInteractions:
    """Reusable amalgamations of API calls to the robot."""

    def __init__(self, robot_client: RobotClient, console: Console = Console()) -> None:
        self.robot_client = robot_client
        self.console = console

    async def execute_command(
        self,
        run_id: str,
        req_body: Dict[str, Any],
        timeout_sec: float = 60.0,
        print_timing: bool = False,
        print_command: bool = True,
    ) -> Response:
        """Post a command to a run waiting until complete then log the response."""

        if print_command:
            self.console.print()
            self.console.print(
                Panel(
                    f"[bold green]Sending Command[/]",
                    style="bold magenta",
                )
            )
            self.console.print(req_body)
        if timeout_sec != 60.0:
            params = {"waitUntilComplete": True, "timeout": int(timeout_sec) * 1000}
        else:
            params = {"waitUntilComplete": True, "timeout": 59000}
        command: Response = await self.robot_client.post_run_command(
            run_id=run_id, req_body=req_body, params=params, timeout_sec=timeout_sec
        )
        await log_response(command, print_timing=print_timing, console=self.console)
        return command

    async def execute_simple_command(
        self,
        req_body: Dict[str, Any],
        timeout_sec: float = 60.0,
        print_timing: bool = False,
    ) -> Response:
        """Post a simple command waiting until complete then log the response."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold green]Sending Command[/]",
                style="bold magenta",
            )
        )
        self.console.print(req_body)
        if timeout_sec != 60.0:
            params = {"waitUntilComplete": True, "timeout": int(timeout_sec) * 1000}
        else:
            params = {"waitUntilComplete": True, "timeout": 59000}
        command = await self.robot_client.post_simple_command(req_body=req_body, params=params, timeout_sec=timeout_sec)
        await log_response(command, print_timing=print_timing, console=self.console)
        return command

    async def get_current_run(self, print_timing: bool = False) -> Optional[str]:
        """Post a simple command waiting until complete then log the response."""
        runs = await self.robot_client.get_runs()
        await log_response(runs, print_timing=print_timing, console=self.console)
        try:
            return runs.json()["links"]["current"]["href"].replace("/runs/", "")
        except KeyError:
            self.console.print("No current run.")
        return None

    async def get_module_id(self, module_model: str) -> str:
        """Given a moduleModel get the id of that module."""
        modules = await self.robot_client.get_modules()
        await log_response(modules)
        ids: List[str] = [module["id"] for module in modules.json()["data"] if module["moduleModel"] == module_model]
        if len(ids) > 1:
            raise ValueError(
                f"You have multiples of a module {module_model} attached and that is not supported."  # noqa: E501
            )
        elif len(ids) == 0:
            raise ValueError(f"No module attached to the robot has moduleModel of {module_model}")
        return ids[0]

    async def query_random_runs(self) -> None:
        runs = await self.robot_client.get_runs()
        run_ids = [run["id"] for run in runs.json()["data"]]
        random_runs = random.choices(run_ids, k=4)

        async def _get_and_log_run(run_id: str) -> None:
            response = await self.robot_client.get_run(run_id)
            await log_response(response, True)

        async with create_task_group() as tg:
            for run_id in random_runs:
                tg.start_soon(_get_and_log_run, run_id)

    async def get_module_data_by_id(self, module_id: str) -> Any:
        """Given a moduleModel get the id of that module."""
        modules = await self.robot_client.get_modules()
        await log_response(modules)
        data = [module for module in modules.json()["data"] if module["id"] == module_id]
        if len(data) == 0:
            raise ValueError(f"No module attached to the robot has id of {module_id}")
        return data[0]

    async def get_attached_pipettes(self) -> List[str]:
        pipettes = self.robot_client.get_pipettes()

    async def wait_until_run_status(
        self,
        run_id: str,
        expected_status: str,
    ) -> Dict[str, Any]:
        """Wait until a run achieves the expected status, returning its data."""
        with anyio.fail_after(15):  # if say a HS is shaking when you say stop it takes some seconds to actually stop
            get_run_response = await self.robot_client.get_run(run_id=run_id)

            while get_run_response.json()["data"]["status"] != expected_status:
                await anyio.sleep(0.1)
                get_run_response = await self.robot_client.get_run(run_id=run_id)

        return cast(Dict[str, Any], get_run_response.json()["data"])

    async def is_current_run_running(self) -> bool:
        """True if there is a current run and it is running, else False."""
        current_run_id = await self.get_current_run()
        if current_run_id:
            get_run_response = await self.robot_client.get_run(run_id=current_run_id)
            if get_run_response.json()["data"]["status"] in ["running"]:
                return True
        return False

    async def stop_run(self, run_id) -> Response:
        """Stop the run with this run_id"""
        return await self.robot_client.post_run_action(run_id=run_id, req_body={"data": {"actionType": "stop"}})

    async def un_current_run(self, run_id) -> Response:
        """Set the current value to False for this run_id"""
        return await self.robot_client.patch_run(run_id=run_id, req_body={"data": {"current": False}})

    async def force_create_new_run(self) -> str:
        """Create a new empty run.  Stop the current run if necessary."""
        run = await self.robot_client.post_run(req_body={"data": {}})
        await log_response(run)
        if run.status_code == 409:
            self.console.print(
                "There is a 409 conflict when creating the run.  Stopping current run and trying again.",
                style="bold red",
            )
            current_run_id = await self.robot_interactions.get_current_run()
            stop = await self.stop_run(current_run_id)
            assert stop.status_code == 201
            await self.robot_interactions.wait_until_run_status(run_id=current_run_id, expected_status="stopped")
            run = await self.robot_client.post_run(req_body={"data": {}})
            await log_response(run)
        return run.json()["data"]["id"]
