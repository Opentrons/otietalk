import asyncio
from pathlib import Path

from rich.console import Console
from rich.theme import Theme
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard


async def stuff(robot_ip: str, robot_port: str) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=f"http://{robot_ip}", port=robot_port, version="*") as robot_client:
        robot_interactions = RobotInteractions(robot_client=robot_client)
        result = await robot_client.get_health()
        await log_response(result, print_timing=True, console=console)
        path_to_csv = Path(Path(__file__).parent, "a.csv")
        upload = await robot_client.post_data_file([path_to_csv])
        data_file_id = upload.json()["data"]["id"]
        variable_name_of_data_file_in_the_protocol = "csv_data"
        protocol_path = Path(Path(__file__).parent, "a.py")
        csv_arg = {variable_name_of_data_file_in_the_protocol: data_file_id}
        console.print(csv_arg)
        protocol_upload = await robot_client.post_protocol(
            files=[protocol_path], run_time_parameter_values={}, run_time_parameter_files=csv_arg
        )
        await log_response(protocol_upload, print_timing=True, console=console)
        protocol_id = protocol_upload.json()["data"]["id"]
        analyses_summaries = protocol_upload.json()["data"]["analysisSummaries"]
        analysis_id = ""
        for analysis_summary in analyses_summaries:
            if analysis_summary["status"] == "pending":
                analysis_id = analysis_summary["id"]
                break
        if analysis_id == "":
            console.print("No pending analyses found")
            if len(analyses_summaries) == 1:
                analysis_id = analyses_summaries[0]["id"]
            else:
                console.print("there are multiple analyses but none are pending")
                console.print("using the last one")
                analysis_id = analyses_summaries[len(analyses_summaries) - 1]["id"]

        await robot_interactions.wait_for_all_analyses_to_complete()
        analysis = await robot_client.get_analysis(protocol_id, analysis_id)
        await log_response(analysis, print_timing=True, console=console)
        analysis2 = await robot_client.get_analysis_as_doc(protocol_id, analysis_id)
        await log_response(analysis2, print_timing=True, console=console)

        protocol_details = await robot_client.get_protocol(protocol_id)
        await log_response(protocol_details, print_timing=True, console=console)

        # pipettes = await robot_client.get_pipettes()
        # await log_response(pipettes)
        # pipettes_offset = await robot_client.get_pipette_offset()
        # await log_response(pipettes_offset)
        # instruments = await robot_client.get_instruments(False)
        # await log_response(instruments)
        # cr = await robot_interactions.get_current_run()
        # await robot_interactions.un_current_run(cr)
        # console.print(cr)
        # all_analyses_complete = await robot_interactions.all_analyses_are_complete()
        # console.print(f"analyses complete? {all_analyses_complete}")
        # protocol = await robot_client.get_protocol("1e858432-d8e0-4daf-94e5-6af848fd0349")
        # await log_response(protocol, console=console)
        # run = await robot_client.get_run("ed5991d5-6a3d-477b-9a2f-ad6e61b1fb17")
        # await log_response(run, console=console)
        # analyses = await robot_client.get_analyses("1e858432-d8e0-4daf-94e5-6af848fd0349")
        # await log_response(analyses, console=console)
        # analysis = await robot_client.get_analysis("1e858432-d8e0-4daf-94e5-6af848fd0349", "31abe15c-fefb-4a13-9ed8-3674783d356c")
        # await log_response(analysis, console=console)
        # ur = await robot_interactions.un_current_run(cr)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    robot_ip = wizard.validate_ip()
    robot_port = wizard.validate_port()
    wizard.reset_log()
    asyncio.run(stuff(robot_ip=robot_ip, robot_port=robot_port))
