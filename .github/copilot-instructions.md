# otietalk Copilot Instructions

## Architecture & Responsibilities
- `clients/robot_client.py` is the only HTTP surface: every robot endpoint has a dedicated async wrapper; add new endpoints here before using them elsewhere.
- `clients/robot_interactions.py` layers orchestration (run lifecycle, module helpers, timing) on top of the client—reuse it for anything that needs `waitUntilComplete`, retries, or run management instead of reimplementing polling.
- `interactions/commands.py` centralizes command payload builders; extend it when new commandTypes are needed so scripts/tests stay declarative.
- Utility building blocks live in `util/` (logging, prompts, timing) and `wizard/` (ip/port validation, log reset). Prefer these helpers over ad-hoc IO to match existing UX.

## Developer Workflows
- Bootstrap with `make setup` (installs dependencies via uv and prepares the managed .venv). Always invoke scripts/tests with `uv run …` (for example `uv run python interactions/hs_commands.py`).
- Every script expects `ROBOT_IP`/`ROBOT_PORT`; `Wizard.validate_*` can pull from env vars and keeps prompting until valid.
- Logs for robot responses append to `responses.log`; call `Wizard.reset_log()` or delete manually before long runs to keep noise down.
- Async scripts should wrap robot access with `async with RobotClient.make(host=f"http://{ip}", port=port, version="*")` so the shared `httpx.AsyncClient` and worker threadpool are configured consistently.

## Patterns Worth Mirroring
- `RobotInteractions.execute_command()` automatically adds `waitUntilComplete` timeouts and rich panels; call it instead of hitting `/runs/{id}/commands` manually unless you truly need raw responses.
- If a run already exists, use `RobotInteractions.force_create_new_run()`—it stops/deletes the current run before posting a new one, matching how tests stay in a known state.
- When adding CLI utilities, inherit from `freeze/base_cli.BaseCli` to get the standard `--robot_ip/--robot_port` flags and help text.
- Concurrency stress tests rely on `anyio.create_task_group()` (see `freeze/freeze.py`); follow that pattern if you need simultaneous telemetry + command traffic.
- `util.log_response()` is the agreed logging format (status, elapsed, JSON). Call it whenever you hit the API directly so investigators can diff behavior via `responses.log`.

## Key Feature Areas
- Heater-Shaker workflows live in `interactions/hs_*` and are validated by `tests/hs_test.py`; they expect the module to be physically attached (slot 1) and enforce latch/temperature invariants.
- Thermocycler flows mirror that setup via `tests/tc_test.py`, with helpers like `starting_state()` ensuring lid/block states before issuing commands.
- Motion experiments (`moveto/move_to_coordinates.py`, `moveto/OT3_move_to_coordinates.py`) show how to compose pipette + movement commands; reuse those sequences when troubleshooting deck coordinates.
- Protocol analysis tooling (`interactions/analyze.py`) demonstrates uploading CSVs with `RobotClient.post_data_file()` and mapping runtime parameter IDs—consult it when dealing with runTimeParameterValues/files.
- `robot_discovery/robots.py` uses Zeroconf + periodic `/networking/status` polling to find robots on the LAN; keep its polling/backoff behavior if extending discovery features.

## External Integrations & Ops
- SSH utilities in `ssh/ssh.py` assume an RSA key at `results/key` and wrap `paramiko` + `scp` for downloading `/data` or replacing `/data/opentrons_robot_server`; dont bypass the progress callbacks if you need user feedback.
- Hardware-facing tests run with `uv run pytest --robot_ip <addr> --robot_port <port>`; they are all `asyncio` tests, so keep new fixtures async and rely on the existing `robot_client` fixture for connectivity.
- Formatting & linting rely on Ruff (140-char line limit, ignore E722) and strict mypy; new modules should type-hint command payloads (see `TypedDict` usage in `interactions/commands.py`).
