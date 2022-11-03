import asyncio
import random
import time
from typing import Any, Dict, List, Optional, cast

import anyio
import httpx
from anyio import create_task_group
from httpcore import Response
from rich.console import Console
from rich.panel import Panel

from robot_client import RobotClient
from util import log_response


def timeit(func):
    async def process(func, *args, **params):
        if asyncio.iscoroutinefunction(func):
            print("this function is a coroutine: {}".format(func.__name__))
            return await func(*args, **params)
        else:
            print("this is not a coroutine")
            return func(*args, **params)

    async def helper(*args, **params):
        print("{}.time".format(func.__name__))
        start = time.time()
        result = await process(func, *args, **params)

        # Test normal function route...
        # result = await process(lambda *a, **p: print(*a, **p), *args, **params)

        print("This function took ", time.time() - start)
        return result

    return helper


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
        panel = Panel(
            f"[bold green]Sending Command[/]",
            style="bold magenta",
        )
        if print_command:
            self.console.print()
            self.console.print(panel)
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
        if len(ids) == 0:
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

    @timeit
    async def wait_until_run_status(
        self,
        run_id: str,
        expected_status: str,
        timeout_sec: int = 15,
    ) -> Dict[str, Any]:
        """Wait until a run achieves the expected status, returning its data."""
        with anyio.fail_after(
            timeout_sec
        ):  # if say a HS is shaking when you say stop it takes some seconds to actually stop
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

    async def stop_run(self, run_id) -> Optional[Response]:
        """Stop the run with this run_id"""
        try:
            return await self.robot_client.post_run_action(run_id=run_id, req_body={"data": {"actionType": "stop"}})
        except httpx.ReadTimeout:
            self.console.print(
                f"Stopping run {run_id} timed out....",
                style="bold red",
            )
        return None

    async def un_current_run(self, run_id) -> Optional[Response]:
        """Set the current value to False for this run_id"""
        try:
            return await self.robot_client.patch_run(run_id=run_id, req_body={"data": {"current": False}})
        except httpx.ReadTimeout:
            self.console.print(
                f"PATCHing current run {run_id} to current = False timed out....",
                style="bold red",
            )
        return None

    async def force_create_new_run(self) -> str:
        """Create a new empty run.  Stop the current run and uncurrent if necessary."""
        run_post_fail = False
        run = None
        try:
            run = await self.robot_client.post_run(req_body={"data": {}})
            await log_response(run)
        except httpx.ReadTimeout:
            self.console.print(
                "POSTing empty Run timed out....",
                style="bold red",
            )
            run_post_fail = True
        if run and run.status_code != 201 or run_post_fail:
            if run:
                self.console.print(
                    f"Post Run status code was {run.status_code}",
                    style="bold red",
                )
            current_run_id = await self.get_current_run()
            await self.stop_run(current_run_id)
            stop_timeout_sec = 15
            await self.wait_until_run_status(
                run_id=current_run_id, expected_status="stopped", timeout_sec=stop_timeout_sec
            )
            run = await self.get_current_run()
            if run:
                delete_run = await self.robot_client.delete_run(run)
                await log_response(delete_run)
                run = await self.get_current_run()
                assert run is None
                await self.un_current_run(run)
            run = await self.robot_client.post_run(req_body={"data": {}})
            await log_response(run)
        return run.json()["data"]["id"]

    async def hmm(self):
        run = await self.robot_client.post_run(req_body={"data": {}})
        await log_response(run, print_timing=True)
        current_run_id = await self.get_current_run(print_timing=True)
        self.execute_simple_command()
        stop = await self.stop_run(current_run_id)
        await log_response(stop, print_timing=True)
        #await self.wait_until_run_status(run_id=current_run_id, expected_status="stopped", timeout_sec=15)
        #run = await self.get_current_run(print_timing=True)
        delete_run = await self.robot_client.delete_run(run)
        await log_response(delete_run, print_timing=True)
        run = await self.get_current_run(print_timing=True)
        assert run is None
