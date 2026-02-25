from enum import StrEnum, auto
from pynput.keyboard import Key, KeyCode

from whisper_writer.input_simulation import InputSimulator
from whisper_writer.navigation import Navigator


class FormattingOptions(StrEnum):
    CLEAR_FORMATTING = auto() # Combine word and libreoffice shortcut (ctrl+space & ctrl+m)
    BOLD = auto()
    ITALICS = auto()
    UNDERLINE = auto()
    STRIKETHROUGH = auto() # No direct keyboard shortcut
    TITLE = auto()
    SUBTITLE = auto()
    HEADING_1 = auto()
    HEADING_2 = auto()
    HEADING_3 = auto()
    HEADING_4 = auto()
    HEADING_5 = auto()
    LEFT_ALIGN = auto()
    CENTRE_ALIGN = auto()
    RIGHT_ALIGN = auto()
    JUSTIFY = auto()
    DECREASE_FONT_SIZE = auto()
    INCREASE_FONT_SIZE = auto()


FORMATTING_KEY_CHORDS: dict[FormattingOptions, tuple[Key | KeyCode, ...]] = {
    FormattingOptions.CLEAR_FORMATTING: (Key.ctrl, Key.space, KeyCode.from_char("m")), # Combine word and libreoffice shortcut (ctrl+space & ctrl+m)
    FormattingOptions.BOLD: (Key.ctrl, KeyCode.from_char('b')),
    FormattingOptions.ITALICS: (Key.ctrl, KeyCode.from_char('i')),
    FormattingOptions.UNDERLINE: (Key.ctrl, KeyCode.from_char('u')),
    FormattingOptions.DECREASE_FONT_SIZE: (Key.ctrl, Key.shift, KeyCode.from_char('<')),
    FormattingOptions.INCREASE_FONT_SIZE: (Key.ctrl, Key.shift, KeyCode.from_char('>')),
    FormattingOptions.LEFT_ALIGN: (Key.ctrl, KeyCode.from_char('l')),
    FormattingOptions.CENTRE_ALIGN: (Key.ctrl, KeyCode.from_char('e')),
    FormattingOptions.RIGHT_ALIGN: (Key.ctrl, KeyCode.from_char('r')),
    FormattingOptions.JUSTIFY: (Key.ctrl, KeyCode.from_char('j')),
}


class Formatter:

    def __init__(self, *, input_simulator: InputSimulator, navigator: Navigator) -> None:
        self.__input_simulator = input_simulator
        self.__navigator = navigator

    def cap(self, word: str) -> str:
        return word[0].upper() + word[1:]

    def all_cap(self, string: str) -> str:
        return string.upper()

    def write_with_formatting(self, string: str, formatting: FormattingOptions) -> None:
        self.__input_simulator.simulate_keypress(FORMATTING_KEY_CHORDS[formatting])
        self.__input_simulator.typewrite(string)
        self.__input_simulator.simulate_keypress(FORMATTING_KEY_CHORDS[formatting])

    def apply_formatting(self, formatting: FormattingOptions) -> None:
        string = self.__navigator.get_selected_item()
        self.write_with_formatting(string, formatting)

    def bold(self, string: str) -> None:
        self.write_with_formatting(string, FormattingOptions.BOLD)

    def italics(self, string: str) -> None:
        self.write_with_formatting(string, FormattingOptions.ITALICS)

    def underline(self, string: str) -> None:
        self.write_with_formatting(string, FormattingOptions.UNDERLINE)
