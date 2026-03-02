from enum import Enum, StrEnum, auto
from pynput import keyboard


class Item(StrEnum):
    PHRASE = auto()
    WORD = auto()
    SENTENCE = auto()
    PARAGRAPH = auto()
    ALL = auto()


class DocumentTabs(StrEnum):
    DOCUMENTS = auto()
    SETTINGS = auto()


class EnablePhrases(StrEnum):
    ON = auto()
    OFF = auto()


class Languages(StrEnum):
    ENGLISH_GB = auto()
    ENGLISH_US = auto()
    FRENCH = auto()
    GERMAN = auto()
    SPANISH = auto()
    ITALIAN = auto()


class SaveService(StrEnum):
    EVERNOTE = auto()
    DROPBOX = auto()
    GOOGLE_DRIVE = auto()
    ONEDRIVE = auto()
    ICLOUD = auto()


class FontSize(Enum):
    SMALL = 6
    MEDIUM = 12
    LARGE = 20


ITEMS = {
    "that": Item.PHRASE,
    "this": Item.PHRASE,
    "phrase": Item.PHRASE,
    "word": Item.WORD,
    "sentence": Item.SENTENCE,
    "paragraph": Item.PARAGRAPH,
    "all": Item.ALL,
}


ENABLE_PHRASES = {
    "on": True,
    "off": False,
}


ALPHABET = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

# TODO: add accent modifiers (grave, acute, circumflex, etc.)

NUMBERS_BASIC = {
    "one": 1, 
    "two": 2, 
    "three": 3, 
    "four": 4, 
    "five": 5, 
    "six": 6, 
    "seven": 7, 
    "eight": 8, 
    "nine": 9, 
}

NUMBERS_UNIQUE = {
    "zero": 0, 
    "ten": 10, 
    "eleven": 11, 
    "twelve": 12, 
    "thirteen": 13, 
    "fourteen": 14, 
    "fifteen": 15, 
    "sixteen": 16, 
    "seventeen": 17, 
    "eighteen": 18, 
    "nineteen": 19
}

NUMBERS_COMPOUND_PREFIX = {
    "twenty": 20, 
    "thirty": 30, 
    "forty": 40, 
    "fourty": 40, 
    "fifty": 50, 
    "sixty": 60, 
    "seventy": 70, 
    "eighty": 80, 
    "ninety": 90, 
}

NUMBERS_COMPOUNT_SUFFIX = {
    "hundred": 100, 
    "thousand": 1000, 
    "million": int(1e6), 
    "billion": int(1e9), 
    "trillion": int(1e12), 
    "quadrillion": int(1e15), 
    "quintillion": int(1e18), 
}

NUMBERS = NUMBERS_UNIQUE | NUMBERS_BASIC

KEYS = {
    "escape": keyboard.Key.esc, 
    "control": keyboard.Key.ctrl, 
    "command": keyboard.Key.cmd, 
    "shift": keyboard.Key.shift, 
    "alt": keyboard.Key.alt, 
    "alt grr": keyboard.Key.alt_gr, 
    "space": keyboard.Key.space, 
    "tab": keyboard.Key.tab, 
    "back space": keyboard.Key.backspace, 
    "delete": keyboard.Key.delete, 
    "home": keyboard.Key.home, 
    "end": keyboard.Key.end, 
    "insert": keyboard.Key.insert, 
    "page up": keyboard.Key.page_up, 
    "page down": keyboard.Key.page_down, 
    "caps lock": keyboard.Key.caps_lock, 
    "scroll lock": keyboard.Key.scroll_lock, 
    "numb lock": keyboard.Key.num_lock, 
    "up": keyboard.Key.up, 
    "down": keyboard.Key.down, 
    "left": keyboard.Key.left, 
    "right": keyboard.Key.right, 
    "enter": keyboard.Key.enter, 
    "f one": keyboard.Key.f1, 
    "f two": keyboard.Key.f2, 
    "f three": keyboard.Key.f3, 
    "f four": keyboard.Key.f4, 
    "f five": keyboard.Key.f5, 
    "f six": keyboard.Key.f6, 
    "f seven": keyboard.Key.f7, 
    "f eight": keyboard.Key.f8, 
    "f nine": keyboard.Key.f9, 
    "f ten": keyboard.Key.f10, 
    "f eleven": keyboard.Key.f11, 
    "f twelve": keyboard.Key.f12, 
    "print screen": keyboard.Key.print_screen, 
    "pause": keyboard.Key.pause, 
} | {
    x: keyboard.KeyCode.from_char(x) for x in ALPHABET
}
