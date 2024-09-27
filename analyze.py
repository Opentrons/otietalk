import asyncio
import json
import time
from pathlib import Path

from rich.console import Console
from rich.theme import Theme
from robot_client import RobotClient
from robot_interactions import RobotInteractions
from util import log_response
from wizard import Wizard

# pipenv run python analyze.py

ROBOT_IP = "0.0.0.0"
ROBOT_PORT = "31950"
# Change each run
CSV_FILE = ""
PROTOCOL_FILE = ""
APP_ANALYSIS_FILE = ""
VARIABLE_NAME_OF_DATA_FILE_IN_THE_PROTOCOL = ""
RESULT_ANALYSIS_FILE = f"ProtocolName-full-analysis-{str(int(time.time()))}.json"

# Dry run flag
GO = True


async def analyze() -> None:
    """Analyze"""
    async with RobotClient.make(host=f"http://{ROBOT_IP}", port=ROBOT_PORT, version="*") as robot_client:
        path_to_csv = Path(Path(__file__).parent, CSV_FILE)
        path_to_protocol = Path(Path(__file__).parent, PROTOCOL_FILE)
        path_to_app_analysis = Path(Path(__file__).parent, APP_ANALYSIS_FILE)
        path_to_result_analysis = Path(Path(__file__).parent, RESULT_ANALYSIS_FILE)
        for path in [path_to_csv, path_to_protocol, path_to_app_analysis]:
            if not path.exists():
                console.print(f"File {path} does not exist")
                exit(1)
        robot_interactions = RobotInteractions(robot_client=robot_client)
        result = await robot_client.get_health()
        await log_response(result, print_timing=True, console=console)

        if GO:
            # upload the csv file
            upload = await robot_client.post_data_file([path_to_csv])
            data_file_id = upload.json()["data"]["id"]

            # upload the protocol file
            csv_arg = {VARIABLE_NAME_OF_DATA_FILE_IN_THE_PROTOCOL: data_file_id}
            protocol_upload = await robot_client.post_protocol(
                files=[path_to_protocol], run_time_parameter_values={}, run_time_parameter_files=csv_arg
            )
            await log_response(protocol_upload, print_timing=True, console=console)
            protocol_id = protocol_upload.json()["data"]["id"]

            # understand the analyses
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

            # wait for the analysis to complete
            await robot_interactions.wait_for_all_analyses_to_complete()

            # get the analysis
            analysis_response = await robot_client.get_analysis(protocol_id, analysis_id)
            await log_response(analysis_response, print_timing=True, console=console)
            analysis = analysis_response.json()["data"]

            # read the app analysis file
            try:
                with open(path_to_app_analysis, "r") as f:
                    app_analysis = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

            analysis["createdAt"] = app_analysis["createdAt"]
            analysis["files"] = app_analysis["files"]
            analysis["config"] = app_analysis["config"]
            analysis["metadata"] = app_analysis["metadata"]

            # write the analysis to a file
            with open(path_to_result_analysis, "w") as f:
                json.dump(analysis, f, indent=4)


if __name__ == "__main__":
    custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
    console = Console(theme=custom_theme)
    wizard = Wizard(console)
    wizard.reset_log(True)

    asyncio.run(analyze())
