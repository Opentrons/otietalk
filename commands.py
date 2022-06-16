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
