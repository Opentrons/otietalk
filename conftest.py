import pytest
import pytest_asyncio
from _pytest.config.argparsing import Parser
from rich.console import Console

from robot_client import RobotClient


def pytest_addoption(parser: Parser) -> None:
    """Add options to the command line parser."""
    parser.addoption("--robot_ip", action="store", default="192.168.50.89", help="specify robot ip like 192.168.50.89")
    parser.addoption("--robot_port", action="store", default="31950", help="specify robot port like 31950")


@pytest_asyncio.fixture
async def robot_client(request: pytest.FixtureRequest) -> RobotClient:
    robot_ip = request.config.getoption("--robot_ip")
    robot_port = request.config.getoption("--robot_port")
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as client:
        yield client


@pytest.fixture()
def console() -> Console:
    return Console(log_time=True)
