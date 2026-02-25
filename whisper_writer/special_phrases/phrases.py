import re

from pynput.keyboard import Key

from whisper_writer.excel_inputs import ExcelUtils
from whisper_writer.formatting import Formatter
from whisper_writer.input_simulation import InputSimulator
from whisper_writer.navigation import Navigator
from whisper_writer.special_phrases.objects import END_OF_SENTENCE_PUNCTUATION_STRING, PUNCTUATION
from whisper_writer.special_phrases.special_phrase import SpecialPhrase
from whisper_writer.text_buffer import TextBuffer
from whisper_writer.utils import ConfigManager


fdbg = open("debug.out", "w")

PUNCTUATION_STRING = ''.join(c for c in PUNCTUATION.values() if c not in "\'")


class SpecialPhrasesManager:
    def __init__(
            self, *,
            text_buffer: TextBuffer, 
            input_simulator: InputSimulator,
    ) -> None:
        self.__text_buffer = text_buffer
        self.__input_simulator = input_simulator
        self.__formatter = Formatter(input_simulator=self.__input_simulator)
        self.__navigator = Navigator(input_simulator=self.__input_simulator, text_buffer=self.__text_buffer)
        self.__excel_utils = ExcelUtils(input_simulator=self.__input_simulator)

        self.preprocess_no_space = False
        self.preprocess_all_caps = False
        self.preprocess_auto_caps = True
        self.preprocess_auto_punctuation = False
        self.first_phrase = True # Used to add spaces between transcribed phrases. This should be re-enabled every time we detect manual input to avoid adding extra spaces
        self.start_of_sentence = True # Used to capitalise the first letter of the first word in a sentence. 

        self.cur_phrase: str = ""

        ### Inline commands
        self.inline_commands = [
            # Edge cases
            SpecialPhrase("i", func=lambda: "I"),

            # Special characters
            SpecialPhrase("new line", func=lambda:"\n", end_of_sentence=True),
            SpecialPhrase("new paragraph", func=lambda:"\n\n", end_of_sentence=True),
            SpecialPhrase("space bar", func=lambda:" "),
            SpecialPhrase("spacebar", func=lambda:" "),
            SpecialPhrase("tab key", func=lambda:"\t"),
            SpecialPhrase("numeral {number}", func=lambda:"convert_number_to_numeral({number})"),
            SpecialPhrase("roman numeral {number}", func=lambda:"convert_number_to_roman_numeral({number})"),

            # Formatting
            SpecialPhrase("cap {word}", func=self.__formatter.cap), # Can be used as "cap {word}" to capitalise the first letter of the next word
            SpecialPhrase("all caps {word}", func=self.__formatter.all_cap),
        ] + [
            SpecialPhrase(k, (lambda s: lambda: s)(v)) for k, v in PUNCTUATION.items()
        ]


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
            SpecialPhrase("when i say {phrase}, replace with {phrase}", func=self.add_auto_text),
            SpecialPhrase("when I say {phrase}, replace with {phrase}", func=self.add_auto_text),

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
        output = phrase[0].lower() + phrase[1:]
        if not self.preprocess_auto_caps: output = phrase.lower()
        if output[-1] == " ": print("removing space "); output = output[:-1]
        if self.preprocess_no_space: output.replace(" ", "")
        if not self.preprocess_auto_punctuation: output = "".join(filter(lambda char: char not in PUNCTUATION_STRING, output))
        return output

    def __postprocess_phrase(self, phrase: str) -> str:
        output = phrase
        if self.preprocess_all_caps: output = output.upper()
        if self.preprocess_no_space: output.replace(" ", "")
        return output

    def __substitute_inline_commands(self, phrase: str) -> str:
        for sp in self.inline_commands:
            if (args_list := sp.match_inline_command(phrase)) is not None:
                for args in args_list:
                    replacement_string = sp.call(args)
                    phrase = re.sub(sp.re_pattern, replacement_string, phrase, count=1)

        return phrase

    def __format_phrase(self, phrase: str) -> str:
        # Iterate through the sentence word by word to do the final processing
        output: list[str] = []
        print(self.start_of_sentence)
        if not self.first_phrase:
            output.append(" ")

        for word in phrase.split(" "):
            print("word:", repr(word), self.start_of_sentence)
            if not word:
                continue

            if self.start_of_sentence:
                word = self.__formatter.cap(word)
                self.start_of_sentence = False

            if word[-1] in END_OF_SENTENCE_PUNCTUATION_STRING:
                self.start_of_sentence = True

            if word in PUNCTUATION_STRING:
                if output:
                    output[-1] += word
                    continue

            output.append(word)

        output_phrase = " ".join(output).replace("\n ", "\n")
        return output_phrase

    def process_inline_commands(self, phrase: str) -> str:
        s = self.__preprocess_phrase(phrase)
        s = self.__substitute_inline_commands(s)
        s = self.__format_phrase(s)
        s = self.__postprocess_phrase(s)
        self.cur_phrase = s
        return s


    def process_phrase(self, phrase: str) -> str:
        if (self.__process_standalone_command(phrase)):
            return ""

        return self.process_inline_commands(phrase)


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
