"""
This module implements the item locator class, 
which finds words, phrases, sentences, and paragraphs in the text. 
Each function finds the specified item in the text, 
and returns the index of the start and the end of the item in the buffer. 
"""


from enum import StrEnum, auto
from typing import Optional

from whisper_writer.special_phrases.objects import Item
from whisper_writer.text_buffer import TextBuffer


class GlobalLocations(StrEnum):
    START = auto()
    END = auto()
    TITLE = auto()
    BODY = auto()


class ItemLocations(StrEnum):
    PREVIOUS = auto()
    NEXT = auto()
    FIRST = auto()
    LAST = auto()


class ItemRelativeLocations(StrEnum):
    START_OF = auto()
    END_OF = auto()


LOCATING_PHRASES = {
    "that": ItemLocations.PREVIOUS,
    "this": ItemLocations.PREVIOUS,
    "previous": ItemLocations.PREVIOUS,
    "next": ItemLocations.NEXT,
    "first": ItemLocations.FIRST,
    "last": ItemLocations.LAST,
}


GLOBAL_LOCATING_PHRASES = {
    "beginning": GlobalLocations.START,
    "start": GlobalLocations.START,
    "end": GlobalLocations.END,
    "title": GlobalLocations.TITLE,
    "dictation": GlobalLocations.BODY,
}


RELATIVE_LOCATING_PHRASES = {
    "start of": ItemRelativeLocations.START_OF,
    "beginning of": ItemRelativeLocations.START_OF,
    "end of": ItemRelativeLocations.END_OF,
    "before": ItemRelativeLocations.START_OF,
    "after": ItemRelativeLocations.END_OF,
}


SENTENCE_TERMINATION_CHARACTERS = frozenset(".?!")
WHITESPACE_CHARACTERS = frozenset(" \t")

class ItemLocator:

    def find_next_char_from_set(self, text: str, chars: frozenset[str], start_index: int = 0) -> int:
        return next((i for i,c in enumerate(text[start_index:]) if c in chars), -1)

    def find_previous_char_from_set(self, text: str, chars: frozenset[str], start_index: int = -1) -> int:
        if start_index < 0:
            start_index += len(text)

        for i in range(start_index, 0, -1):
            if text[i] in chars:
                return i
            
        return 0


    def find_previous_word(self, text: str, index: int = -1) -> tuple[int, int]:
        end_index = self.find_previous_char_from_set(text, WHITESPACE_CHARACTERS, index)
        start_index = self.find_previous_char_from_set(text, WHITESPACE_CHARACTERS, end_index - 1)
        return start_index, end_index

    def find_next_word(self, text: str, index: int = 0) -> tuple[int, int]:
        start_index = self.find_next_char_from_set(text, WHITESPACE_CHARACTERS, index)
        end_index = self.find_next_char_from_set(text, WHITESPACE_CHARACTERS, start_index + 1)
        return start_index, end_index

    def find_previous_sentence(self, text: str, index: int = -1) -> tuple[int, int]:
        end_index = self.find_previous_char_from_set(text, SENTENCE_TERMINATION_CHARACTERS, index)
        start_index = self.find_previous_char_from_set(text, SENTENCE_TERMINATION_CHARACTERS, end_index - 1)
        return start_index, end_index

    def find_next_sentence(self, text: str, index: int = 0) -> tuple[int, int]:
        start_index = self.find_next_char_from_set(text, SENTENCE_TERMINATION_CHARACTERS, index)
        end_index = self.find_next_char_from_set(text, SENTENCE_TERMINATION_CHARACTERS, start_index + 1)
        return start_index, end_index

    def find_previous_paragraph(self, text: str, index: int = -1) -> tuple[int, int]:
        try:
            end_index = text.rindex("\n\n", index)
        except ValueError:
            return 0, 0

        try:
            start_index = text.rindex("\n\n", end_index - 1)
        except ValueError:
            return 0, end_index

        return start_index, end_index

    def find_next_paragraph(self, text: str, index: int = -1) -> tuple[int, int]:
        text_len = len(text)
        try:
            start_index = text.index("\n\n", index)
        except ValueError:
            return text_len - 1, text_len - 1

        try:
            end_index = text.index("\n\n", start_index + 2)
        except ValueError:
            return start_index, text_len - 1

        return start_index, end_index


class LocationInterpreter:
    def __init__(self, text_buffer: TextBuffer) -> None:
        self.__text_buffer = text_buffer
        self.__item_locator = ItemLocator()

    def find(self, rel_loc: ItemRelativeLocations | None, loc: ItemLocations, item: Item, index: Optional[int] = None) -> int:

        # Default values
        if rel_loc is None:
            rel_loc = ItemRelativeLocations.START_OF

        # Get current cursor location
        if index is None:
            index = self.__text_buffer.get_cursor_loc()

        start_index, end_index = index, index
        match loc:
            case ItemLocations.PREVIOUS:
                match item:
                    case Item.WORD: start_index, end_index = self.__item_locator.find_previous_word(self.__text_buffer.get_text(), index)
                    case Item.SENTENCE: start_index, end_index = self.__item_locator.find_previous_sentence(self.__text_buffer.get_text(), index)
                    case Item.PARAGRAPH: start_index, end_index = self.__item_locator.find_previous_paragraph(self.__text_buffer.get_text(), index)
            case ItemLocations.NEXT:
                match item:
                    case Item.WORD: start_index, end_index = self.__item_locator.find_next_word(self.__text_buffer.get_text(), index)
                    case Item.SENTENCE: start_index, end_index = self.__item_locator.find_next_sentence(self.__text_buffer.get_text(), index)
                    case Item.PARAGRAPH: start_index, end_index = self.__item_locator.find_next_paragraph(self.__text_buffer.get_text(), index)
            case ItemLocations.FIRST:
                match item:
                    case Item.WORD: start_index, end_index = self.__item_locator.find_next_word(self.__text_buffer.get_text(), 0)
                    case Item.SENTENCE: start_index, end_index = self.__item_locator.find_next_sentence(self.__text_buffer.get_text(), 0)
                    case Item.PARAGRAPH: start_index, end_index = self.__item_locator.find_next_paragraph(self.__text_buffer.get_text(), 0)
            case ItemLocations.LAST:
                match item:
                    case Item.WORD: start_index, end_index = self.__item_locator.find_previous_word(self.__text_buffer.get_text(), -1)
                    case Item.SENTENCE: start_index, end_index = self.__item_locator.find_previous_word(self.__text_buffer.get_text(), -1)
                    case Item.PARAGRAPH: start_index, end_index = self.__item_locator.find_previous_word(self.__text_buffer.get_text(), -1)


        if rel_loc == ItemRelativeLocations.START_OF:
            return start_index
        else:
            return end_index


    def move_cursor_to(self, rel_loc: ItemRelativeLocations | None, loc: ItemLocations, item: Item, index: Optional[int] = None) -> None:
        self.__text_buffer.move_cursor_to(self.find(rel_loc, loc, item, index))

    # def select(self, )