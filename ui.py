import asyncio
import ipaddress
import os
from logging import PlaceHolder

from rich.console import Console, ConsoleOptions, RenderableType
from rich.json import JSON
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import StyleType
from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.app import App
from textual.layouts.dock import DockLayout
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Button, ButtonPressed, Footer, Header, ScrollView
from textual_extras.widgets import TextInput

from robot_client import RobotClient


def percent(percent, total):
    return int(percent * total / 100)


def is_valid_IPAddress(sample_str):
    """Returns True if given string is a
    valid IP Address, else returns False"""
    result = True
    try:
        ipaddress.ip_network(sample_str)
    except:
        result = False
    return result


class ApiAction(Button):
    def __init__(
        self,
        label: RenderableType,
        name: str | None = None,
        style: StyleType = "white on dark_blue",
    ):
        super().__init__(label, name, style)

    mouse_over = Reactive(False)

    def render(self) -> Panel:
        return Panel(self.label, style=("bold on red" if self.mouse_over else ""))

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False


class MyApp(App):
    """An example of a very simple Textual App"""

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("escape", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:
        """Create and dock the widgets."""
        y = os.get_terminal_size()[1]

        self.body = ScrollView(gutter=1)
        self.input_box = TextInput(
            title=Text("Robot IP"),
            placeholder=Text(
                "Enter your robot IP here like 192.168.50.89 and then press enter",
                style="dim white",
            ),
        )

        self.timing = ScrollView(Text("Timing of last call."))

        self.runs_view = ScrollView(Text("Runs"))

        self.runs = ApiAction(label=Text("Get Runs"), name="runs")

        self.make_run = ApiAction(label=Text("Create Run"), name="runs")
        # get current run
        # get modules
        # uncurrent run
        # load attached left pipette
        # load attached right pipette
        # load tiprack
        # load a module by moduleType
        # load a labware
        # load a labware on a module
        # loadtip
        # home
        # move to well
        #

        # Header / footer / dock
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(
            self.runs_view,
            name="runs_view",
            edge="left",
            size=90,
        )
        await self.view.dock(
            self.input_box,
            size=3,
            name="input_box",
        )
        await self.view.dock(
            self.timing,
            size=2,
            name="timing",
        )

        await self.view.dock(
            self.runs,
            size=3,
            name="runs",
        )
        # Dock the body in the remaining space
        await self.view.dock(self.body, edge="right")

        await self.body.update("Enter IP to see data here.")

        # await self.call_later(get_health)

    # async def _clear_screen(self) -> None:
    #     # clears all the widgets from the screen..and re render them all
    #     # Why? you ask? this was the only way at the time of this writing

    #     if isinstance(self.view.layout, DockLayout):
    #         self.view.layout.docks.clear()
    #     self.view.widgets.clear()

    # async def refresh_screen(self) -> None:
    #     """
    #     Refresh the screen by repainting all the widgets
    #     """

    #     await self._clear_screen()
    #     x, y = os.get_terminal_size()

    async def get_health(self, ip) -> None:
        health = ""
        async with RobotClient.make(host=f"http://{ip}", port=31950, version="*") as robot_client:
            health = await robot_client.get_health()
        json = JSON(health.text)
        await self.body.update(json)
        await self.timing.update(Text(f"Call to {health.request.url}\nelapsed time = {health.elapsed}"))

    async def get_runs(self, ip) -> None:
        health = ""
        async with RobotClient.make(host=f"http://{ip}", port=31950, version="*") as robot_client:
            health = await robot_client.get_runs()
        json = JSON(health.text)
        await self.runs_view.update(json)
        await self.timing.update(Text(f"Call to {health.request.url}\nelapsed time = {health.elapsed}"))

    async def get_ip(self):
        """ """

        value = self.input_box.value.strip()
        if not is_valid_IPAddress(value):
            return False
        return value

    async def on_key(self, event: events.Key):
        if event.key == "enter":
            self.ip = await self.get_ip()
            if self.ip:
                try:
                    await self.get_health(self.ip)
                except Exception as e:
                    await self.body.update(Pretty(e, expand_all=True))

    async def handle_button_pressed(self, message: ButtonPressed) -> None:
        """A message sent by the button widget"""

        assert isinstance(message.sender, Button)
        button_name = message.sender.name
        if button_name == "runs":
            await self.runs_view.update("Getting Runs...")
            try:
                await self.get_runs(self.ip)
            except Exception as e:
                await self.runs_view.update(Pretty(e, expand_all=True))


MyApp.run(title="Robot Viewer", log="textual.log")
