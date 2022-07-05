from typing import Optional


def load_module_command(model: str, slot_name: str, module_id: str):
    return {
        "data": {
            "commandType": "loadModule",
            "params": {
                "model": model,
                "location": {"slotName": slot_name},
                "moduleId": module_id,
            },
        }
    }


def open_latch_command(hs_id: str):
    return {
        "data": {
            "commandType": "heaterShaker/openLabwareLatch",
            "params": {
                "moduleId": hs_id,
            },
        }
    }


def close_latch_command(hs_id: str):
    return {
        "data": {
            "commandType": "heaterShaker/closeLabwareLatch",
            "params": {
                "moduleId": hs_id,
            },
        }
    }


def set_target_shake_speed_command(hs_id: str, rpm: int):
    return {
        "data": {
            "commandType": "heaterShaker/setAndWaitForShakeSpeed",
            "params": {
                "moduleId": hs_id,
                "rpm": rpm,
            },
        }
    }


def stop_shake_command(hs_id: str):
    return {
        "data": {
            "commandType": "heaterShaker/deactivateShaker",
            "params": {
                "moduleId": hs_id,
            },
        }
    }


def set_target_temp_command(hs_id: str, celsius: float):
    """not blocking"""
    return {
        "data": {
            "commandType": "heaterShaker/setTargetTemperature",
            "params": {
                "moduleId": hs_id,
                "celsius": celsius,
            },
        }
    }


def wait_for_temp_command(hs_id: str, celsius: float):
    "blocking"
    return {
        "data": {
            "commandType": "heaterShaker/waitForTemperature",
            "params": {
                "moduleId": hs_id,
                "celsius": celsius,
            },
        }
    }


def deactivate_heater_command(hs_id: str):
    return {
        "data": {
            "commandType": "heaterShaker/deactivateHeater",
            "params": {
                "moduleId": hs_id,
            },
        }
    }


def load_labware_command(
    deck_slot_name: str,  # TODO: Also support modules.
    load_name: str,
    namespace: str,
    version: int,
    labware_id: Optional[str] = None,
    display_name: Optional[str] = None,
):
    return {
        "data": {
            "commandType": "loadLabware",
            "params": {
                "location": {"slotName": deck_slot_name},
                "loadName": load_name,
                "namespace": namespace,
                "version": version,
                "labwareId": labware_id,
                "displayName": display_name,
            },
        }
    }


def load_pipette_command(
    pipette_name: str,
    mount: str,
    pipette_id: Optional[str] = None,
):
    return {
        "data": {
            "commandType": "loadPipette",
            "params": {
                "pipetteName": pipette_name,
                "mount": mount,
                "pipetteId": pipette_id,
            },
        }
    }


def pick_up_tip_command(
    pipette_id: str,
    labware_id: str,
    well_name: str,
    # TODO: Support wellLocation also.
):
    return {
        "data": {
            "commandType": "pickUpTip",
            "params": {
                "pipetteId": pipette_id,
                "labwareId": labware_id,
                "wellName": well_name,
            },
        }
    }


def drop_tip_command(
    pipette_id: str,
    labware_id: str,
    well_name: str,
    # TODO: Add wellLocation parameter.
):
    return {
        "data": {
            "commandType": "dropTip",
            "params": {
                "pipetteId": pipette_id,
                "labwareId": labware_id,
                "wellName": well_name,
            },
        }
    }


def move_to_coordinates_command(
    pipette_id: str,
    x: float,
    y: float,
    z: float,
    minimum_z_height: Optional[float] = None,
    force_direct: Optional[bool] = None,
):
    body = {
        "data": {
            "commandType": "moveToCoordinates",
            "params": {
                "pipetteId": pipette_id,
                "coordinates": {
                    "x": x,
                    "y": y,
                    "z": z,
                },
            },
        }
    }
    if minimum_z_height is not None:
        body["data"]["params"]["minimumZHeight"] = minimum_z_height
    if force_direct is not None:
        body["data"]["params"]["forceDirect"] = force_direct

    return body


def home_command():  # TODO: Add axes parameter.
    return {"data": {"commandType": "home", "params": {}}}
