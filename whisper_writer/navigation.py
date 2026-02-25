from typing import Optional
from pynput.keyboard import Key
import pyperclip

from whisper_writer.input_simulation import InputSimulator
from whisper_writer.locating import ItemLocations, ItemRelativeLocations, LocationInterpreter
from whisper_writer.special_phrases.objects import Item
from whisper_writer.text_buffer import TextBuffer


class Navigator:
    def __init__(self, *, input_simulator: InputSimulator, text_buffer: TextBuffer) -> None:
        self.__input_simulator = input_simulator
        self.__location_interpreter = LocationInterpreter(text_buffer=text_buffer)

    def select(self, loc: ItemLocations, item: Item) -> None:
        self.__location_interpreter.move_cursor_to(rel_loc=ItemRelativeLocations.START_OF, loc=loc, item=item)
        self.__input_simulator.press_and_hold_key(Key.shift)
        self.__location_interpreter.move_cursor_to(rel_loc=ItemRelativeLocations.END_OF, loc=loc, item=item)

    def move_cursor_to(self, rel_loc: Optional[ItemRelativeLocations], loc: ItemLocations, item: Item, index: Optional[int] = None) -> None:
        self.__location_interpreter.move_cursor_to(rel_loc=rel_loc, loc=loc, item=item, index=index)

    def copy_item(self, loc: ItemLocations, item: Item) -> None:
        self.select(loc=loc, item=item)
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)

    def copy_all(self) -> None:
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.SELECT_ALL)
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)

    def get_selected_item(self) -> str:
        old_clipboard = pyperclip.paste()
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)
        selected_text = pyperclip.paste()
        pyperclip.copy(old_clipboard)
        return selected_text
