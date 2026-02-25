"""
This module contains Excel-/Google Sheets-specific shortcuts and actions. 
"""

from enum import StrEnum, auto
from whisper_writer.input_simulation import InputSimulator, Key, KeyCode

class CellFormats(StrEnum):
    GENERAL=auto()
    CURRENCY=auto()
    PERCENTAGE=auto()
    SCIENTIFIC=auto()
    DATE=auto()
    TIME=auto()
    NUMBER=auto()


CELL_FORMATS: dict[str, CellFormats] = {
    "general": CellFormats.GENERAL,
    "currency": CellFormats.CURRENCY,
    "percentage": CellFormats.PERCENTAGE,
    "scientific": CellFormats.SCIENTIFIC,
    "date": CellFormats.DATE,
    "time": CellFormats.TIME,
    "number": CellFormats.NUMBER,
}


CELL_FORMAT_KEYS: dict[CellFormats, str] = {
    CellFormats.GENERAL: "~",
    CellFormats.CURRENCY: "4",
    CellFormats.PERCENTAGE: "5",
    CellFormats.SCIENTIFIC: "6",
    CellFormats.DATE: "3",
    CellFormats.TIME: "2",
    CellFormats.NUMBER: "1",
}


CELL = {
    "cell ({letter} )+ {number}": "$1$2"
}


class ExcelUtils:
    def __init__(self, *, input_simulator: InputSimulator):
        self.__input_simulator = input_simulator

    def goto_cell(self, cell_ref: str) -> None:
        self.__input_simulator.simulate_keypress(Key.f5)
        self.__input_simulator.typewrite(cell_ref)
        self.__input_simulator.simulate_keypress(Key.enter)

    def zoom_in(self) -> None:
        self.__input_simulator.simulate_keypress((Key.ctrl, Key.alt, KeyCode.from_char("=")))

    def zoom_out(self) -> None:
        self.__input_simulator.simulate_keypress((Key.ctrl, Key.alt, KeyCode.from_char("-")))

    def set_format(self, cell_format: CellFormats) -> None:
        self.__input_simulator.simulate_keypress((Key.ctrl, Key.shift, KeyCode.from_char(CELL_FORMAT_KEYS[cell_format])))

    def select_row(self) -> None:
        self.__input_simulator.simulate_keypress((Key.shift, Key.space))

    def select_column(self) -> None:
        self.__input_simulator.simulate_keypress((Key.ctrl, Key.space))

    def edit_cell(self, cell_ref: str | None) -> None:
        if cell_ref is not None:
            self.goto_cell(cell_ref)
        
        self.__input_simulator.simulate_keypress(Key.f2)

    def select_cells(self, cell_ref_0: str, cell_ref_1: str) -> None:
        self.goto_cell(cell_ref_0)
        self.__input_simulator.press_and_hold_key(Key.shift)
        self.goto_cell(cell_ref_1)

