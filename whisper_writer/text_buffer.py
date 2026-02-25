from pynput import keyboard
import pyperclip

from whisper_writer.cursor_controller import Cursor
from whisper_writer.input_simulation import InputSimulator


class TextBuffer:
    text: str

    def __init__(self, input_simulator: InputSimulator) -> None:
        self.__input_simulator = input_simulator
        self.__cursor = Cursor(input_simulator)
        self.need_refresh = True

    def get_text(self) -> str:
        return self.text

    def refresh_text(self) -> None: # TODO: Detect manual keyboard/mouse presses so we know when we need to refresh the text
        """
        Copy the current text into the text buffer, and update the stored cursor location with the actual cursor location. 
        This should be run just before completing any voice command. 
        (This could be refined down further to only refresh when there has been mouse/keyboard input since the last command.) 

        This is the hackiest part of the program. 
        We need a way of copying all of the text into memory so we can make inferences, find words, etc.
        We also need to find the location of the cursor. 
        Hence, we:
         - Type an obscure character (¬) at the current cursor location
         - Select the whole text and copy it to the clipboard (with the character at the cursor location)
         - Read the text from the clipboard - this is our text buffer, but we need to remove the '¬' character
         - Undo the previous actions - this removes the '¬' character from the text, and resets the cursor back to its original location - all fixed on that end
            - This has the added benefit of fully undoing any damage done by typing '¬', e.g. if we had stuff selected
        
        We can now find the cursor position by finding the index of the '¬' character in the text buffer.
        Then remove the '¬' character to leave a text buffer (mostly) identical to that of the text.
        !!The only times the text will differ now is if there was text selected which is identical to the current clipboard text (i.e. it has just been copied)!!

        It should also be noted that in some programs, typing '¬' when text is selected counts as two actions (delete selected text, then type '¬'), 
        so these will delete any selected text whenever this is used. 
        """
        # Backup the old clipboard
        old_clipboard = pyperclip.paste()

        # Read any text that is currently selected, as this will be lost when we press '¬'
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)
        current_selection = pyperclip.paste()
        if current_selection == old_clipboard:
            current_selection = ""

        # Extract text
        self.__input_simulator.simulate_keypress(keyboard.KeyCode.from_char("¬"))
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.SELECT_ALL)
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)
        text = pyperclip.paste()
        self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.UNDO)

        try:
            self.__cursor.set_loc(text.index("¬"))
        except ValueError:
            print("Failed to update cursor location!")

        # Replace the '¬' in the buffer with the selection we deleted (or nothing if there was nothing selected)
        self.text = text.replace("¬", current_selection, 1)

        # Fix the clipboard from the backup
        pyperclip.copy(old_clipboard)

    def get_cursor_loc(self) -> int:
        return self.__cursor.get_loc()

    def move_cursor_to(self, loc: int) -> None:
        if self.need_refresh:
            self.refresh_text()
        self.__cursor.move_to(loc)

    def move_cursor_back(self) -> None:
        if self.need_refresh:
            self.refresh_text()
        self.__cursor.move_back()
