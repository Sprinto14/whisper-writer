from dataclasses import dataclass
from typing import Callable

@dataclass
class SpecialPhrase:
    """
    
    """
    func: Callable
    deletePhrase: bool = True


SPECIAL_PHRASES_DEFAULT = {
    "new line": SpecialPhrase(func=lambda:"\n"),
    "new paragraph": SpecialPhrase(func=lambda:"\n\n"),
    "undo that": SpecialPhrase(func=lambda:"undo"),
}
