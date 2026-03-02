from pynput.keyboard import Key

from whisper_writer.excel_inputs import ExcelUtils
from whisper_writer.formatting import Formatter
from whisper_writer.input_simulation import InputSimulator
from whisper_writer.navigation import Navigator
from whisper_writer.special_phrases.objects import Item
from whisper_writer.special_phrases.punctuation import PUNCTUATION, PUNCTUATION_STRING
from whisper_writer.special_phrases.special_phrase import CommandMatch, SpecialPhrase, fdbg
from whisper_writer.text_buffer import TextBuffer
from whisper_writer.utils import ConfigManager


class SpecialPhrasesManager:
    def __init__(
            self, *,
            input_simulator: InputSimulator,
            text_buffer: TextBuffer,
    ) -> None:
        self.__input_simulator = input_simulator
        self.__text_buffer = text_buffer
        self.__navigator = Navigator(input_simulator=self.__input_simulator, text_buffer=self.__text_buffer)
        self.__formatter = Formatter(input_simulator=self.__input_simulator, navigator=self.__navigator)
        self.__excel_utils = ExcelUtils(input_simulator=self.__input_simulator)

        self.preprocess_no_space = False
        self.preprocess_all_caps = False
        self.preprocess_auto_caps = True
        self.preprocess_auto_punctuation = False
        self.prepend_space = False # Used to add spaces between transcribed phrases. This should be disabled every time we detect manual input to avoid adding extra spaces
        self.start_of_sentence = True # Used to capitalise the first letter of the first word in a sentence. 

        self.cur_phrase: str = ""
        self.ESCAPE_PHRASE = "escape "

        ### Inline commands
        self.inline_commands = [
            # Edge cases
            SpecialPhrase("i", func=lambda: "I"),

            # Special characters
            SpecialPhrase("space bar", func=lambda:" ", space_before=False, space_after=False),
            SpecialPhrase("spacebar", func=lambda:" ", space_before=False, space_after=False),
            SpecialPhrase("tab key", func=lambda:"\t", space_before=False, space_after=False),
            SpecialPhrase("numeral {number}", func=lambda:"convert_number_to_numeral({number})"),
            SpecialPhrase("roman numeral {number}", func=lambda:"convert_number_to_roman_numeral({number})"),

            # Formatting
            SpecialPhrase("cap {word}", func=self.__formatter.cap), # Can be used as "cap {word}" to capitalise the first letter of the next word
            SpecialPhrase("all caps {word}", func=self.__formatter.all_cap),
        ] + PUNCTUATION


        ### Standalone commands
        self.standalone_commands = [
            SpecialPhrase("press {key}(?: ({number}) times)?", func=self.__input_simulator.simulate_keypress),
            SpecialPhrase("back space", func=lambda:self.__input_simulator.simulate_keypress(Key.backspace)),
            SpecialPhrase("backspace", func=lambda:self.__input_simulator.simulate_keypress(Key.backspace)),

            # History
            SpecialPhrase("undo that", func=lambda:self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.UNDO)),
            SpecialPhrase("redo that", func=lambda:self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.REDO)),

            # Selection
            SpecialPhrase("select {loc}? {item}", func=self.__navigator.select),
            SpecialPhrase("unselect", func=lambda: self.__input_simulator.simulate_keypress(Key.esc)), # TODO: Allow cut out words in selected section

            # Correction
            SpecialPhrase("correct that", func=lambda:"correct(current) - look at https://github.com/openai/whisper/pull/2189/files"),
            SpecialPhrase("correct {phrase}", func=lambda:"correct {phrase}"),
            SpecialPhrase("correct {word} through {word}", func=lambda:"select_between_words(word1, word2) then correct()"),
            SpecialPhrase("resume with", func=lambda:"resume"), # Overwrite from the current cursor location

            # Formatting
            SpecialPhrase("bold {item}", func=self.__formatter.bold), # Need to work out how to incorporate location
            SpecialPhrase("underline {item}", func=self.__formatter.underline), # Need to work out how to incorporate location
            SpecialPhrase("italicize {item}", func=self.__formatter.italics), # Need to work out how to incorporate location
            # SpecialPhrase("bold {loc}? {item}", func=self.__formatter.bold), # Need to work out how to incorporate location
            # SpecialPhrase("underline {loc}? {item}", func=self.__formatter.underline), # Need to work out how to incorporate location
            # SpecialPhrase("italicize {loc}? {item}", func=self.__formatter.italics), # Need to work out how to incorporate location
            SpecialPhrase("set highlight colour to {colour}", func=lambda:"highlight(current, {colour})"),
            SpecialPhrase("all caps that", func=self.__formatter.all_cap),
            SpecialPhrase("unformat that", func=lambda: self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.CLEAR_FORMATTING)),

            # Deleting words
            SpecialPhrase("scratch that", func=lambda:"delete_last_phrase"),
            SpecialPhrase("delete {loc}? {item}", func=lambda:"delete_last_phrase"),

            # Cursor control
            SpecialPhrase("go to {rel}? {loc} {item}?", func=self.__navigator.move_cursor_to), # previous/next word
            SpecialPhrase("go back", func=self.__text_buffer.move_cursor_back),
            SpecialPhrase("insert {rel}? {loc} {item}?", func=lambda:"insert {loc}"),

            # Document control
            SpecialPhrase("new document", func=lambda:"new document"),
            SpecialPhrase("open {word_tab}", func=lambda:"open {word_tab}"),
            SpecialPhrase("import document", func=lambda:"import"),
            SpecialPhrase("save document", func=lambda:"save()"),
            SpecialPhrase("save document as {phrase}", func=lambda:"save(name={phrase})"),
            SpecialPhrase("rename document", func=lambda:"rename_document"),
            SpecialPhrase("print document", func=lambda:"print"),

            # Document settings (word-specific?)
            SpecialPhrase("set document spacing to {spacing_type}", func=lambda:"change_document_spacing({spacing_type})"),
            SpecialPhrase("set font size to {font_size}", func=lambda:"set_font_size({font_size})"),
            SpecialPhrase("set font to {font_name}", func=lambda:"set_font"),

            # Widgets
            SpecialPhrase("show keyboard", func=lambda:"show_keyboard()"),
            SpecialPhrase("show my auto-texts", func=lambda:"show_auto_texts()"),
            SpecialPhrase("show my words", func=lambda:"show_custom_words"),
            SpecialPhrase("show settings", func=lambda:"show_settings()"),

            # Moving text
            SpecialPhrase("copy {loc}? {item}", func=self.__navigator.copy_item),
            SpecialPhrase("copy", func=lambda:self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.COPY)),
            SpecialPhrase("paste", func=lambda:self.__input_simulator.simulate_keypress(self.__input_simulator.CommonKeypresses.PASTE)),
            SpecialPhrase("transfer text", func=lambda:"copy all"),

            # Sharing
            SpecialPhrase("share document", func=lambda:"share({method})"),
            SpecialPhrase("email document as attachment", func=lambda:"save then email"),
            SpecialPhrase("email document", func=lambda:"copy paste into email"),
            SpecialPhrase("save to {service}", func=lambda:"save(service={service})"),
            SpecialPhrase("sync to {service}", func=lambda:"save(service={service}, sync=True)"),

            # Dictation settings
            SpecialPhrase("microphone on", func=lambda:"start_listening()"),
            SpecialPhrase("microphone off", func=lambda:"stop_listening()"),
            SpecialPhrase("log me out", func=lambda:"save and exit"),
            SpecialPhrase("switch to {language}", func=lambda lang:ConfigManager.set_config_value(lang, ("model_options", "common", "language"))),
            SpecialPhrase("no space {on_off}", func=self.__set_no_space),
            SpecialPhrase("caps lock {on_off}", func=self.__set_all_caps),
            SpecialPhrase("auto punctuation {on_off}", func=self.__set_auto_punctuation),
            SpecialPhrase("auto caps {on_off}", func=self.__set_auto_caps),

            # Vocabulary
            SpecialPhrase("add that to vocabulary", func=lambda:"add_to_vocabulary(current)"),
            SpecialPhrase("use default pronunciation", func=lambda:"use_default_pronunciation"),
            SpecialPhrase("use custom pronunciation", func=lambda:"use_custom_pronunciation"),
            SpecialPhrase("do not recognise that word", func=lambda:"remove_from_vocabulary"),

            # Photographs
            SpecialPhrase("choose photo", func=lambda:"select_photo"),
            SpecialPhrase("take photo", func=lambda:"take_photo()"),
            SpecialPhrase("take a photo", func=lambda:"take_photo()"),

            # Help
            SpecialPhrase("what can i say", func=lambda:"display_commands"),
            SpecialPhrase("give me help", func=lambda:"display_help_pages"),

            # Special phrases
            SpecialPhrase("add auto-text", func=lambda:"add_auto_text"),
            SpecialPhrase("when i say {phrase} replace with {phrase}", func=self.add_auto_text),

            # Excel
            SpecialPhrase("go to cell {cell_ref}", func=self.__excel_utils.goto_cell),
            SpecialPhrase("edit cell {cell_ref}?", func=self.__excel_utils.edit_cell),
            SpecialPhrase("select from {cell_ref} to {cell_ref}", func=self.__excel_utils.select_cells),
            SpecialPhrase("select row", func=self.__excel_utils.select_row),
            SpecialPhrase("select column", func=self.__excel_utils.select_column),
            SpecialPhrase("set format to {cell_format}", func=self.__excel_utils.set_format),
        ]

    def __process_standalone_command(self, phrase: str) -> bool:
        if not phrase:
            return True

        phrase = phrase[0].lower() + phrase[1:]
        for sp in self.standalone_commands:
            if (args_list := sp.match_whole_phrase(phrase)) is not None:
                sp.call(args_list)
                return True
        return False

    def __preprocess_phrase(self, phrase: str) -> str:

        if not phrase or phrase == " ":
            return ""

        output = phrase

        # Remove spaces
        if output[0] == " ": output = output[1:]
        if output and output[-1] == " ": output = output[:-1]

        # Remove case and punctuation
        output = output[0].lower() + output[1:]
        if not self.preprocess_auto_caps: output = output.lower()
        if self.preprocess_no_space: output.replace(" ", "")
        if not self.preprocess_auto_punctuation: output = "".join(c for c in output if c not in PUNCTUATION_STRING)
        return output

    def __postprocess_phrase(self, phrase: str) -> str:
        output = phrase
        if self.preprocess_all_caps: output = output.upper()
        if self.preprocess_no_space: output.replace(" ", "")
        return output

    def __find_all_inline_commands(self, phrase: str) -> list[CommandMatch]:
        command_match_list: list[CommandMatch] = []
        for sp in self.inline_commands:
            if (new_command_match_list := sp.match_inline_command(phrase)) is not None:
                command_match_list.extend(new_command_match_list)

        # Sort the commands in order of their order in the phrase
        command_match_list.sort(key = lambda a: a.start_index)

        # Filter out any overlapping commands - prioritise commands that started first
        index = 1
        while (index < len(command_match_list)):
            if (command_match_list[index].start_index < command_match_list[index - 1].end_index):
                command_match_list.pop(index)
            else:
                index += 1

        return command_match_list


    def __substitute_inline_commands(self, phrase: str) -> list[str | CommandMatch]:

        command_match_list = self.__find_all_inline_commands(phrase)

        # Build a list of strings and function tuples that can later be evaluated in order to build the final processed phrase
        print("\n\nCommand match list:\n", command_match_list, file=fdbg, flush=True)
        output: list[str | CommandMatch] = []
        cur_index = 0
        for command_match in command_match_list:

            # Escape the string if it is preceded by the ESCAPE_PHRASE, otherwise call the function and replace the text
            escape_start_index = max(command_match.start_index - len(self.ESCAPE_PHRASE), 0)

            if phrase[escape_start_index:command_match.start_index] == self.ESCAPE_PHRASE: # If command is escaped...

                # The command is escaped - simply add the command string to the output list, cutting out the ESCAPE_PHRASE
                if escape_start_index > cur_index:
                    output.append(phrase[cur_index:escape_start_index] + phrase[command_match.start_index:command_match.end_index])
                else:
                    output.append(phrase[command_match.start_index:command_match.end_index])

            else: # The command is not escaped

                # Add any text leading up to the command to the output list
                if command_match.start_index > cur_index:
                    output.append(phrase[cur_index:command_match.start_index - 1])

                # Add the CommandMatch to the list
                output.append(command_match)

            cur_index = command_match.end_index + 1

        if cur_index < len(phrase):
            output.append(phrase[cur_index:])

        # Finally, combine any adjacent strings in the list to make later processing easier
        index = 1
        while (index < len(output)):
            if isinstance(output[index - 1], str) and isinstance(output[index], str):
                output[index - 1] += " " + output.pop(index)
            else:
                index += 1

        print("\n\nInline command list:\n", output, file=fdbg, flush=True)
        return output

    def __format_phrase_from_command_list(self, command_list: list[str | CommandMatch]) -> str:
        print("\n\nCommand list:", command_list, file=fdbg, flush=True)
        output_phrase: str = ""

        for command in command_list:
            print("command:", command, ":", self.prepend_space)

            if isinstance(command, str):

                if self.prepend_space:
                    output_phrase += " "
                else:
                    self.prepend_space = True

                if self.start_of_sentence:
                    output_phrase += command[0].upper() + command[1:]
                else:
                    output_phrase += command
                continue

            command_str = command.func(*command.args)
            if command_str:

                if command.space_before and self.prepend_space: output_phrase += " "
                output_phrase += command_str
                self.start_of_sentence = command.end_of_sentence
                self.prepend_space = command.space_after

        return output_phrase

    def process_inline_commands(self, phrase: str) -> str:
        s = self.__substitute_inline_commands(phrase)
        s = self.__format_phrase_from_command_list(s)
        s = self.__postprocess_phrase(s)
        self.cur_phrase = s
        return s


    def process_phrase(self, phrase: str) -> str:
        s = self.__preprocess_phrase(phrase)
        if (self.__process_standalone_command(s)):
            return ""

        return self.process_inline_commands(s)


    def __set_no_space(self, enable: bool) -> None:
        self.preprocess_no_space = enable

    def __set_all_caps(self, enable: bool) -> None:
        self.preprocess_all_caps = enable

    def __set_auto_caps(self, enable: bool) -> None:
        self.preprocess_auto_caps = enable

    def __set_auto_punctuation(self, enable: bool) -> None:
        self.preprocess_auto_punctuation = enable

    def add_auto_text(self, phrase_to_replace: str, new_phrase: str) -> None:
        self.inline_commands.append(
            SpecialPhrase(phrase_to_replace, func=lambda:new_phrase)
        )
