import io
import json
from pathlib import Path

import httpx
from flask import Flask, render_template, request, send_file
from robot_client import RobotClient
from robot_interactions import RobotInteractions

app = Flask(__name__)

OT2_SERVER = "http://robot-server-ot2"
OT2_PORT = "31952"
FLEX_SERVER = "http://robot-server-flex"
FLEX_PORT = "31951"

CONTAINER_LABWARE = "/var/lib/ot/labware"
CONTAINER_PROTOCOLS_ROOT = "/var/lib/ot/protocols"
CONTAINER_RESULTS = "/var/lib/ot/results"
HOST_LABWARE = Path(os.getcwd(), "labware")
HOST_PROTOCOLS_ROOT = Path(os.getcwd(), "protocols")
HOST_RESULTS = Path(os.getcwd(), "results")

def test_connections():
    message = {"flexStatusCode": 9999, "ot2StatusCode": 9999}
    headers = {"Opentrons-Version": "*"}
    try:
        # Test robot-server-flex
        response_flex = httpx.get(f"{FLEX_SERVER}:{FLEX_PORT}/health", headers=headers)
        message["flexStatusCode"] = response_flex.status_code

        # Test robot-server-ot2
        response_ot2 = httpx.get(f"{OT2_SERVER}:{OT2_PORT}/health", headers=headers)
        message["ot2StatusCode"] = response_ot2.status_code
    except Exception as e:
        print("Error connecting to services:", e)
    return message

async def initial_analyze(protocol,csv=None,labware=None) -> None:
    """Do some stuff with the API client or whatever."""
    async with RobotClient.make(host=FLEX_SERVER, port=FLEX_PORT, version="*") as robot_client:
        robot_interactions = RobotInteractions(robot_client=robot_client)
        if labware:
            raise NotImplementedError("Labware upload not implemented")
        if csv:
            upload = await robot_client.post_data_file(csv)
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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        protocol_file = request.files["protocol_file"]
        csv_file = request.files["csv_file"]

        # Placeholder for processing the files and making API calls
        status = test_connections()
        # use analysis CLI to analyze the protocol and labware files
        # read the analysis
        # if robotType is OT2, send to OT2 server
        # if robotType is Flex, send to Flex server
        # if error, send error message
        # if outcome is success, send success message
        result = {
            "message": "Files processed successfully",
            "protocol_file_name": protocol_file.filename,
            "csv_file_name": csv_file.filename,
            "status": status,
        }

        # Convert the result to a JSON file and send it for download
        json_str = json.dumps(result)
        return send_file(io.BytesIO(json_str.encode()), mimetype="application/json", as_attachment=True, download_name="result.json")
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
