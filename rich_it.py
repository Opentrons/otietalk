import json
import time

from rich.console import Console

your_garbage = """
tavern.util.exceptions.KeyMismatchError: Structure of returned data was different than expected  - Extra keys in response: {'commandType', 'createdAt', 'key', 'startedAt', 'completedAt', 'params', 'result', 'status'} (expected["data"]["0"]["commands"]["11"] = '{'id': <tavern.util.loader.StrSentinel object at 0x1296d5590>}' (type = <class 'dict'>), actual["data"]["0"]["commands"]["11"] = '{'id': '778cc963-1b3f-4fad-9afd-8383b21a7f21', 'createdAt': '2022-06-09T19:26:20.627801+00:00', 'commandType': 'blowout', 'key': '778cc963-1b3f-4fad-9afd-8383b21a7f21', 'status': 'succeeded', 'params': {'pipetteId': 'pipetteId', 'labwareId': 'destPlateId', 'wellName': 'B1', 'wellLocation': {'origin': 'bottom', 'offset': {'x': 0.0, 'y': 0.0, 'z': 12.0}}}, 'result': {}, 'startedAt': '2022-06-09T19:26:20.737766+00:00', 'completedAt': '2022-06-09T19:26:20.740554+00:00'}' (type = <class 'dict'>))
"""

with open("pretty.log", "wt") as log:
    console = Console(file=log, width=120)
    console.rule(f"Report Generated {time.time()}")
    try:
        json = json.loads(your_garbage)
    except Exception:
        console.print_exception()
        console.print("Python cant parse a json so just printing")
        console.print(your_garbage)
    console.print(json)
