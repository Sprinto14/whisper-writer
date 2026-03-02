from dataclasses import dataclass
import re
from typing import Any, Callable, Iterable, Optional

from whisper_writer.excel_inputs import CELL_FORMATS
from whisper_writer.locating import LOCATING_PHRASES
from whisper_writer.special_phrases.objects import ITEMS, KEYS, NUMBERS


fdbg = open("debug.out", "w")

# Regex match groups
def generate_regex_group(x: Iterable[str]) -> str:
    return "(" + "|".join(x) + ")"


STRENUM_GROUPS: dict[str, Any] = {
    "{item}": ITEMS,
    "{loc}": LOCATING_PHRASES,
    "{key}": KEYS,
    "{number}": NUMBERS,
    "{letter}": "[a-zA-Z]",
    "{cell_ref}": {"({letter} )+ {number}": "cell_ref"},
    "{cell_format}": CELL_FORMATS,
    "{word}": {r"\w+": "word"},
    "{phrase}": {r"\w+(?:\s(?:\w+))+": "phrase"}
}


REGEX_GROUPS = {k: generate_regex_group(v) for k,v in STRENUM_GROUPS.items()}
REGEX_GROUPS_PATTERN = "|".join(STRENUM_GROUPS.keys())


@dataclass
class CommandMatch:
    text: str
    start_index: int
    end_index: int
    func: Callable[..., Optional[str]]
    args: tuple[Any, ...]
    space_before: bool
    space_after: bool
    end_of_sentence: bool


class SpecialPhrase:
    """
    A single special phrase, which is either replaced by a special character, or triggers an action different from simply typing to the screen. 
    """

    def __init__(self, phrase: str, func: Callable[..., str | None], space_before: bool = True, space_after: bool = True, end_of_sentence: bool = False) -> None:
        self.phrase = phrase
        self.func = func
        self.space_before = space_before
        self.space_after = space_after
        self.end_of_sentence = end_of_sentence
        self.re_pattern = self.generate_regex_phrase(phrase)
        self.re_groups = self.find_regex_groups(phrase)

    def find_regex_groups(self, phrase: str) -> tuple[dict[str, Any], ...]:
        match = re.findall(REGEX_GROUPS_PATTERN, phrase)
        return tuple(STRENUM_GROUPS[m] for m in match) if match else ()

    def generate_regex_phrase(self, phrase: str) -> str:
        phrase = phrase.replace(r"? ", r"? ?") # Fix double spaces around optional arguments
        for keystr, regroup in REGEX_GROUPS.items():
            phrase = phrase.replace(keystr, regroup)

        return r"\b" + phrase + r"\b"

    def match_whole_phrase(self, phrase: str) -> tuple[Any, ...] | None:
        """
        Attempt to match the whole given phrase against the given SpecialPhrase.
        If there is a match, then return a tuple of the converted parameters based on the types defined in the SpecialPhrase.re_groups.
        If a parameter cannot be converted, then the matched string is returned instead (allowing for word captures).
        """
        match = re.fullmatch(self.re_pattern, phrase.lower())
        return tuple(group_type.get(m, phrase[match.start(i):match.end(i)]) for i, (m, group_type) in enumerate(zip(match.groups(), self.re_groups), 1)) if match else None

    def match_inline_command(self, phrase: str) -> tuple[CommandMatch, ...] | None:
        """
        Attempt to match the given phrase against the given SpecialPhrase. This can match multiple times. 
        If there is a match, then return a tuple of the converted parameters based on the types defined in the SpecialPhrase.re_groups for each match (resulting in a tuple of tuples).
        If a parameter cannot be converted, then the matched string is returned instead (allowing for word captures).
        """
        matches = re.finditer(self.re_pattern, phrase.lower())
        result = tuple(
            CommandMatch(
                text=match.group(0),
                start_index=match.start(0),
                end_index=match.end(0),
                func=self.func,
                args=tuple(group_type.get(m, phrase[match.start(i):match.end(i)]) for i, (m, group_type) in enumerate(zip(match.groups(), self.re_groups), 1)),
                space_before=self.space_before,
                space_after=self.space_after,
                end_of_sentence=self.end_of_sentence,
            )
            for match in matches if match
        )

        if len(result) == 0:
            return None
        else:
            return result


    def call(self, args: tuple[Any]) -> str:
        """
        Call the function for the special phrase given a set of arguments. This should return a string (for inline commands) or None (for standalone commands).
        For ease of use, both are converted to strings (None -> "").
        """
        result = self.func(*args)
        if not isinstance(result, str):
            result = ""
        return result
