from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

import httpx
from httpx import Response

STARTUP_WAIT = 15
SHUTDOWN_WAIT = 15


class RobotClient:
    """Client for the robot's HTTP API.

    This is mostly a thin wrapper, where most methods have a 1:1 correspondence
    with HTTP endpoints. See the robot server's OpenAPI specification for
    details on semantics and request/response shapes.
    """

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        worker_executor: concurrent.futures.ThreadPoolExecutor,
        host: str,
        port: str,
    ) -> None:
        """Initialize the client."""
        self.base_url: str = f"{host}:{port}"
        self.httpx_client: httpx.AsyncClient = httpx_client
        self.worker_executor: concurrent.futures.ThreadPoolExecutor = worker_executor

    @staticmethod
    @contextlib.asynccontextmanager
    async def make(host: str, port: str, version: str) -> AsyncGenerator[RobotClient, None]:
        with concurrent.futures.ThreadPoolExecutor() as worker_executor:
            async with httpx.AsyncClient(headers={"opentrons-version": version}) as httpx_client:
                yield RobotClient(
                    httpx_client=httpx_client,
                    worker_executor=worker_executor,
                    host=host,
                    port=port,
                )

    async def alive(self) -> bool:
        """Are /health and /openapi.json both reachable?"""
        try:
            await self.get_health()
            await self.get_openapi()
            return True
        except (httpx.ConnectError, httpx.HTTPStatusError):
            return False

    async def dead(self) -> bool:
        """Are /health and /openapi.json both unreachable?"""
        try:
            await self.get_health()
            return False
        except httpx.HTTPStatusError:
            return False
        except httpx.ConnectError:
            pass
        try:
            await self.get_openapi()
            return False
        except httpx.HTTPStatusError:
            return False
        except httpx.ConnectError:
            # Now both /health and /openapi.json have returned ConnectError.
            return True

    async def _poll_for_alive(self) -> None:
        """Retry the /health and /openapi.json until both reachable."""
        while not await self.alive():
            # Avoid spamming the server in case a request immediately
            # returns some kind of "not ready."
            await asyncio.sleep(0.1)

    async def _poll_for_dead(self) -> None:
        """Poll the /health and /openapi.json until both unreachable."""
        while not await self.dead():
            # Avoid spamming the server in case a request immediately
            # returns some kind of "not ready."
            await asyncio.sleep(0.1)

    async def wait_until_alive(self, timeout_sec: float = STARTUP_WAIT) -> bool:
        try:
            await asyncio.wait_for(self._poll_for_alive(), timeout=timeout_sec)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_until_dead(self, timeout_sec: float = SHUTDOWN_WAIT) -> bool:
        """Retry the /health and /openapi.json until both unreachable."""
        try:
            await asyncio.wait_for(self._poll_for_dead(), timeout=timeout_sec)
            return True
        except asyncio.TimeoutError:
            return False

    async def get_health(self) -> Response:
        """GET /health."""
        response = await self.httpx_client.get(url=f"{self.base_url}/health", timeout=60)
        # response.raise_for_status()
        return response

    async def get_openapi(self) -> Response:
        """GET /openapi.json."""
        response = await self.httpx_client.get(url=f"{self.base_url}/openapi.json")
        response.raise_for_status()
        return response

    async def get_protocols(self) -> Response:
        """GET /protocols."""
        response = await self.httpx_client.get(url=f"{self.base_url}/protocols", timeout=180)
        response.raise_for_status()
        return response

    async def get_protocol(self, protocol_id: str) -> Response:
        """GET /protocols/{protocol_id}."""
        response = await self.httpx_client.get(url=f"{self.base_url}/protocols/{protocol_id}", timeout=60)
        return response

    async def post_data_file(self, files: List[Path] | bytes) -> Response:
        file_payload = []
        if isinstance(files, bytes):
            file_payload.append(("file", files))
        else:
            for file in files:
                file_payload.append(("file", open(file, "rb")))
        response = await self.httpx_client.post(url=f"{self.base_url}/dataFiles", files=file_payload, timeout=120)
        return response

    async def post_protocol(
        self, files: List[Path] | bytes, labware_files=None, run_time_parameter_values=None, run_time_parameter_files=None
    ) -> Response:
        """POST /protocols."""
        if run_time_parameter_files is None:
            run_time_parameter_files = {}
        if run_time_parameter_values is None:
            run_time_parameter_values = {}
        file_payload = []
        if isinstance(files, bytes):
            file_payload.append(("files", files))
        else:
            for file in files:
                file_payload.append(("files", open(file, "rb")))
        if labware_files is not None:
            raise NotImplementedError("Labware files are not yet supported")
        # Include the form fields (JSON data) as strings
        file_payload.append(
            (
                "runTimeParameterValues",
                (None, json.dumps(run_time_parameter_values), "application/json"),
            )
        )
        file_payload.append(
            (
                "runTimeParameterFiles",
                (None, json.dumps(run_time_parameter_files), "application/json"),
            )
        )
        file_payload.append(("protocolKind", (None, "standard")))
        response = await self.httpx_client.post(url=f"{self.base_url}/protocols", files=file_payload, timeout=120)
        response.raise_for_status()
        return response

    async def post_simple_command(
        self,
        req_body: Dict[str, object],
        params: Dict[str, Any],
        timeout_sec: float = 30.0,
    ) -> Response:
        """POST /commands."""
        response = await self.httpx_client.post(
            url=f"{self.base_url}/commands",
            json=req_body,
            params=params,
            timeout=timeout_sec,
        )
        # response.raise_for_status()
        return response

    async def get_runs(self) -> Response:
        """GET /runs."""
        response = await self.httpx_client.get(url=f"{self.base_url}/runs")
        response.raise_for_status()
        return response

    async def post_run(self, req_body: Dict[str, object]) -> Response:
        """POST /runs."""
        response = await self.httpx_client.post(url=f"{self.base_url}/runs", json=req_body, timeout=15)
        return response

    async def patch_run(self, run_id: str, req_body: Dict[str, object]) -> Response:
        """POST /runs."""
        response = await self.httpx_client.patch(url=f"{self.base_url}/runs/{run_id}", json=req_body, timeout=15)
        response.raise_for_status()
        return response

    async def get_run(self, run_id: str) -> Response:
        """GET /runs/:run_id."""
        response = await self.httpx_client.get(url=f"{self.base_url}/runs/{run_id}", timeout=15)
        response.raise_for_status()
        return response

    async def post_run_command(
        self,
        run_id: str,
        req_body: Dict[str, object],
        params: Dict[str, Any],
        timeout_sec: float = 30.0,
    ) -> Response:
        """POST /runs/:run_id/commands."""
        response = await self.httpx_client.post(
            url=f"{self.base_url}/runs/{run_id}/commands",
            json=req_body,
            params=params,
            timeout=timeout_sec,
        )
        # response.raise_for_status()
        return response

    async def get_run_commands(self, run_id: str) -> Response:
        """GET /runs/:run_id/commands."""
        response = await self.httpx_client.get(url=f"{self.base_url}/runs/{run_id}/commands", params={"pageLength": 300})
        response.raise_for_status()
        return response

    async def get_run_command(self, run_id: str, command_id: str) -> Response:
        """GET /runs/:run_id/commands/:command_id."""
        response = await self.httpx_client.get(url=f"{self.base_url}/runs/{run_id}/commands/{command_id}")
        response.raise_for_status()
        return response

    async def post_labware_offset(
        self,
        run_id: str,
        req_body: Dict[str, object],
    ) -> Response:
        """POST /runs/:run_id/labware_offsets."""
        response = await self.httpx_client.post(
            url=f"{self.base_url}/runs/{run_id}/labware_offsets",
            json=req_body,
        )
        response.raise_for_status()
        return response

    async def post_run_action(
        self,
        run_id: str,
        req_body: Dict[str, object],
    ) -> Response:
        """POST /runs/:run_id/commands."""
        response = await self.httpx_client.post(url=f"{self.base_url}/runs/{run_id}/actions", json=req_body, timeout=15)
        response.raise_for_status()
        return response

    async def get_analysis(self, protocol_id: str, analysis_id: str) -> Response:
        """GET /protocols/{protocol_id}/{analysis_id}."""
        response = await self.httpx_client.get(url=f"{self.base_url}/protocols/{protocol_id}/analyses/{analysis_id}", timeout=6000)
        response.raise_for_status()
        return response

    async def get_analysis_as_doc(self, protocol_id: str, analysis_id: str) -> Response:
        """GET /protocols/{protocol_id}/{analysis_id}."""
        response = await self.httpx_client.get(
            url=f"{self.base_url}/protocols/{protocol_id}/analyses/{analysis_id}/asDocument", timeout=6000
        )
        response.raise_for_status()
        return response

    async def get_analyses(self, protocol_id: str) -> Response:
        """GET /protocols/{protocol_id}/{analysis_id}."""
        response = await self.httpx_client.get(url=f"{self.base_url}/protocols/{protocol_id}/analyses", timeout=60)
        response.raise_for_status()
        return response

    async def delete_run(self, run_id: str) -> Response:
        """DELETE /runs/{run_id}."""
        response = await self.httpx_client.delete(f"{self.base_url}/runs/{run_id}", timeout=15)
        response.raise_for_status()
        return response

    async def post_setting_reset_options(
        self,
        req_body: Dict[str, bool],
    ) -> Response:
        """POST /settings/reset."""
        response = await self.httpx_client.post(
            url=f"{self.base_url}/settings/reset",
            json=req_body,
        )
        response.raise_for_status()
        return response

    async def get_settings(
        self,
    ) -> Response:
        """GET /settings"""
        response = await self.httpx_client.get(
            url=f"{self.base_url}/settings",
        )
        response.raise_for_status()
        return response

    async def post_setting(
        self,
        id: str,
        value: bool | int | str,
    ) -> Response:
        """POST /settings/reset."""
        response = await self.httpx_client.post(
            url=f"{self.base_url}/settings",
            json={"id": id, "value": value},
        )
        response.raise_for_status()
        return response

    async def get_modules(self) -> Response:
        """GET /modules."""
        response = await self.httpx_client.get(url=f"{self.base_url}/modules", timeout=15)
        response.raise_for_status()
        return response

    async def get_pipettes(self) -> Response:
        """GET /pipettes."""
        response = await self.httpx_client.get(url=f"{self.base_url}/pipettes")
        response.raise_for_status()
        return response

    async def get_instruments(self, refresh=False) -> Response:
        """GET /instruments.
        If refresh=True, actively scan for attached pipettes. Note: this requires disabling the pipette motors
        and should only be done when no protocol is running and you know it won't cause a problem.
        """
        response = await self.httpx_client.get(url=f"{self.base_url}/instruments", params={"refresh": refresh})
        response.raise_for_status()
        return response

    async def get_pipette_offset(self) -> Response:
        """GET /calibrations/pipette_offset"""
        response = await self.httpx_client.get(url=f"{self.base_url}/calibration/status")
        response.raise_for_status()
        return response
