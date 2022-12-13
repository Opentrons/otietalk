from opentrons.protocol_api import ProtocolContext

metadata = {
    "apiLevel": "2.6",
    "author": "engineer@opentrons.com",
    "protocolName": "basic_transfer_standalone",
}


def run(protocol: ProtocolContext) -> None:
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 1)
    tiprack_1 = protocol.load_labware("opentrons_96_tiprack_20ul", 2)
    p20 = protocol.load_instrument(instrument_name="p20_single_gen2", mount="right", tip_racks=[tiprack_1])

    p20.pick_up_tip()
    p20.aspirate(18, plate["A1"])
    p20.dispense(17, plate["B1"])
    p20.return_tip()
